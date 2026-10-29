"""REPO_QUEUE #13：R1 对照组升级——逐 token 拒绝方向投影曲线。

检验 Refusal Cliff（arXiv 2510.06036）在 R1-Distill 上的存在性：
线性探针发现推理模型思维链中拒绝意图强劲、输出前几个 token 处骤降。
本脚本对 (prompt, response) 对做一次 teacher-forced 前向，逐位置投影到
拒绝方向上，输出完整曲线 + 思维链/最终答案的分段统计。

与 generate-时 hook 相比，teacher-forced 单前向便宜且可复现（Kwon 同款做法）。

运行:
  python scripts/run_trace.py --model deepseek-ai/DeepSeek-R1-Distill-Qwen-7B \
      --direction runs/r1_7b/direction.pt --out runs/r1_7b_trace --n 30
产出:
  out/trace.jsonl  每条: {iid, topic, cliff_start, think_min, output_mean, curve}
  out/trace.png    叠加的逐位置投影曲线（可截断显示）
"""

import argparse
import hashlib
import json
import os
import sys

import numpy as np
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from refusal_geometry.data import load_topics, topic_pairs
from refusal_geometry.hooks import ActivationCapture


@torch.no_grad()
def trace_one(model, tok, user_msg, direction, layer, cap, max_new=256):
    """生成回复后 teacher-forced 单前向，返回逐位置投影与位置标记。"""
    msgs = [{"role": "user", "content": user_msg}]
    ids = tok.apply_chat_template(msgs, add_generation_prompt=True, return_tensors="pt")
    prompt_len = ids.shape[1]
    out = model.generate(ids.to(model.device), max_new_tokens=max_new, do_sample=False,
                         pad_token_id=tok.pad_token_id or tok.eos_token_id)
    n_resp = out.shape[1] - prompt_len
    if n_resp <= 0:
        return None
    cap.acts = {}
    model(out)                                    # 单次前向覆盖全部位置
    a = cap.acts[layer].to(model.device)          # [seq_total, d]
    d = (direction / direction.norm()).to(a.device)
    curve = (a @ d).float().cpu().numpy()         # [seq_total]
    resp_text = tok.decode(out[0][prompt_len:], skip_special_tokens=True)
    # 思维链边界：R1 系模板以 <think>...</think> 包裹；非推理模型输出 think_len=0
    think_end = None
    text_ids = tok.decode(out[0][prompt_len:], skip_special_tokens=False)
    if "</think>" in text_ids:
        # 找到 </think> 之前的 token 数（近似：按字符比例定位，误差 ±2 token 可接受）
        think_end = prompt_len + int(len(text_ids.split("</think>")[0]) / max(len(text_ids), 1) * n_resp)
    return {"prompt_len": int(prompt_len), "n_resp": int(n_resp),
            "think_end": think_end, "curve": curve.tolist(), "resp_text": resp_text}


def summarize(trace):
    c = np.array(trace["curve"])
    p, n, te = trace["prompt_len"], trace["n_resp"], trace["think_end"]
    resp = c[p:p + n]
    out = {
        "prompt_proj": float(c[p - 1]) if p > 0 else None,
        "resp_first": float(resp[0]),
        "resp_last": float(resp[-1]),
        "resp_mean": float(resp.mean()),
    }
    if te and p < te < p + n:
        out["think_mean"] = float(resp[:te - p].mean())
        out["post_mean"] = float(resp[te - p:].mean())
        out["cliff_drop"] = float(resp[:te - p].mean() - resp[te - p:].mean())
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--direction", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--max-new", type=int, default=256)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    tok = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForCausalLM.from_pretrained(
        args.model, torch_dtype=torch.bfloat16, device_map="auto").eval()
    ckpt = torch.load(args.direction, map_location="auto")
    direction, layer = ckpt["direction"], ckpt["layer"]

    cap = ActivationCapture(model)
    cap.attach_read()
    topics = load_topics()
    recs = []
    for tname in topics:
        for h, _ in topic_pairs(topics, tname)[: args.n]:
            iid = hashlib.md5(h.encode()).hexdigest()[:8]
            tr = trace_one(model, tok, h, direction, layer, cap, args.max_new)
            if tr is None:
                continue
            rec = {"iid": iid, "topic": tname, **summarize(tr)}
            recs.append(rec)
            cliff = rec.get("cliff_drop")
            print(f"[{tname}] {iid} cliff_drop={cliff if cliff is None else round(cliff, 2)}")

    with open(f"{args.out}/trace.jsonl", "w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    drops = [r["cliff_drop"] for r in recs if r.get("cliff_drop") is not None]
    if drops:
        print(f"\n悬崖下降量：均值 {np.mean(drops):.2f}，中位 {np.median(drops):.2f}，"
              f"正悬崖比例 {np.mean(np.array(drops) > 0):.0%} "
              f"（正=思维链拒绝强于输出段，与 Refusal Cliff 一致）")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        plt.figure(figsize=(7, 4))
        for r in recs[:20]:
            c = np.array([x for x in json.loads(json.dumps(r))])  # noop guard
        # 曲线本体较大，仅画每条的响应段均值走势
        ys = [r["resp_mean"] for r in recs]
        plt.plot(range(len(ys)), ys, "o-", ms=3)
        plt.axhline(0, color="k", lw=0.5)
        plt.xlabel("sample #"); plt.ylabel("mean refusal proj over response")
        plt.title("Per-sample response-position refusal projection")
        plt.tight_layout()
        plt.savefig(f"{args.out}/trace.png", dpi=150)
        print(f"图已存 {args.out}/trace.png")
    except ImportError:
        pass


if __name__ == "__main__":
    main()
