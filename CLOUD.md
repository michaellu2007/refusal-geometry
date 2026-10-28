# 云 GPU 运行手册（AutoDL 为例）+ 预算

## 环境一键搭建

```bash
# AutoDL 选 PyTorch 2.x + CUDA 12.x 镜像，GPU: 4090 24GB（7-9B bf16）
# 数据盘执行：
git clone <你的repo> && cd refusal-geometry
pip install -r requirements.txt
# 国内加速下载模型
export HF_ENDPOINT=https://hf-mirror.com
python scripts/smoke_test.py                      # 1 分钟，数学自检
python scripts/run_extract.py --model zai-org/GLM-4-9B-Chat --out runs/glm9b
python scripts/run_extract.py --model deepseek-ai/DeepSeek-R1-Distill-Qwen-7B --out runs/r1_7b
# 两个模型都跑阶段 3
for m in glm9b r1_7b; do
  python scripts/run_prompt_experiment.py --model <对应model_id> \
    --direction runs/$m/direction.pt --out runs/${m}_prompts
  python scripts/run_analysis.py --run runs/${m}_prompts
done
```

## 模型 ID 对照

| 档位 | model_id | 显存(bf16) |
|---|---|---|
| 调试 | deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B | ~4 GB |
| 主实验 | zai-org/GLM-4-9B-Chat | ~19 GB |
| 对照 | deepseek-ai/DeepSeek-R1-Distill-Qwen-7B | ~15 GB |
| 加分项 | zai-org/GLM-4.5-Air（FP8, 106B） | 1×H800/H20 80GB |

## 预算（4090 ≈ ¥2.0/时）

| 阶段 | 估时 |
|---|---|
| 阶段2 提取+验证 ×2 模型 | 2-3 h |
| 阶段3 提示族实验 ×2 模型（~120 指令 × 6 变体 × 生成都算在内） | 4-6 h |
| 调试/重跑余量 | 3-4 h |
| **合计** | **¥20-30** |

GLM-4.5-Air 档（可选加分）：H800 约 ¥15-25/时 × 3-5h ≈ ¥50-120。

## 评测协议（依据 arXiv 2512.12066 SSI 研究，所有实验遵守）

1. **主实验一律 greedy（温度=0，do_sample=False）**：单样本与 20 配置真值一致率 98.7%，够用且最省卡时。
2. **关键结论点 5 样本复核**：对"进 blog 的每一个数字"用 t=0.3 × 5 种子重跑，报 SSI = max_c(n_c)/5；SSI < 0.8 的结论必须降级表述或加样本。
3. **judge 双轨一致性**：关键词三分类 vs LLM judge，报告 Cohen's κ（文献基线 0.62）；HEDGE 类必须 LLM judge 复核。
4. **翻转率入报告**：5 样本中出现 ≥2 类判定的比例，逐提示族统计——这是别人没有、审稿人喜欢的一列。
5. **模板哈希记录**：所有输出文件带 `tpl_hash`；换模板 = 重新跑全部对比实验，不许混用。
6. **失败即记录**：任何提示族在基线（无改写）上拒绝率 < 90%，先修数据集再跑实验（方向提取的假设前提是被拒）。

## 里程碑判定
1. validate.json：消融后有害拒绝率 < 50% 且注入后良性拒绝率 > 50% → 单方向假设在中文话题成立，继续
2. 若不成立 → 直接转"多方向结构"故事线，阶段 3 不变
3. AUC ≥ 0.7 → 核心命题成立，blog 按大纲第 4 节定理化写
