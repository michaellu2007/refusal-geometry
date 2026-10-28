"""分析：投影-成败 ROC/AUC（双读出位×双方向）、各族统计、HARC 平面图。

运行: python scripts/run_analysis.py --run runs/r1_prompts
"""

import argparse
import json

import numpy as np

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError:
    plt = None


def auc(scores, labels):
    """Mann-Whitney U 版 AUC。labels: 1=越狱成功(COMPLY)。"""
    scores, labels = np.asarray(scores, float), np.asarray(labels, int)
    pos, neg = scores[labels == 1], scores[labels == 0]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    gt = (pos[:, None] > neg[None, :]).sum()
    eq = (pos[:, None] == neg[None, :]).sum()
    return (gt + 0.5 * eq) / (len(pos) * len(neg))


def roc_curve(scores, labels):
    s = np.asarray(scores, float); y = np.asarray(labels, int)
    order = np.argsort(-s)
    y = y[order]
    tpr = np.cumsum(y) / max(y.sum(), 1)
    fpr = np.cumsum(1 - y) / max((1 - y).sum(), 1)
    return np.concatenate([[0], fpr]), np.concatenate([[0], tpr])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    args = ap.parse_args()

    recs = [json.loads(l) for l in open(f"{args.run}/records.jsonl", encoding="utf-8")]
    print(f"共 {len(recs)} 条")
    has_h = "dh_resp1" in recs[0]
    # 越狱成功 = COMPLY；负的 Δproj 预测成功（几何失效假设）
    y = [1 - int(r["refused"]) for r in recs]

    print(f"\n{'family':<12}{'COMPLY':>8}{'HEDGE':>7}{'REFUSE':>8}"
          f"{'dr_resp1|s':>12}{'dr_resp1|f':>12}")
    for fam in sorted({r["family"] for r in recs}):
        sub = [r for r in recs if r["family"] == fam]
        mp = lambda xs, k: np.mean([x[k] for x in xs]) if xs else float("nan")
        succ = [r for r in sub if r["label"] == "COMPLY"]
        fail = [r for r in sub if r["label"] != "COMPLY"]
        print(f"{fam:<12}{sum(r['label']=='COMPLY' for r in sub):>8}"
              f"{sum(r['label']=='HEDGE' for r in sub):>7}"
              f"{sum(r['label']=='REFUSE' for r in sub):>8}"
              f"{mp(succ,'dr_resp1'):>12.2f}{mp(fail,'dr_resp1'):>12.2f}")

    print("\n[核心] AUC( -Δproj → 越狱成功 )：")
    results = {}
    for key in ["dr_resp1", "dr_prompt"] + (["dh_resp1", "dh_prompt"] if has_h else []):
        a = auc([-r[key] for r in recs], y)
        results[key] = a
        tag = "响应位" if "resp1" in key else "prompt位"
        dim = "harm" if key.startswith("dh") else "refusal"
        print(f"  {dim}/{tag}: {a:.3f}")

    for t in sorted({r["topic"] for r in recs}):
        sub = [r for r in recs if r["topic"] == t]
        at = auc([-r["dr_resp1"] for r in sub], [1 - int(r["refused"]) for r in sub])
        print(f"  topic={t:<12} AUC={at:.3f}  n={len(sub)}")

    if plt is not None:
        # 图 1：响应位 refusal 方向 ROC
        fpr, tpr = roc_curve([-r["dr_resp1"] for r in recs], y)
        plt.figure(figsize=(9, 4))
        plt.subplot(1, 2, 1)
        plt.plot(fpr, tpr, label=f"resp1 AUC={results['dr_resp1']:.3f}")
        if "dr_prompt" in results:
            fp2, tp2 = roc_curve([-r["dr_prompt"] for r in recs], y)
            plt.plot(fp2, tp2, label=f"prompt AUC={results['dr_prompt']:.3f}")
        plt.plot([0, 1], [0, 1], "k--", lw=0.8)
        plt.xlabel("FPR"); plt.ylabel("TPR"); plt.legend(); plt.title("Projection drop → jailbreak")
        # 图 2：HARC 平面（harm vs refusal，响应位）
        if has_h:
            plt.subplot(1, 2, 2)
            for lab, c in (("COMPLY", "tab:red"), ("HEDGE", "tab:orange"), ("REFUSE", "tab:blue")):
                xs = [r["dr_resp1"] for r in recs if r["label"] == lab]
                ys = [r["dh_resp1"] for r in recs if r["label"] == lab]
                plt.scatter(xs, ys, s=14, alpha=0.6, label=lab, c=c)
            plt.axhline(0, color="k", lw=0.5); plt.axvline(0, color="k", lw=0.5)
            plt.xlabel("Δproj refusal (resp1)"); plt.ylabel("Δproj harm (resp1)")
            plt.legend(); plt.title("HARC plane: attack families")
        plt.tight_layout()
        plt.savefig(f"{args.run}/analysis.png", dpi=150, bbox_inches="tight")
        print(f"\n图已存 {args.run}/analysis.png")


if __name__ == "__main__":
    main()
