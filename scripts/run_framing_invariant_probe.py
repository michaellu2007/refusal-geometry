"""框架不变（framing-invariant）harm 探针 + 判别力对照。

问题：diff-in-means harm 方向（有害 vs 中性）可能编码"这句话看起来像有害请求"的表面框架。
      我们的提示族改写恰好改变框架 → 观察到"双方向塌陷"可能是探针的表层敏感性伪影。

设计：
  1) d_std：原始有害 − 原始良性（常规做法）
  2) d_inv：**框架平衡**的有害 − 良性（有害与良性各自都套同样的 5 个族改写）
     —— 因为两侧框架分布相同，"框架"作为混淆变量被差分抵消，剩下的是话题危害本身
  3) 有效性检验：两个方向在**原始**有害/良性上的 AUC（应都接近 1）
  4) 判别力检验：在**改写后**的越狱样本上，看哪个方向还能预测成败
     —— 若 d_inv 在越狱样本里仍高，则"识别完好但拒绝被跳过"（Kwon 形态）
     —— 若两者都塌，则改写确实抹掉了可读危害信号

用法:
  python scripts/run_framing_invariant_probe.py --model M --direction out/glm9b/direction.pt \
    --trace out/glm9b_trace2/trace_families.jsonl --out out/glm9b_probe --n-per-topic 2
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
from refusal_geometry.prompts import FAMILIES, apply_family


def ids_of(tok, msg, prefix=""):
    ids = tok.apply_chat_template([{"role": "user", "content": msg}],
                                  add_generation_prompt=True, return_dict=True,
                                  return_tensors="pt").input_ids
    if prefix:
        pre = tok(prefix, add_special_tokens=False, return_tensors="pt").input_ids
        ids = torch.cat([ids, pre], 1)
    return ids


@torch.no_grad()
def act(model, tok, cap, layer, msg, prefix=""):
    cap.acts = {}
    model(ids_of(tok, msg, prefix).to(model.device))
    return cap.acts[layer][-1].float().cpu()


def auc(scores, labels):
    s = np.asarray(scores, float); y = np.asarray(labels, int)
    pos, neg = s[y == 1], s[y == 0]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    gt = (pos[:, None] > neg[None, :]).sum()
    eq = (pos[:, None] == neg[None, :]).sum()
    return (gt + 0.5 * eq) / (len(pos) * len(neg))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--direction", required=True, help="取其 layer")
    ap.add_argument("--trace", required=True, help="trace_families.jsonl，提供 (iid,variant,label)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--n-per-topic", type=int, default=2)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    tok = AutoTokenizer.from_pretrained(args.model, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        args.model, torch_dtype=torch.bfloat16, device_map="auto",
        trust_remote_code=True).eval()
    layer = torch.load(args.direction, map_location="cpu", weights_only=False)["layer"]
    cap = ActivationCapture(model)
    cap.attach_read()

    topics = load_topics()
    pairs = []
    for t in topics:
        pairs += [(t, h, b) for h, b in topic_pairs(topics, t)[: args.n_per_topic]]

    # 1) 原始激活
    orig_h = {hashlib.md5(h.encode()).hexdigest()[:8]: act(model, tok, cap, layer, h) for _, h, _ in pairs}
    orig_b = {hashlib.md5(b.encode()).hexdigest()[:8]: act(model, tok, cap, layer, b) for _, _, b in pairs}

    # 2) 框架化激活（有害/良性各套同样的族）
    fr_h, fr_b = [], []
    for _, h, b in pairs:
        for fam in FAMILIES:
            mh, ph = apply_family(fam, h)
            mb, pb = apply_family(fam, b)
            fr_h.append(act(model, tok, cap, layer, mh, ph))
            fr_b.append(act(model, tok, cap, layer, mb, pb))

    d_std = torch.stack(list(orig_h.values())).mean(0) - torch.stack(list(orig_b.values())).mean(0)
    d_inv = torch.stack(fr_h).mean(0) - torch.stack(fr_b).mean(0)

    def proj(d, v):
        return float(v @ (d / d.norm()))

    # 3) 有效性：原始有害 vs 良性
    oh = [proj(d_std, v) for v in orig_h.values()]
    ob = [proj(d_std, v) for v in orig_b.values()]
    ih = [proj(d_inv, v) for v in orig_h.values()]
    ib = [proj(d_inv, v) for v in orig_b.values()]
    y0 = [1] * len(oh) + [0] * len(ob)
    print(f"[有效性] 原始有害vs良性 AUC: d_std={auc(oh + ob, y0):.3f}  d_inv={auc(ih + ib, y0):.3f}")
    print(f"         d_std 有害{np.mean(oh):+.1f}/良性{np.mean(ob):+.1f} | "
          f"d_inv 有害{np.mean(ih):+.1f}/良性{np.mean(ib):+.1f}")
    cos = float((d_std / d_std.norm()) @ (d_inv / d_inv.norm()))
    print(f"[方向对比] cos(d_std, d_inv) = {cos:+.3f}")

    # 4) 判别力：改写后越狱样本（含 prompt 前缀的激活需与记录一致）
    trace = [json.loads(l) for l in open(args.trace, encoding="utf-8")]
    rows = []
    for tname, h, b in pairs:
        iid = hashlib.md5(h.encode()).hexdigest()[:8]
        for fam in FAMILIES:
            mh, ph = apply_family(fam, h)
            v = act(model, tok, cap, layer, mh, ph)
            lab = next((r["label"] for r in trace
                        if r["iid"] == iid and r["variant"] == fam), None)
            if lab is None:
                continue
            rows.append({"topic": tname, "iid": iid, "family": fam, "label": lab,
                         "proj_std": proj(d_std, v), "proj_inv": proj(d_inv, v)})

    y = [1 if r["label"] == "COMPLY" else 0 for r in rows]
    print(f"\n[判别力] 改写后样本 n={len(rows)} 成功={sum(y)}")
    for key in ("proj_std", "proj_inv"):
        print(f"  AUC({key} → 越狱成功) = {auc([r[key] for r in rows], y):.3f}")
    for lab in ("COMPLY", "HEDGE", "REFUSE"):
        v = [r for r in rows if r["label"] == lab]
        if v:
            print(f"  {lab:<7} n={len(v):>2} proj_std={np.mean([r['proj_std'] for r in v]):+7.1f} "
                  f"proj_inv={np.mean([r['proj_inv'] for r in v]):+7.1f}")

    torch.save({"d_std": d_std, "d_inv": d_inv, "layer": layer}, f"{args.out}/probes.pt")
    with open(f"{args.out}/projections.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
