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

## 里程碑判定
1. validate.json：消融后有害拒绝率 < 50% 且注入后良性拒绝率 > 50% → 单方向假设在中文话题成立，继续
2. 若不成立 → 直接转"多方向结构"故事线，阶段 3 不变
3. AUC ≥ 0.7 → 核心命题成立，blog 按大纲第 4 节定理化写
