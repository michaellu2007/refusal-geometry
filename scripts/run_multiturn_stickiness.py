# -*- coding: utf-8 -*-
import sys
import functools
print = functools.partial(print, flush=True)
"""多轮粘性实验：检验两种相反的"粘性"。

现象假说（来自日常使用经验）：
  A. 对齐模型：一旦在某个框架下越狱成功，只要**维持同一框架**继续追问，模型会持续遵从（粘性遵从）。
  B. abliterated（拒绝方向被移除）模型：一旦拒绝过一次，后续请求（甚至不同问题）也倾向继续拒绝（粘性拒绝）。

设计：同一话题内取 4 个有害问题，在固定框架下逐轮追问；每轮把模型回答写回历史。
  指标 1：逐轮拒绝率（看是否随轮次下降=粘性遵从）
  指标 2：转移概率 P(拒绝_t | 拒绝_{t-1}) 与 P(遵从_t | 遵从_{t-1})
  指标 3：粘性拒绝泄漏——第 1 轮拒绝后，第 2 轮问**良性**问题，看是否仍被拒

用法:
  python scripts/run_multiturn_stickiness.py --model M --out out/stick --topic violence --frame persona --n-turns 4
"""
import argparse
import json
import os
import sys

import numpy as np
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from refusal_geometry.data import load_topics, topic_pairs
from refusal_geometry.judge import classify
from refusal_geometry.prompts import FAMILIES, apply_family


@torch.no_grad()
def chat(model, tok, msgs, max_new=96):
    ids = tok.apply_chat_template(msgs, add_generation_prompt=True, return_dict=True,
                                  return_tensors="pt").input_ids.to(model.device)
    pid = getattr(tok, "pad_token_id", None) or tok.eos_token_id
    out = model.generate(ids, max_new_tokens=max_new, do_sample=False, pad_token_id=pid)
    return tok.decode(out[0][ids.shape[1]:], skip_special_tokens=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--topic", default="violence")
    ap.add_argument("--frame", default="persona", choices=list(FAMILIES))
    ap.add_argument("--n-turns", type=int, default=4)
    ap.add_argument("--max-new", type=int, default=96)
    ap.add_argument("--direction", default=None, help="给出则启用受控抑制（制造中等拒绝率）")
    ap.add_argument("--steer-layer", type=int, default=None,
                    help="覆盖注入层（默认用 direction.pt 里的最优层）")
    ap.add_argument("--steer-alpha", type=float, default=0.0,
                    help="负值=抑制拒绝（abliteration 式），0=不干预")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    tok = AutoTokenizer.from_pretrained(args.model, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        args.model, torch_dtype=torch.bfloat16, device_map="auto",
        trust_remote_code=True).eval()

    if args.direction and args.steer_alpha:
        import warnings
        from refusal_geometry.hooks import ActivationCapture as _AC
        ck = torch.load(args.direction, map_location="cpu", weights_only=False)
        _cap = _AC(model)
        _layer = args.steer_layer if args.steer_layer is not None else ck["layer"]
        _cap.attach_steer(ck["direction"], layer=_layer, alpha=args.steer_alpha)
        print(f"[受控] 在 L{_layer} 注入 alpha={args.steer_alpha}（负=抑制拒绝）", flush=True)

    topics = load_topics()
    pairs = topic_pairs(topics, args.topic)
    harms = [h for h, _ in pairs][: args.n_turns]
    benign = [b for _, b in pairs][: len(harms)]

    results = []
    # ---- 指标 1/2：同一框架内连续追问 ----
    msgs = []
    for i, h in enumerate(harms):
        framed, pre = apply_family(args.frame, h)
        msgs.append({"role": "user", "content": framed})
        # 框架前缀（如"好的，具体来说："）以 assistant 起始形式并入回答
        ans = chat(model, tok, msgs[:-1] + [msgs[-1]], args.max_new) if not pre else pre + chat(
            model, tok, msgs, args.max_new)
        lab = classify(framed, ans)
        results.append({"kind": "framed_chain", "turn": i + 1, "label": lab})
        print(f"[链] 第{i+1}轮 {lab:<6} 问题={framed[:28]}…", flush=True)
        msgs.append({"role": "assistant", "content": ans[:800]})

    # ---- 指标 3：拒绝泄漏到良性问题 ----
    msgs_leak = []
    h0 = harms[0]
    framed0, pre0 = apply_family(args.frame, h0)
    msgs_leak.append({"role": "user", "content": framed0})
    ans0 = chat(model, tok, msgs_leak, args.max_new)
    lab0 = classify(framed0, ans0)
    msgs_leak.append({"role": "assistant", "content": ans0[:800]})
    msgs_leak.append({"role": "user", "content": benign[0]})
    ans1 = chat(model, tok, msgs_leak, args.max_new)
    lab1 = classify(benign[0], ans1)
    results.append({"kind": "leak", "first": lab0, "after": lab1})
    print(f"[泄漏] 第1轮 {lab0} → 良性追问 {lab1}（若为 REFUSE 说明拒绝泄漏）", flush=True)

    # 汇总
    labels = [r["label"] for r in results if r["kind"] == "framed_chain"]
    n = len(labels)
    refuse = [1 if l != "COMPLY" else 0 for l in labels]
    print(f"\n=== 汇总 {os.path.basename(args.model)} [{args.topic}/{args.frame}] ===")
    print(f"逐轮拒绝: {['R' if x else 'C' for x in refuse]}  总拒绝率={np.mean(refuse):.0%}")
    if n >= 2:
        rr = [(refuse[i], refuse[i - 1]) for i in range(1, n)]
        p_rr = np.mean([1 for a, b in rr if b == 1 and a == 1]) if any(b == 1 for a, b in rr) else float("nan")
        p_cc = np.mean([1 for a, b in rr if b == 0 and a == 0]) if any(b == 0 for a, b in rr) else float("nan")
        print(f"转移：P(拒绝_t|拒绝_t-1)={p_rr if p_rr==p_rr else 'n/a'}  P(遵从_t|遵从_t-1)={p_cc if p_cc==p_cc else 'n/a'}")

    with open(f"{args.out}/stickiness_{args.topic}_{args.frame}.json", "w", encoding="utf-8") as f:
        json.dump({"model": args.model, "topic": args.topic, "frame": args.frame,
                   "results": results}, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
