# -*- coding: utf-8 -*-
import sys
import functools
print = functools.partial(print, flush=True)
"""单层消融（纠错：区分全局消融 vs 局部消融）。

run_extract 的消融是"从层 L 起全部消融"。本脚本只在**单个层**做投影消融，
比较：单层消融几乎无效 + 全局消融有效 ⇒ 拒绝是分布式的；
单层消融也有效 ⇒ 拒绝集中在该层。

用法:
  python scripts/ablate_single.py --model M --direction out/glm9b/direction.pt \
    --layers 17,19,21,23,38 --n 6 --out out/glm9b_single_ablate
"""
import argparse
import json
import os
import sys

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from refusal_geometry.data import load_topics, topic_pairs
from refusal_geometry.hooks import ActivationCapture
from refusal_geometry.judge import classify


def chat_ids(tok, msg):
    return tok.apply_chat_template([{"role": "user", "content": msg}],
                                   add_generation_prompt=True, return_dict=True,
                                   return_tensors="pt").input_ids


@torch.no_grad()
def gen(model, tok, msg, max_new=96):
    ids = chat_ids(tok, msg).to(model.device)
    pid = getattr(tok, "pad_token_id", None) or tok.eos_token_id
    out = model.generate(ids, max_new_tokens=max_new, do_sample=False, pad_token_id=pid)
    return tok.decode(out[0][ids.shape[1]:], skip_special_tokens=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--direction", required=True)
    ap.add_argument("--layers", default="17,19,21,23,38")
    ap.add_argument("--n", type=int, default=6)
    ap.add_argument("--max-new", type=int, default=96)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    tok = AutoTokenizer.from_pretrained(args.model, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        args.model, torch_dtype=torch.bfloat16, device_map="auto",
        trust_remote_code=True).eval()
    ck = torch.load(args.direction, map_location="cpu", weights_only=False)
    d = ck["direction"]
    cap = ActivationCapture(model)
    n_layers = len(cap.layers)
    layers = [int(x) for x in args.layers.split(",") if 0 <= int(x) < n_layers]

    topics = load_topics()
    harmful = [h for t in topics for h, _ in topic_pairs(topics, t)][: args.n]

    # 基线
    cap.clear()
    base = [classify(h, gen(model, tok, h, args.max_new)) for h in harmful]
    base_r = sum(l != "COMPLY" for l in base) / len(base)
    print(f"[baseline] 有害拒绝率={base_r:.0%}", flush=True)

    out = {"baseline_noncomply": base_r, "single_layer": {}, "global_from": {}}
    for L in layers:
        cap.clear(); cap.attach_ablate(d, start_layer=L, end_layer=L)
        labs = [classify(h, gen(model, tok, h, args.max_new)) for h in harmful]
        r = sum(l != "COMPLY" for l in labs) / len(labs)
        out["single_layer"][L] = r
        print(f"[single] L={L} 有害拒绝率={r:.0%}", flush=True)

    # 全局（从最优层起到末尾）作对照
    best = max(out["single_layer"], key=lambda k: -out["single_layer"][k])  # 拒绝率最低的层
    cap.clear(); cap.attach_ablate(d, start_layer=best)
    labs = [classify(h, gen(model, tok, h, args.max_new)) for h in harmful]
    out["global_from"][best] = sum(l != "COMPLY" for l in labs) / len(labs)
    print(f"[global ] from L={best} 有害拒绝率={out['global_from'][best]:.0%}", flush=True)
    cap.clear()

    json.dump(out, open(f"{args.out}/single_ablate.json", "w"), indent=2)


if __name__ == "__main__":
    main()
