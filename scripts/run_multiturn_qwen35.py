# -*- coding: utf-8 -*-
import sys
import functools
print = functools.partial(print, flush=True)
"""针对 Qwen3.5 架构（Huihui-Qwen3.8-27B-abliterated）的多轮粘性测试。

该模型要点：
  - model_type = qwen3_5，是图文模型（Qwen3_5ForConditionalGeneration），需 transformers >= 5
  - 27B 参数，bf16 约 54GB，24GB 卡必须 4 比特量化（约 15GB）
  - 文本任务直接走 chat template，无需图片

用法:
  python scripts/run_multiturn_qwen35.py --model DIR --out out/stick27b --topic violence --frame persona
"""
import argparse
import json
import os
import sys

import torch
import torch.nn.functional as F

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from refusal_geometry.data import load_topics, topic_pairs
from refusal_geometry.judge import classify
from refusal_geometry.prompts import FAMILIES, apply_family


def load_model(path, four_bit=True):
    from transformers import AutoProcessor
    try:                                  # 新版 transformers 的图文模型类
        from transformers import AutoModelForImageTextToText as M
    except ImportError:                   # 退化：直接用因果 LM
        from transformers import AutoModelForCausalLM as M
    proc = AutoProcessor.from_pretrained(path, trust_remote_code=True)
    kw = dict(device_map={"": 0}, trust_remote_code=True)
    if four_bit:
        from transformers import BitsAndBytesConfig
        kw["quantization_config"] = BitsAndBytesConfig(
            load_in_4bit=True, bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_quant_type="nf4", bnb_4bit_use_double_quant=True)
    else:
        kw["dtype"] = torch.bfloat16
    model = M.from_pretrained(path, **kw).eval()
    return proc, model


@torch.no_grad()
def chat(proc, model, msgs, max_new=96):
    """文本对话生成。兼容 processor 与 tokenizer 两种返回。"""
    enc = proc.apply_chat_template(msgs, add_generation_prompt=True,
                                   return_dict=True, return_tensors="pt")
    ids = enc["input_ids"].to(model.device)
    attn = enc.get("attention_mask")
    attn = attn.to(model.device) if attn is not None else torch.ones_like(ids)
    out = model.generate(ids, attention_mask=attn, max_new_tokens=max_new,
                         do_sample=False,
                         pad_token_id=getattr(proc.tokenizer if hasattr(proc, "tokenizer")
                                              else proc, "pad_token_id", None) or 0)
    new = out[0][ids.shape[1]:]
    tok = proc.tokenizer if hasattr(proc, "tokenizer") else proc
    return tok.decode(new, skip_special_tokens=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--topic", default="violence")
    ap.add_argument("--frame", default="persona", choices=list(FAMILIES))
    ap.add_argument("--n-turns", type=int, default=4)
    ap.add_argument("--max-new", type=int, default=96)
    ap.add_argument("--no-4bit", action="store_true")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    proc, model = load_model(args.model, four_bit=not args.no_4bit)
    print(f"[load] 4bit={not args.no_4bit} device={model.device}", flush=True)

    topics = load_topics()
    pairs = topic_pairs(topics, args.topic)
    harms = [h for h, _ in pairs][: args.n_turns]
    benign = [b for _, b in pairs][:1]

    results, msgs = [], []
    for i, h in enumerate(harms):
        framed, _pre = apply_family(args.frame, h)
        msgs.append({"role": "user", "content": framed})
        ans = chat(proc, model, msgs, args.max_new)
        lab = classify(framed, ans)
        results.append({"turn": i + 1, "label": lab})
        print(f"[链] 第{i+1}轮 {lab:<6} {framed[:26]}…", flush=True)
        msgs.append({"role": "assistant", "content": ans[:800]})

    # 泄漏探针
    framed0, _ = apply_family(args.frame, harms[0])
    m2 = [{"role": "user", "content": framed0}]
    a0 = chat(proc, model, m2, args.max_new)
    l0 = classify(framed0, a0)
    m2 += [{"role": "assistant", "content": a0[:800]}, {"role": "user", "content": benign[0]}]
    a1 = chat(proc, model, m2, args.max_new)
    l1 = classify(benign[0], a1)
    print(f"[泄漏] 首轮 {l0} → 良性追问 {l1}", flush=True)

    refuse = [1 if r["label"] != "COMPLY" else 0 for r in results]
    print(f"\n=== {os.path.basename(os.path.dirname(args.model))} [{args.topic}/{args.frame}] ===")
    print(f"逐轮: {['R' if x else 'C' for x in refuse]}  拒绝率={sum(refuse)/len(refuse):.0%}")
    with open(f"{args.out}/stick27b_{args.topic}_{args.frame}.json", "w", encoding="utf-8") as f:
        json.dump({"model": args.model, "topic": args.topic, "frame": args.frame,
                   "results": results, "leak": [l0, l1]}, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
