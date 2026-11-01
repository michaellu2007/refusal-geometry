"""在指定层提取拒绝方向（用于"因果层 vs 提取最优层"对照实验）。

背景：run_extract 只保存层扫描最优层（GLM-4-9B 上是 L38/40）。
但位点扫描显示注入只在 L15–L23 有效——提取最优层 ≠ 干预有效层。
本脚本按指定层重算 diff-in-means 方向，产出与 run_extract 兼容的 direction.pt。

用法:
  python scripts/extract_at_layer.py --model M --layer 19 --out out/glm9b_L19
"""
import argparse
import hashlib
import json
import os
import sys

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from refusal_geometry.data import load_topics, topic_pairs, load_neutral
from refusal_geometry.extract import diff_in_means, permutation_baseline, system_prompt_contrast
from refusal_geometry.hooks import ActivationCapture


def chat_ids(tok, msg):
    return tok.apply_chat_template([{"role": "user", "content": msg}],
                                   add_generation_prompt=True, return_dict=True,
                                   return_tensors="pt").input_ids


@torch.no_grad()
def collect(model, tok, texts, cap, layer):
    """只收集目标层的激活（按序列末尾对齐），返回 [n, d]。"""
    out = []
    for t in texts:
        cap.acts = {}
        model(chat_ids(tok, t).to(model.device))
        out.append(cap.acts[layer][-1].cpu())
    return torch.stack(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--layer", type=int, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--n-pairs", type=int, default=30)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    tok = AutoTokenizer.from_pretrained(args.model, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        args.model, torch_dtype=torch.bfloat16, device_map="auto",
        trust_remote_code=True).eval()
    cap = ActivationCapture(model)
    cap.attach_read()

    topics = load_topics()
    harm = [h for t in topics for h, _ in topic_pairs(topics, t)][: args.n_pairs * len(topics)]
    ben = [b for t in topics for _, b in topic_pairs(topics, t)][: args.n_pairs * len(topics)]
    neu = load_neutral()

    ah = collect(model, tok, harm, cap, args.layer)
    ab = collect(model, tok, ben, cap, args.layer)
    an = collect(model, tok, neu, cap, args.layer)

    d_ref = diff_in_means(ah, ab)
    d_harm = diff_in_means(ah, an)
    mu, sd = permutation_baseline(ah, ab, n_perm=20)
    d_n = d_ref / d_ref.norm()
    score = float((ah @ d_n).mean() - (ab @ d_n).mean()) / float(torch.cat([ah @ d_n, ab @ d_n]).std())
    z = (score - mu) / (sd + 1e-8)
    d_cls = system_prompt_contrast(model, tok, cap, args.layer)
    cos_cls = float((d_ref / d_ref.norm()) @ (d_cls / d_cls.norm()))

    print(f"[L{args.layer}] d={score:.3f} perm {mu:.3f}±{sd:.3f} z={z:.1f} | cls_cos={cos_cls:+.3f}", flush=True)
    torch.save({"direction": d_ref, "harm_direction": d_harm, "cls_direction": d_cls,
                "layer": args.layer, "pos": "last",
                "scores": {f"{args.layer}_last": score},
                "perm": {"mean": mu, "std": sd, "z": z},
                "topics": list(topics),
                "tpl_hash": hashlib.md5((tok.chat_template or "").encode()).hexdigest()[:8]},
               f"{args.out}/direction.pt")


if __name__ == "__main__":
    main()
