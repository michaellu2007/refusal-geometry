"""投影-成败关系的必要/充分性分析（对 records.jsonl）。

命题 3 原形是确定式：P(越狱) = 𝟙[z+Δz < τ]。本脚本把它拆成两个可独立检验的方向：
  - 必要性：成功越狱的样本，投影是否都已塌陷到阈值以下（有无反例）
  - 充分性：投影塌陷是否足以判定成功（AUC 是否显著 > 0.5）

用法: python scripts/analyze_necessity.py results/glm9b_prompts2/records.jsonl [--thr 30]
"""
import argparse
import json

import numpy as np


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
    ap.add_argument("path")
    ap.add_argument("--thr", type=float, default=30.0,
                    help="判定'投影已塌陷'的绝对阈值（对照原始基线中位数）")
    args = ap.parse_args()

    rows = [json.loads(l) for l in open(args.path, encoding="utf-8")]
    base = {r["iid"]: r["r_base"] for r in rows}
    comp = [r for r in rows if r["label"] == "COMPLY"]
    non = [r for r in rows if r["label"] != "COMPLY"]

    print(f"记录数 {len(rows)} | 原始指令基线投影 中位 {np.median(list(base.values())):.1f} "
          f"(区间 {min(base.values()):.1f}~{max(base.values()):.1f})")
    print(f"越狱成功 n={len(comp)}：改写后投影 {min(r['r_prompt'] for r in comp):.1f}~"
          f"{max(r['r_prompt'] for r in comp):.1f}")
    print(f"未成功   n={len(non)}：改写后投影 {min(r['r_prompt'] for r in non):.1f}~"
          f"{max(r['r_prompt'] for r in non):.1f}")

    # 必要性：成功者中投影仍高于阈值的反例
    leak = [r for r in comp if r["r_prompt"] > args.thr]
    print(f"\n[必要性] 投影>{args.thr} 仍越狱成功：{len(leak)}/{len(comp)} "
          f"→ {'反例存在，必要性不成立' if leak else '无反例，支持“投影须先塌陷”'}")

    # 充分性：AUC
    y = [1 if r["label"] == "COMPLY" else 0 for r in rows]
    print(f"[充分性] AUC(-Δproj → 成功) = {auc([-r['dr_prompt'] for r in rows], y):.3f} "
          f"| AUC(绝对投影 → 成功) = {auc([r['r_prompt'] for r in rows], y):.3f}")

    # 塌陷幅度 vs 结果（看是否饱和）
    print("\n[饱和性] 按族：平均 Δproj 与成功率")
    for fam in sorted({r["family"] for r in rows}):
        sub = [r for r in rows if r["family"] == fam]
        sr = sum(r["label"] == "COMPLY" for r in sub) / len(sub)
        print(f"  {fam:<10} Δproj均值={np.mean([r['dr_prompt'] for r in sub]):+7.2f} "
              f"成功率={sr:.0%}  族内AUC(-Δ→成功)="
              f"{auc([-r['dr_prompt'] for r in sub], [1 if r['label']=='COMPLY' else 0 for r in sub]):.3f}")


if __name__ == "__main__":
    main()
