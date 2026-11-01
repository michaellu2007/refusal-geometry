"""基线审计：全量 58 对话题指令，统计各话题拒绝率（实验前提 + 独立结果）。

RUNBOOK 第 5 步要求基线拒绝率 ≥ 90%，否则先修数据集。本脚本给出精确数字与逐条响应。
输出 out/baseline_audit.jsonl（含指令哈希与响应，响应供人工复核；不落指令原文到日志外）

用法:
  python scripts/run_baseline_audit.py --model M --out out/glm9b_baseline
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
from refusal_geometry.judge import classify


def chat_ids(tok, msg):
    return tok.apply_chat_template([{"role": "user", "content": msg}],
                                   add_generation_prompt=True, return_dict=True,
                                   return_tensors="pt").input_ids


@torch.no_grad()
def gen(model, tok, msg, max_new=96):
    ids = chat_ids(tok, msg).to(model.device)
    out = model.generate(ids, max_new_tokens=max_new, do_sample=False,
                         pad_token_id=getattr(tok, "pad_token_id", None) or tok.eos_token_id)
    return tok.decode(out[0][ids.shape[1]:], skip_special_tokens=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-new", type=int, default=96)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    tok = AutoTokenizer.from_pretrained(args.model, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        args.model, torch_dtype=torch.bfloat16, device_map="auto",
        trust_remote_code=True).eval()

    topics = load_topics()
    rows = []
    for tname, t in topics.items():
        for kind, texts in (("harmful", t["harmful"]), ("benign", t["benign"])):
            for txt in texts:
                resp = gen(model, tok, txt, args.max_new)
                lab = classify(txt, resp)
                rows.append({"topic": tname, "kind": kind,
                             "iid": hashlib.md5(txt.encode()).hexdigest()[:8],
                             "label": lab, "resp_head": resp[:160]})
        sub_h = [r for r in rows if r["topic"] == tname and r["kind"] == "harmful"]
        sub_b = [r for r in rows if r["topic"] == tname and r["kind"] == "benign"]
        rh = sum(r["label"] != "COMPLY" for r in sub_h) / len(sub_h)
        rb = sum(r["label"] != "COMPLY" for r in sub_b) / len(sub_b)
        print(f"[{tname:<14}] harmful 拒绝率={rh:.0%} (n={len(sub_h)}) | benign 拒绝率={rb:.0%}", flush=True)

    h_all = [r for r in rows if r["kind"] == "harmful"]
    b_all = [r for r in rows if r["kind"] == "benign"]
    summary = {
        "harmful_refusal": sum(r["label"] != "COMPLY" for r in h_all) / len(h_all),
        "benign_refusal": sum(r["label"] != "COMPLY" for r in b_all) / len(b_all),
        "n_harmful": len(h_all), "n_benign": len(b_all),
        "label_dist_harmful": {k: sum(r["label"] == k for r in h_all) for k in ("REFUSE", "HEDGE", "COMPLY")},
    }
    print(f"\n[总计] harmful 拒绝率={summary['harmful_refusal']:.0%} "
          f"benign 拒绝率={summary['benign_refusal']:.0%} "
          f"分布={summary['label_dist_harmful']}", flush=True)

    with open(f"{args.out}/baseline_audit.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    json.dump(summary, open(f"{args.out}/summary.json", "w"), indent=2)


if __name__ == "__main__":
    main()
