"""阶段 3（核心）：提示族 × (拒绝方向, harmfulness 方向) × (prompt 位, 响应位) 投影实验。

对每个 (提示族 f, 有害指令 x) 记录 4 个投影读数：
  r 位（refusal 方向）：dproj_prompt / dproj_resp1
  h 位（harm 方向）  ：dharm_prompt / dharm_resp1
构成 HARC (arXiv 2607.00572) 式 harm-refusal 平面：不同攻击类预计占据可分离区域。
依据 Kwon 2026 (arXiv 2607.14147)：prefill 类越狱 prompt 侧表示不变、
拒绝是响应位计算 —— prefix 族以响应位为主证据。

协议（痛点 2512.12066：单次评测 18-28% 翻转）：全程温度=0（greedy）；
records 中不保存有害指令原文（8 位哈希）；记录 chat 模板哈希。

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


def build_ids(tok, user_msg, assistant_prefix=""):
    msgs = [{"role": "user", "content": user_msg}]
    ids = tok.apply_chat_template(msgs, add_generation_prompt=True, return_tensors="pt")
    if assistant_prefix:
        pre = tok(assistant_prefix, return_tensors="pt", add_special_tokens=False).input_ids
        ids = torch.cat([ids, pre], 1)
    return ids


@torch.no_grad()
def projs(model, ids, dirs, layer, cap):
    """一次前向，返回 {方向名: 末 token 投影}。dirs: {name: [d]}"""
    cap.acts = {}
    model(ids.to(model.device))
    a = cap.acts[layer].to(model.device)
    return {name: float(a[-1] @ (d / d.norm()).to(a.device)) for name, d in dirs.items()}


@torch.no_grad()
def gen_first(model, tok, user_msg, assistant_prefix="", max_new=128):
    ids = build_ids(tok, user_msg, assistant_prefix)
    out = model.generate(ids.to(model.device), max_new_tokens=max_new, do_sample=False,
                         pad_token_id=tok.pad_token_id or tok.eos_token_id)
    text = tok.decode(out[0][ids.shape[1]:], skip_special_tokens=True)
    return text, int(out[0][ids.shape[1]]), ids


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
                resp, first_id, ids_jb = gen_first(model, tok, msg, prefix)
                pj = projs(model, ids_jb, dirs, layer, cap)
                ids_r1 = torch.cat([ids_jb.to(model.device),
                                    torch.tensor([[first_id]], device=model.device)], dim=1)
                pr = projs(model, ids_r1, dirs, layer, cap)
                label = classify(msg, resp)
                rec = {"topic": tname, "family": fam, "iid": iid, "label": label,
                       "refused": label != "COMPLY", "tpl_hash": tpl,
                       "r_base": base["r"], "r_prompt": pj["r"], "r_resp1": pr["r"],
                       "dr_prompt": pj["r"] - base["r"], "dr_resp1": pr["r"] - base["r"]}
                if "h" in dirs:
                    rec.update({"h_base": base["h"], "h_prompt": pj["h"], "h_resp1": pr["h"],
                                "dh_prompt": pj["h"] - base["h"], "dh_resp1": pr["h"] - base["h"]})
                recs.append(rec)
                print(f"[{tname}/{fam}] dr={rec['dr_resp1']:+.2f} dh={rec.get('dh_resp1', 0):+.2f} {label}")

    with open(f"{args.out}/records.jsonl", "w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"\n共 {len(recs)} 条 → {args.out}/records.jsonl (模板 {tpl})")


if __name__ == "__main__":
    main()
