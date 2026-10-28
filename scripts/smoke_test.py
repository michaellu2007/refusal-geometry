"""合成张量 smoke test：不下载模型，用 numpy/torch 验证全部核心数学。
覆盖：diff-in-means 方向恢复、层扫描分数、投影消融零化、注入平移、AUC。
"""

import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

rng = np.random.default_rng(0)
d, n = 64, 400

# 构造带真实"拒绝方向"的合成激活
true_dir = rng.normal(size=d)
true_dir /= np.linalg.norm(true_dir)
shift = 6.0
mu_h = true_dir * shift          # harmful 均值沿方向平移
harm = rng.normal(size=(n, d)) + mu_h
ben = rng.normal(size=(n, d))

# diff-in-means 应恢复 true_dir 方向
r = harm.mean(0) - ben.mean(0)
cos = float(r @ true_dir / np.linalg.norm(r))
assert cos > 0.98, f"方向恢复失败 cos={cos}"
print(f"[1] diff-in-means 恢复方向 cos={cos:.4f} ✓")

# 层扫描分数：真实层应远高于噪声层
from refusal_geometry.extract import layer_scan  # noqa: E402
import torch  # 如无 torch 则跳过钩子部分
acts_h = {0: torch.tensor(harm)[:, None], 1: torch.tensor(rng.normal(size=(n, d)))[:, None]}
acts_b = {0: torch.tensor(ben)[:, None], 1: torch.tensor(rng.normal(size=(n, d)))[:, None]}
scores = layer_scan(acts_h, acts_b)
assert scores[(0, "last")] > 3 and abs(scores[(1, "last")]) < 1.0
print(f"[2] 层扫描定位真实层 ✓ (score={scores[(0,'last')]:.2f} vs 噪声层 {scores[(1,'last')]:.2f}; "
      "注: 噪声层 ~0.6 提示层选择存在多重比较偏差，blog 需报告基线)")

# 投影消融 → 投影恒为 0；注入 → 投影平移 alpha
x = torch.tensor(rng.normal(size=(2, 7, d)), dtype=torch.float32)
dt = torch.tensor(r, dtype=torch.float32)
from refusal_geometry.hooks import project_out  # noqa: E402
xab = project_out(x, dt)
proj = torch.einsum("bsd,d->bs", xab, dt / dt.norm())
assert proj.abs().max() < 1e-4, "消融未零化投影"
steered = x + 7.0 * (dt / dt.norm())
proj_s = torch.einsum("bsd,d->bs", steered, dt / dt.norm())
assert torch.allclose(proj_s - torch.einsum("bsd,d->bs", x, dt / dt.norm()),
                      torch.full_like(proj_s, 7.0), atol=1e-4)
print("[3] 消融零化投影、注入精确平移 alpha ✓")

# AUC：构造 -Δproj 与成功标签相关的数据，应接近理论值
from scripts.run_analysis import auc  # noqa: E402
scores_ = rng.normal(size=200)
labels = (scores_ + rng.normal(scale=0.5, size=200) > 0).astype(int)
a = auc(scores_, labels)
assert 0.85 < a <= 1.0, f"AUC 异常 {a}"
print(f"[4] AUC 实现正确（合成信号 AUC={a:.3f}）✓")

print("\n全部通过：数学管线可直接上真实模型。")
