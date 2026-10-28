#!/usr/bin/env bash
# 容器一键全链路（AutoDL / 任意 24GB+ GPU）
# 用法: bash setup_container.sh
# 兜底: 每步失败自动重试 3 次；单模型失败不阻塞后续（记录到 runs/FAILURES.log）
set -uo pipefail
cd "$(dirname "$0")"

retry() {  # retry <cmd...>：最多 3 次，间隔 20s（防"系统繁忙"类瞬断）
  for i in 1 2 3; do
    "$@" && return 0
    echo "[retry] 第 $i 次失败: $*" >&2
    sleep 20
  done
  return 1
}

FAIL=runs/FAILURES.log; mkdir -p runs; : > "$FAIL"
step() {  # step <名字> <cmd...>：失败记日志不中断
  echo "=== $1 ==="; shift
  retry "$@" || echo "$(date +%F' '%T) $1" >> "$FAIL"
}

step "依赖安装" pip install -r requirements.txt
export HF_ENDPOINT="${HF_ENDPOINT:-https://hf-mirror.com}"

step "数学自检" python scripts/smoke_test.py
step "单测" python tests/test_all.py

GLM=zai-org/GLM-4-9B-Chat
R1=deepseek-ai/DeepSeek-R1-Distill-Qwen-7B

step "glm9b-extract"   python scripts/run_extract.py --model $GLM --out runs/glm9b --start-layer-sweep
step "r1-extract"      python scripts/run_extract.py --model $R1  --out runs/r1_7b --start-layer-sweep
step "glm9b-cosine"    python scripts/run_cosine_matrix.py --model $GLM --direction runs/glm9b/direction.pt --out runs/glm9b
step "glm9b-prompts"   python scripts/run_prompt_experiment.py --model $GLM --direction runs/glm9b/direction.pt --out runs/glm9b_prompts
step "r1-prompts"      python scripts/run_prompt_experiment.py --model $R1  --direction runs/r1_7b/direction.pt --out runs/r1_7b_prompts
step "glm9b-analysis"  python scripts/run_analysis.py --run runs/glm9b_prompts
step "r1-analysis"     python scripts/run_analysis.py --run runs/r1_7b_prompts

echo; echo "全部完成。失败步骤（如有）见 $FAIL"
echo "带回: runs/*/validate.json, records.jsonl, analysis.png, cosine_matrix.json, direction.pt"
