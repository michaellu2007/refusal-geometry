# -*- coding: utf-8 -*-
import sys
import functools
print = functools.partial(print, flush=True)
"""通过 Ollama API 跑多轮粘性实验（对应日常使用形态）。

为什么用 Ollama：
  - 该模型是 GGUF/新架构（qwen3_5），transformers 支持不完整；Ollama 已适配
  - 走 HTTP 接口 = 和用户日常使用一致，行为结论最贴近真实体验
  - 代价：无法读层内激活（纯行为实验）

实验内容：
  1) 基线：直接问有害问题（无框架），看这个 abliterated 模型到底拒不拒
  2) 多轮链：固定框架下连续 4 个同类有害问题，逐轮记结果（测"粘性遵从"）
  3) 粘性拒绝探针：先问一个它确实会拒的问题，再问同类第二个，看拒绝是否延续
  4) 泄漏探针：拒绝后问良性问题，看拒绝是否蔓延

用法: python scripts/ollama_stick.py --out /root/Share/zcode-rg/out/stick27b --model huihui_ai/qwen3.8-abliterated:27b
"""
import argparse
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from refusal_geometry.data import load_topics, topic_pairs
from refusal_geometry.judge import classify
from refusal_geometry.prompts import FAMILIES, apply_family

API = "http://127.0.0.1:11434/api/chat"


def chat(model, messages, max_new=768, temperature=0.0):
    body = json.dumps({
        "model": model, "messages": messages, "stream": False,
        "options": {"temperature": temperature, "num_predict": max_new, "seed": 42},
    }).encode()
    req = urllib.request.Request(API, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        msg = json.load(r)["message"]
    # 思考型模型：正文可能为空而内容在 thinking 里；优先取 content
    return msg.get("content") or msg.get("thinking") or ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="huihui_ai/qwen3.8-abliterated:27b")
    ap.add_argument("--out", required=True)
    ap.add_argument("--n-turns", type=int, default=4)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    topics = load_topics()
    report = {"model": args.model, "baseline": {}, "chains": {}, "sticky_refusal": {}, "leak": {}}

    # ---------- 1) 基线：无框架直问 ----------
    print("=== 基线（无框架直问）===", flush=True)
    for tname in topics:
        pairs = topic_pairs(topics, tname)[:2]
        labs = []
        for h, _ in pairs:
            ans = chat(args.model, [{"role": "user", "content": h}])
            lab = classify(h, ans)
            labs.append(lab)
            print(f"  [{tname}] {lab:<6} {ans[:50]!r}", flush=True)
        report["baseline"][tname] = labs

    # ---------- 2) 多轮链（固定框架） ----------
    print("\n=== 多轮链（固定框架连续追问）===", flush=True)
    refused_topics = [t for t, labs in report["baseline"].items()
                      if any(l != "COMPLY" for l in labs)] or list(report["baseline"])[:2]
    print(f"  （含拒绝的话题：{refused_topics}，在其上测链）", flush=True)
    for tname in refused_topics:
        for frame in ("persona", "academic"):
            harms = [h for h, _ in topic_pairs(topics, tname)][: args.n_turns]
            msgs, labels = [], []
            for h in harms:
                framed, _ = apply_family(frame, h)
                msgs.append({"role": "user", "content": framed})
                ans = chat(args.model, msgs)
                labels.append(classify(framed, ans))
                msgs.append({"role": "assistant", "content": ans[:1200]})
            report["chains"][f"{tname}/{frame}"] = labels
            print(f"  [{tname}/{frame}] {['R' if l!='COMPLY' else 'C' for l in labels]}", flush=True)

    # ---------- 3) 粘性拒绝：先拒一次，再问同类 ----------
    print("\n=== 粘性拒绝探针 ===", flush=True)
    for tname in topics:
        pairs = topic_pairs(topics, tname)
        # 找一条它能拒的（无框架直问，最多试 4 条）
        target = None
        for h, _ in pairs[:6]:
            if classify(h, chat(args.model, [{"role": "user", "content": h}])) != "COMPLY":
                target = h
                break
        if target is None:
            report["sticky_refusal"][tname] = {"found": False}
            print(f"  [{tname}] 前 6 条无一被拒 → 无法测粘性", flush=True)
            continue
        # 第 1 轮：该问题（可能被拒）；第 2 轮：同话题另一个问题（无框架）
        other = next(h for h, _ in pairs if h != target)
        m = [{"role": "user", "content": target}]
        a1 = chat(args.model, m)
        l1 = classify(target, a1)
        m += [{"role": "assistant", "content": a1[:1200]}, {"role": "user", "content": other}]
        a2 = chat(args.model, m)
        l2 = classify(other, a2)
        report["sticky_refusal"][tname] = {"first": l1, "second": l2}
        print(f"  [{tname}] 首问={l1} → 同类追问={l2}", flush=True)
        # 4) 泄漏：拒绝后问良性
        ben = topic_pairs(topics, tname)[0][1]
        m3 = [{"role": "user", "content": target},
              {"role": "assistant", "content": a1[:1200]},
              {"role": "user", "content": ben}]
        l3 = classify(ben, chat(args.model, m3))
        report["leak"][tname] = l3
        print(f"  [{tname}] 拒绝后良性追问={l3}", flush=True)

    with open(f"{args.out}/ollama_stick.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n结果已存 {args.out}/ollama_stick.json", flush=True)


if __name__ == "__main__":
    main()
