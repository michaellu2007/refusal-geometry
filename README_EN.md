# Refusal Geometry of Chinese LLMs

Is refusal of Chinese safety topics mediated by a single linear direction? And do successful prompt jailbreaks systematically suppress the projection onto that direction?

Primary models: `zai-org/GLM-4-9B-Chat`; comparisons: `deepseek-ai/DeepSeek-R1-Distill-Qwen-7B` / `-Qwen-1.5B` (debug tier).

Methodological basis:
- Arditi et al. 2024, *Refusal in Language Models Is Mediated by a Single Direction* (NeurIPS) — https://github.com/andyrdt/refusal_direction
- Wollschläger et al., *The Geometry of Refusal: Concept Cones* (arXiv 2502.17420)
- HARC, *Coupling Harmfulness and Refusal Directions* (arXiv 2607.00572)
- Full 42-paper annotated survey: [`notes/lit_review.md`](notes/lit_review.md) (in Chinese)

## Research questions

1. Is Chinese-topic refusal mediated by a single direction? (paired diff-in-means + layer scan with permutation baseline)
2. Do per-topic directions form a line, a cone, or multiple blocks? (`run_cosine_matrix.py`)
3. **Core**: do successful jailbreak prompts shift activations out of the refusal half-space? Measured as Δproj at two readout sites (prompt last token + mean-pooled first 8 response tokens, HARC-style) on the harm–refusal plane; AUC separates *geometric failure* from *expression suppression*.

## Layout

```
refusal_geometry/        # core package
  hooks.py               # residual-stream read / directional ablation / steering
  extract.py             # diff-in-means, layer scan, permutation baseline
  judge.py               # three-way REFUSE/HEDGE/COMPLY classifier
  prompts.py             # 5 prompt-rewrite families
  data.py                # AdvBench (official URL) + Chinese paired topics + neutral set
scripts/
  run_extract.py         # extract both directions + ablation/steering/start-layer validation
  run_cosine_matrix.py   # cross-topic cosine matrix (RQ2)
  run_prompt_experiment.py # families × dual directions × dual readouts (RQ3)
  run_analysis.py        # dual AUC, ROC, harm-refusal plane plot
  smoke_test.py          # synthetic-tensor math check (no model needed)
tests/test_all.py        # CPU unit tests
data/topics/             # 5 Chinese topic pairs (58 pairs) + neutral instructions
notes/                   # formalism.md (3 propositions), lit_review.md, pain_points.md
blog/                    # draft sections (Chinese)
docs/zsrc_template.md    # responsible-disclosure report template
setup_container.sh       # one-shot GPU pipeline
```

## Quick start (GPU)

```bash
pip install -r requirements.txt
python scripts/smoke_test.py                       # 1-min math check, no model
python scripts/run_extract.py --model zai-org/GLM-4-9B-Chat --out runs/glm9b
python scripts/run_cosine_matrix.py --model zai-org/GLM-4-9B-Chat --direction runs/glm9b/direction.pt --out runs/glm9b
python scripts/run_prompt_experiment.py --model zai-org/GLM-4-9B-Chat --direction runs/glm9b/direction.pt --out runs/glm9b_prompts
python scripts/run_analysis.py --run runs/glm9b_prompts
```

No GPU? `python tests/test_all.py` + `python scripts/smoke_test.py` verify all the math on synthetic tensors.

## Evaluation protocol

- Greedy decoding throughout (single greedy sample ≈ 98.7% reliable per arXiv 2512.12066); key conclusions re-run with 5 samples at t≤0.3 and reported with SSI.
- Three-way judging (REFUSE/HEDGE/COMPLY) to keep hedging out of both classes; judge-agreement (keyword vs LLM judge κ) reported.
- Chat-template hash recorded in every output (refusal can flip 65/75→0/75 with template changes, per arXiv 2605.30162).
- Prompt-side representation is measured **and** response-side (prefill-style attacks leave the prompt side intact, per arXiv 2607.14147).

## Disclosure discipline

- Repo and blog contain methodology and sanitized examples only — no harmful payloads.
- Any finding against hosted APIs is reported first (ZSRC for Zhipu via VulBox; GitHub Security Policy for DeepSeek); corresponding details are published only after vendor response.

## 中文主 README

见 [README.md](README.md)。
