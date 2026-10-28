"""研究问题 2：跨话题拒绝方向余弦矩阵（单方向 vs 拒绝锥 vs 多方向）。

同一层/位置上分话题提取方向，两两余弦：
  C_ij ≈ 1           → 共享单方向（Arditi 式）
  C_ij 块状高但不满 1 → 拒绝锥（Wollschläger 式）
  C_ij 存在低块       → 中文话题多方向（新发现）

运行:
  python scripts/run_cosine_matrix.py --model ... --direction runs/glm9b/direction.pt --out runs/glm9b
"""

import argparse
import json
import os
import sys

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))
from run_extract import collect_acts, tpl_hash
from refusal_geometry.data import load_topics, topic_pairs
from refusal_geometry.extract import diff_in_means, pairwise_cosine
from refusal_geometry.hooks import ActivationCapture


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--direction", required=True, help="用其 layer/pos 保证可比")
    ap.add_argument("--out", required=True)
    ap.add_argument("--n-pairs", type=int, default=30)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    tok = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForCausalLM.from_pretrained(
        args.model, torch_dtype=torch.bfloat16, device_map="auto").eval()
    ckpt = torch.load(args.direction, map_location="auto")
    layer, pi = ckpt["layer"], (-1 if ckpt["pos"] == "last" else -2)

    cap = ActivationCapture(model)
    cap.attach_read()
    topics = load_topics()
    dirs = {}
    for tname in topics:
        pairs = topic_pairs(topics, tname)[: args.n_pairs]
        ah = collect_acts(model, tok, [h for h, _ in pairs], cap)
        ab = collect_acts(model, tok, [b for _, b in pairs], cap)
        dirs[tname] = diff_in_means(ah[layer][:, pi], ab[layer][:, pi])
        print(f"[{tname}] 方向已提取 @layer{layer}")

    C, keys = pairwise_cosine(dirs)
    print("\n余弦矩阵：\n", C.round(3))
    json.dump({"keys": keys, "cosine": C.tolist(), "layer": layer,
               "tpl_hash": tpl_hash(tok)},
              open(f"{args.out}/cosine_matrix.json", "w", ensure_ascii=False), indent=2)

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        plt.figure(figsize=(4.5, 4))
        plt.imshow(C, vmin=0, vmax=1, cmap="viridis")
        plt.xticks(range(len(keys)), keys, rotation=45, ha="right")
        plt.yticks(range(len(keys)), keys)
        for i in range(len(keys)):
            for j in range(len(keys)):
                plt.text(j, i, f"{C[i, j]:.2f}", ha="center", va="center",
                         color="w" if C[i, j] < 0.6 else "k", fontsize=8)
        plt.colorbar(label="cos(r_i, r_j)")
        plt.title("Cross-topic refusal directions")
        plt.tight_layout()
        plt.savefig(f"{args.out}/cosine_matrix.png", dpi=150)
        print(f"图已存 {args.out}/cosine_matrix.png")
    except ImportError:
        pass


if __name__ == "__main__":
    main()
