# 第二轮实验协议（纠错版）

> 针对第一轮 REPORT.md「局限」逐条纠错。每阶段独立可断点续跑（标记文件见远端 out/ROUND2/）。

## 纠错对照表（第一轮局限 → 第二轮对策）

| 第一轮局限 | 第二轮对策 | 落在阶段 |
|---|---|---|
| n 太小（6~20/条件） | 全部升到 n≥30（位点扫描 12、提示族 60 指令×5 族=300） | S2/S4/S5 |
| 只有关键词分类器 | LLM judge（Ollama 27B 当判官）双轨 + Cohen's κ | S7 |
| 单次 greedy 无稳定性 | 子集 40 条 × 3 次 @t=0.3，报 SSI 翻转率 | S7 |
| 消融只有"从层 L 起全消" | 新增**单层消融**（只消 L19 一层），区分全局 vs 局部机制 | S6 |
| 注入只有单一 α=30 | α ∈ {10,30,60} × 层 {15,19,23} 完整剂量-位点扫描 | S6 |
| 响应位投影循环性 | 改用 prompt 位 + 框架不变探针为主判据；响应位仅作辅助 | S4/S5 |
| 未验证写读分离是否普遍 | Qwen2.5-7B-Instruct 上重复位点扫描（ModelScope 直拉） | S8（可选） |

## 阶段清单（由 round2_driver.py 在 .32 上顺序执行）

- S1: ModelScope 拉取 GLM-4-9B-Chat（18GB）→ models2/
- S2: run_extract --val-n 30 --max-new 96（基线+层扫描+消融/注入 n=30）
- S3: extract_at_layer --layer 19（因果层方向，n=60 指令）
- S4: run_prompt_experiment --n-pairs 12 --direction L38 → 300 条 records（含 resp_full）
- S5: run_prompt_experiment --n-pairs 12 --direction L19 → 300 条 records
- S6: 位点×剂量完整扫描（注入 α{10,30,60}×层{15,19,23}；单层消融 L17/19/21/23）n=12
- S7: judge_dual（LLM 判官双轨 + κ）+ SSI 子集（40×3@t=0.3）+ analyze_necessity
- S8: （可选）Qwen2.5-7B-Instruct 位点扫描

## 完成判据

out/ROUND2/stage8.done 存在 → 驱动脚本把全部 json/jsonl/png 拉回本地 results/ROUND2/。
