# The Refusal Geometry of Chinese LLMs: One Vector, Prompt Translations, and a Dot-Product Detector

> English mirror skeleton v1 (section-level; expand after GPU results fill placeholders in full_draft.md).

## TL;DR

- On open weights of GLM-4-9B-Chat and DeepSeek-R1-Distill-Qwen-7B, we extract refusal directions using **paired Chinese native-topic instructions** and test whether "refusal = a single linear direction" (Arditi et al., NeurIPS 2024) holds in Chinese. Our cross-topic cosine matrix yields three readable outcomes: single direction / concept cone (arXiv:2502.17420) / multi-direction blocks — 【measured: pending】.
- We formalize prompt jailbreaks as **translations in activation space**: a rewrite only shifts activations by δ_f; its projection onto the refusal direction (Δz) against a calibrated threshold decides success (Proposition 3; threshold calibration follows ACE standardization, arXiv:2411.09003).
- Core experiment: 5 prompt-rewrite families × two directions (refusal/harm, the HARC plane) × two readout sites (last prompt token + mean-pooled first 8 response tokens) × 58 Chinese topic pairs. The criterion is AUC: **high AUC = geometric failure; AUC ≈ 0.5 with nonzero compliance = expression suppression** — behaviorally indistinguishable, separable only by projection analysis.【measured: pending】
- If geometric failure dominates, a **one-dot-product-per-token** response-site projection monitor can jailbreak-check online (cost argument: RAS white-box scoring is 216× faster than judge-based evaluation, arXiv:2606.25750).
- Code, template-only data (no payloads), and a results-decision runbook are open-sourced; hosted-API findings go through responsible disclosure first.

## 1 Background

Single direction (arXiv:2406.11717) → affine function + calibrated threshold (ACE, arXiv:2411.09003) → concept cones up to 5 dims (arXiv:2502.17420) → per-prompt heterogeneity (WRDO, arXiv:2610.29555) → secondary directions for role-play (arXiv:2502.09674) → two separable directions with attack classes occupying separable regions of the harm-refusal plane (HARC, arXiv:2607.00572) → prefill jailbreaks leave harm representation intact while refusal collapses at the response site (arXiv:2607.14147).

**The Chinese gap, stated precisely**: PolyRefuse showed cross-lingual universality with Chinese as an extraction source (arXiv:2505.17306); XSafety quantified Chinese unsafe rates (8.1% vs 1.0% English for ChatGPT, arXiv:2310.00905). The open questions are: per-**topic** (not per-language) decomposition of Chinese refusal geometry; the geometric footprint of **black-box prompt rewrites**; **readout sites in reasoning models** (cf. Refusal Cliff, arXiv:2510.06036); and GLM's early/late divergence topology (CLS covered only Llama/Qwen, arXiv:2606.22686).

## 2 Method

- **Extraction**: paired diff-in-means (harmful vs benign sharing sentence templates, 58 pairs over 5 topics) for r_refusal; harmful vs topic-unrelated neutral for r_harm. Layer scan with **permutation-test baselines** (noise layers reach d ≈ 0.6 — most prior work does not report this).
- **Proposition 2 (calibrated half-space)**: ablation zeroes z; steering shifts it; τ is calibrated to the benign mean per ACE standardization, τ̂ = ⟨r̂, μ_benign⟩.
- **Proposition 3 (prompts as translations)**: rewrites move activations by δ_f(x); Δz = ⟨δ_f, r̂⟩; P(jailbreak) = 𝟙[z+Δz<τ] + ε. High AUC(−Δz → success) ⇒ geometric failure; flipped behavior with Δz ≈ 0 ⇒ expression suppression. ε is measured by 1 − AUC.
- **Readout sites**: prompt last token + first response token + 8-token pooled (Kwon: prefill attacks leave the prompt side intact — prompt-side-only monitors are structurally blind to them).
- **Protocol**: greedy main protocol (98.7% single-sample reliability, arXiv:2512.12066) + 5 samples @ t≤0.3 with SSI for key claims; three-way REFUSE/HEDGE/COMPLY judging; chat-template hash everywhere; instruction hashes instead of payloads.

## 3 Results 【pending】

- Layer scan peak 【】 (vs RAS windows: Qwen L22-26 / Llama L22-30); z = 【】
- Ablated refusal 【】 / steered benign refusal 【】 (1.5B negative control: both 0% on the unaligned distill)
- Cosine matrix outcome: 【single / cone / multi】
- Dual AUC table 【】; HARC-plane scatter with family priors 【persona→DAN, encoding→CodeAttack, academic→PAIR】
- R1 cliff: median cliff_drop 【】; positive-cliff share 【%】

## 4 For defenders

A response-site projection monitor: one dot product per generated token, zero extra forward passes. Two-direction version alarms by HARC-plane quadrant. Honest limits: directions can be adversarially targeted (arXiv:2607.08883); low cross-topic cosine (if outcome C) means single-direction monitoring has blind spots; thresholds calibrated on benign pairs with reported FPR.

Training-side recommendations: **DeepRefusal** (probabilistic ablation during training; LoRA, 45 min on one A100; Prefilling ASR 86.8%→0.4%, arXiv:2509.15202) + **SSRFT** (safe-role internalization halves prefill-induced ASR gains while *improving* over-refusal, arXiv:2610.07023), both needing ACE-style calibration (harmful-only training reaches 74% XSTest over-refusal).

## 5 Limitations

Single-turn; 8- vs 32-token pooling; small neutral contrast set (12); mixed judge; white-box ≠ hosted; ε decomposition is a framework, not an attribution; scale extrapolation unverified.

## Reproduction & disclosure

`bash setup_container.sh` (any 24GB GPU, ≈ ¥20-30); `RUNBOOK_RESULTS.md` is the results decision tree. Template-only data; hosted-API findings go through ZSRC / GitHub Security Policy before publication.

## References

See `references.bib` (48 entries) and `notes/lit_review.md` (48 annotated papers, 16 deep-read).
