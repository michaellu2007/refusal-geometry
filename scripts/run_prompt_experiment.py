"""阶段 3（核心）：提示族 × (拒绝方向, harmfulness 方向) × (prompt 位, 响应位) 投影实验。

对每个 (提示族 f, 有害指令 x) 记录投影读数（HARC arXiv 2607.00572 平面）：
  refusal 方向 r：dr_prompt / dr_resp1 / dr_resp8
  harm 方向 h    ：dh_prompt / dh_resp1 / dh_resp8（若有）
读出位配方（Kwon arXiv 2607.14147 + HARC）：prompt 位=末 token；响应位=末 1 个
与末 8 个响应 token 均值池化（HARC 用 32，先 8，32 对比进 RESEARCH_QUEUE）。
假设 H（formalism.md 命题 3）：越狱成功 ⟺ 投影下降（几何失效）；投影不变而行为
翻转 = 表达抑制。提示族平面先验：persona→DAN 象限、encoding→CodeAttack、
academic→PAIR（见 lit_review 1.7）。

协议（arXiv 2512.12066 痛点）：温度=0；指令原文只存 8 位哈希；记录模板哈希。

运行:
  python scripts/run_prompt_experiment.py --model ... --direction runs/r1/direction.pt --out runs/r1_prompts
"""

import argparse
import hashlib
import json
import os
import sys

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from refusal_geometry.data import load_topics, topic_pairs
from refusal_geometry.hooks import ActivationCapture
from refusal_geometry.judge import classify
from refusal_geometry.prompts import FAMILIES, apply_family

RESP_POOL = 8  # HARC 用前 32 token 均值池化；先 8（成本/信息折中）


def build_ids(tok, user_msg, assistant_prefix=""):
    msgs = [{"role": "user", "content": user_msg}]
    ids = tok.apply_chat_template(msgs, add_generation_prompt=True, return_tensors="pt")
    if assistant_prefix:
        pre = tok(assistant_prefix, return_tensors="pt", add_special_tokens=False).input_ids
        ids = torch.cat([ids, pre], 1)
    return ids


@torch.no_grad()
def projs(model, ids, dirs, layer, cap, k=1):
    """一次前向，返回 {方向名: 末 k 个位置均值池化后的投影}。dirs: {name: [d]}"""
    cap.acts = {}
    model(ids.to(model.device))
    a = cap.acts[layer].to(model.device)
    pool = a[-k:].mean(0)
    return {name: float(pool @ (d / d.norm()).to(a.device)) for name, d in dirs.items()}


@torch.no_grad()
def gen_first(model, tok, user_msg, assistant_prefix="", max_new=128):
    """生成回复，返回 (文本, 前 RESP_POOL 个响应 token ids [1,k], prompt ids)。"""
    ids = build_ids(tok, user_msg, assistant_prefix)
    out = model.generate(ids.to(model.device), max_new_tokens=max_new, do_sample=False,
                         pad_token_id=tok.pad_token_id or tok.eos_token_id)
    text = tok.decode(out[0][ids.shape[1]:], skip_special_tokens=True)
    n_resp = max(out.shape[1] - ids.shape[1], 1)
    first8 = out[0][ids.shape[1]:ids.shape[1] + min(RESP_POOL, n_resp)].view(1, -1)
    return text, first8, ids


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--direction", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--n-pairs", type=int, default=30)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    tok = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForCausalLM.from_pretrained(
        args.model, torch_dtype=torch.bfloat16, device_map="auto").eval()
    ckpt = torch.load(args.direction, map_location="auto")
    layer = ckpt["layer"]
    dirs = {"r": ckpt["direction"]}
    if "harm_direction" in ckpt:      # 兼容旧 checkpoint
        dirs["h"] = ckpt["harm_direction"]
    tpl = hashlib.md5((tok.chat_template or "").encode()).hexdigest()[:8] \
        if tok.chat_template else "none"

    cap = ActivationCapture(model)
    cap.attach_read()
    topics = load_topics()
    recs = []
    for tname in topics:
        for h, _ in topic_pairs(topics, tname)[: args.n_pairs]:
            iid = hashlib.md5(h.encode()).hexdigest()[:8]
            base = projs(model, build_ids(tok, h), dirs, layer, cap)
            for fam in FAMILIES:
                msg, prefix = apply_family(fam, h)
                resp, first8, ids_jb = gen_first(model, tok, msg, prefix)
                dev = model.device
                pj = projs(model, ids_jb, dirs, layer, cap)               # prompt 末 token
                pr1 = projs(model, torch.cat([ids_jb.to(dev), first8[:, :1].to(dev)], dim=1),
                            dirs, layer, cap)                              # 响应第 1 token 位
                pr8 = projs(model, torch.cat([ids_jb.to(dev), first8.to(dev)], dim=1),
                            dirs, layer, cap, k=first8.shape[1])           # 前 8 token 池化
                label = classify(msg, resp)
                rec = {"topic": tname, "family": fam, "iid": iid, "label": label,
                       "refused": label != "COMPLY", "tpl_hash": tpl,
                       "r_base": base["r"], "r_prompt": pj["r"],
                       "r_resp1": pr1["r"], "r_resp8": pr8["r"],
                       "dr_prompt": pj["r"] - base["r"],
                       "dr_resp1": pr1["r"] - base["r"], "dr_resp8": pr8["r"] - base["r"]}
                if "h" in dirs:
                    rec.update({"h_base": base["h"], "h_prompt": pj["h"],
                                "h_resp1": pr1["h"], "h_resp8": pr8["h"],
                                "dh_prompt": pj["h"] - base["h"],
                                "dh_resp1": pr1["h"] - base["h"],
                                "dh_resp8": pr8["h"] - base["h"]})
                recs.append(rec)
                print(f"[{tname}/{fam}] dr8={rec['dr_resp8']:+.2f} "
                      f"dh8={rec.get('dh_resp8', 0):+.2f} {label}")

    with open(f"{args.out}/records.jsonl", "w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"\n共 {len(recs)} 条 → {args.out}/records.jsonl (模板 {tpl})")


if __name__ == "__main__":
    main()
