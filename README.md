# 中文大模型拒绝方向的几何结构 Refusal Geometry

中文安全话题的拒绝行为是否由单一线性方向中介？成功的越狱提示是否系统性地压低激活在拒绝方向上的投影？

主模型：`zai-org/GLM-4-9B-Chat`；对照：`deepseek-ai/DeepSeek-R1-Distill-Qwen-7B` / `-Qwen-1.5B`（调试档）。

方法论参照（完整 47 篇注释文献库见 [notes/lit_review.md](notes/lit_review.md)）：
- Arditi et al. 2024, *Refusal in LLMs Is Mediated by a Single Direction* (NeurIPS, arXiv 2406.11717)
- Wollschläger et al., *The Geometry of Refusal: Concept Cones* (arXiv 2502.17420)
- HARC, *Coupling Harmfulness and Refusal Directions* (arXiv 2607.00572)
- Kwon, *Breaking Refusal in the First Half* (arXiv 2607.14147)

## 研究问题

1. 中文话题拒绝是否单方向中介？（成对差分均值 + 全层扫描 + 置换检验基线）
2. 分话题方向呈单方向 / 拒绝锥 / 多方向块？（`run_cosine_matrix.py`）
3. **核心**：提示词改写 = 激活平移？Δproj 在 harm-refusal 平面（HARC）× 双读出位（Kwon）上预测越狱成败，AUC 判别"几何失效 vs 表达抑制"。

## 目录

```
refusal_geometry/        # 核心 Python 包
  hooks.py               # residual stream hook（读激活 / 消融 / 注入）
  extract.py             # 差异均值法 + 全层×位置扫描 + 置换检验基线
  judge.py               # 三分类判定（REFUSE/HEDGE/COMPLY，关键词 + LLM judge）
  prompts.py             # 5 类越狱提示族模板
  data.py                # AdvBench 官方 CSV + 中文话题对 + 中性指令集
scripts/
  run_extract.py         # 双方向（refusal+harm）提取 + 消融/注入/起始层三重验证
  run_cosine_matrix.py   # 研究问题2：跨话题余弦矩阵
  run_prompt_experiment.py # 阶段3：双方向×双读出位投影实验
  run_analysis.py        # 双 AUC、ROC、HARC 平面图
  smoke_test.py          # 合成张量数学自检（无需模型与 GPU）
tests/test_all.py        # CPU 单测（python tests/test_all.py）
data/topics/             # 中文话题对（5 话题 58 对）+ 中性指令集
notes/                   # formalism.md / lit_review.md / pain_points.md
blog/                    # 五节草稿（背景/方法/结果模板/防御/局限）
docs/zsrc_template.md    # ZSRC 负责任披露模板（漏洞盒子字段对照）
CLOUD.md                 # 云 GPU 手册 + 评测协议 + 预算
setup_container.sh       # 容器一键全链路（含重试兜底）
README_EN.md             # 英文镜像
```

## 快速开始（需 GPU）

```bash
bash setup_container.sh        # 一键全链路（推荐）

# 或分步：
pip install -r requirements.txt
python scripts/smoke_test.py                      # 1 分钟数学自检
python tests/test_all.py                          # CPU 单测
python scripts/run_extract.py --model zai-org/GLM-4-9B-Chat --out runs/glm9b --start-layer-sweep
python scripts/run_cosine_matrix.py --model zai-org/GLM-4-9B-Chat --direction runs/glm9b/direction.pt --out runs/glm9b
python scripts/run_prompt_experiment.py --model zai-org/GLM-4-9B-Chat --direction runs/glm9b/direction.pt --out runs/glm9b_prompts
python scripts/run_analysis.py --run runs/glm9b_prompts
```

无 GPU？`python tests/test_all.py` 与 `python scripts/smoke_test.py` 在纯 CPU 上验证全部数学。

## 评测协议（摘要，全文见 CLOUD.md）

greedy 主协议（单样本 98.7% 可靠）· 关键点 5 样本 @t≤0.3 + SSI · judge 一致性 κ 入报告 · 模板哈希全程记录 · 响应位读出（prefill 攻击 prompt 侧不失明）。

## 发布纪律

- repo 与 blog 只含方法论与无害化示例，不附有害 payload 原文（数据集为模板化占位）。
- 线上 API 侧发现先经 ZSRC（智谱，https://zcode.z.ai/cn/zsrc ，漏洞盒子提交）/ DeepSeek GitHub Security Policy 报告，待响应后公开对应细节。
