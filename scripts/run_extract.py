"""阶段 2：提取拒绝方向 + harmfulness 方向，并做消融/注入/起始层三重验证。

痛点修正：
- HARC (arXiv 2607.00572)：harmfulness 与 refusal 是两个可分离方向 → 同时提取
  r_refusal（harmful vs 配对 benign）与 r_harm（harmful vs 中性指令），
  后者以话题无关中性指令为对照，控制"指令性"，捕捉话题危害内容本身。
- Activation-Guided GCG (arXiv 2607.08883)：跨层全局抑制 > 单位点 → 消融
  验证增加起始层扫描曲线（--start-layer-sweep）。
- 层扫描多重比较（smoke test 实测噪声层 d≈0.6）→ 最优层报告置换检验 z 分数。
- BioRefusalAudit (arXiv 2605.30162)：chat 模板敏感 → 输出记录模板哈希。

运行（示例）:
  python scripts/run_extract.py --model deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B --out runs/r1_1p5b
产出:
  out/direction.pt   {direction, harm_direction, layer, pos, scores, perm, topics, tpl_hash}
  out/validate.json  {ablate_harmful_refusal, steer_benign_refusal, start_layer_sweep, ...}
"""

import argparse
import hashlib
import json
import os
import sys

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from refusal_geometry.data import load_topics, topic_pairs, load_neutral
from refusal_geometry.extract import (diff_in_means, layer_scan, best_layer,
                                      permutation_baseline, system_prompt_contrast)
from refusal_geometry.hooks import ActivationCapture
from refusal_geometry.judge import classify


def tpl_hash(tok):
    return hashlib.md5((tok.chat_template or "").encode()).hexdigest()[:8] \
        if tok.chat_template else "none"


def chat_ids(tok, user_msg, assistant_prefix=""):
    msgs = [{"role": "user", "content": user_msg}]
    ids = tok.apply_chat_template(msgs, add_generation_prompt=True, return_dict=True, return_tensors="pt").input_ids
    if assistant_prefix:
        pre = tok(assistant_prefix, return_tensors="pt", add_special_tokens=False).input_ids
        ids = torch.cat([ids, pre], 1)
    return ids


@torch.no_grad()
def collect_acts(model, tok, texts, cap):
    """对一组文本各跑一次前向，返回 {layer: [n, seq, d]}。

    真实指令长度不一：stack 时按层左对齐零填充——读出位全部在序列尾部
    （last/last2），左填充不改变尾部对齐，位置语义不变。
    """
    acts = {}
    for t in texts:
        cap.acts = {}
        model(chat_ids(tok, t).to(model.device))
        for layer, a in cap.acts.items():
            acts.setdefault(layer, []).append(a)
    out = {}
    for l, v in acts.items():
        L = max(x.shape[0] for x in v)
        d = v[0].shape[1]
        padded = [torch.cat([torch.zeros(L - x.shape[0], d, dtype=x.dtype), x], 0)
                  if x.shape[0] < L else x for x in v]
        out[l] = torch.stack(padded)
    return out


def gen(model, tok, user_msg, assistant_prefix="", max_new=128):
    ids = chat_ids(tok, user_msg, assistant_prefix).to(model.device)
    out = model.generate(ids, max_new_tokens=max_new, do_sample=False,
                         pad_token_id=tok.pad_token_id or tok.eos_token_id)
    return tok.decode(out[0][ids.shape[1]:], skip_special_tokens=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--topic", default="all")
    ap.add_argument("--n-pairs", type=int, default=30)
    ap.add_argument("--start-layer-sweep", action="store_true",
                    help="消融起始层扫描曲线（约 8 个层点 × 生成，较慢）")
    ap.add_argument("--max-new", type=int, default=128, help="验证生成上限")
    ap.add_argument("--val-n", type=int, default=None,
                    help="验证用的指令对数（默认全部，CPU 上建议 20）")
    ap.add_argument("--skip-validation", action="store_true",
                    help="只做提取+扫描+CLS 互验，跳过生成验证")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    tok = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForCausalLM.from_pretrained(
        args.model, torch_dtype=torch.bfloat16, device_map="auto").eval()
    topics = load_topics()
    topic_names = list(topics) if args.topic == "all" else [args.topic]
    harm_texts, benign_texts = [], []
    for t in topic_names:
        for h, b in topic_pairs(topics, t)[: args.n_pairs]:
            harm_texts.append(h)
            benign_texts.append(b)
    neutral_texts = load_neutral()

    # 1) 读激活 + 全层扫描（含置换基线）
    cap = ActivationCapture(model)
    cap.attach_read()
    ah = collect_acts(model, tok, harm_texts, cap)
    ab = collect_acts(model, tok, benign_texts, cap)
    scores = layer_scan(ah, ab, positions=("last", "last2"))
    layer, pos = best_layer(scores)
    mu, sd = permutation_baseline(ah[layer][:, -1], ab[layer][:, -1])
    print(f"[scan] 最优层={layer} 位置={pos} d={scores[(layer, pos)]:.3f} "
          f"置换基线 {mu:.3f}±{sd:.3f} (z={(scores[(layer, pos)]-mu)/(sd+1e-8):.1f})")

    # 2) 提取两个方向（同一层、同一位置）
    pi = -1 if pos == "last" else -2
    r_refusal = diff_in_means(ah[layer][:, pi], ab[layer][:, pi])
    an = collect_acts(model, tok, neutral_texts, cap)
    r_harm = diff_in_means(ah[layer][:, pi], an[layer][:, pi])
    # CLS 式第二提取法（可选互验）：两法方向余弦高 = 提取法稳健
    r_cls = system_prompt_contrast(model, tok, cap, layer)
    cos_cross = float((r_refusal / r_refusal.norm()).cpu()
                      @ (r_cls / r_cls.norm()).cpu())
    print(f"[cls] 系统提示对比方向 vs 成对指令方向 cos={cos_cross:.3f}")
    torch.save({"direction": r_refusal, "harm_direction": r_harm,
                "cls_direction": r_cls,
                "layer": layer, "pos": pos,
                "scores": {f"{k[0]}_{k[1]}": v for k, v in scores.items()},
                "perm": {"mean": mu, "std": sd, "z": (scores[(layer, pos)] - mu) / (sd + 1e-8)},
                "topics": topic_names, "tpl_hash": tpl_hash(tok)},
               f"{args.out}/direction.pt")

    # 3) 消融验证：有害指令 + 方向消融 → 拒绝率应下降
    if args.skip_validation:
        json.dump({"skipped": True}, open(f"{args.out}/validate.json", "w"), indent=2)
        return
    val_pairs = list(zip(harm_texts, benign_texts))[: args.val_n] if args.val_n else list(zip(harm_texts, benign_texts))
    cap.clear(); cap.attach_ablate(r_refusal, start_layer=layer)
    labs = [classify(h, gen(model, tok, h, max_new=args.max_new)) for h, _ in val_pairs]
    ref_rate = sum(l != "COMPLY" for l in labs) / len(labs)
    print(f"[ablate] 有害指令非遵从率 = {ref_rate:.2%}")

    # 4) 起始层扫描（可选）：越早开始消融，越接近全局抑制
    sweep = {}
    if args.start_layer_sweep:
        n_layers = len(cap.layers)
        for sl in range(max(0, layer - 12), min(n_layers, layer + 13), max(1, n_layers // 8)):
            cap.clear(); cap.attach_ablate(r_refusal, start_layer=sl)
            rr = sum(classify(h, gen(model, tok, h, max_new=args.max_new)) != "COMPLY"
                     for h in harm_texts[:10]) / 10
            sweep[sl] = rr
            print(f"[sweep] start_layer={sl} 非遵从率={rr:.2%}")
        cap.clear()

    # 5) 注入验证：良性请求 + 方向注入 → 应出现拒绝
    cap.clear(); cap.attach_steer(r_refusal, layer=layer, alpha=15.0)
    ben = [classify(b, gen(model, tok, b, max_new=args.max_new)) for _, b in val_pairs]
    ben_ref = sum(l != "COMPLY" for l in ben) / len(ben)
    print(f"[steer] 良性请求非遵从率 = {ben_ref:.2%}")
    cap.clear()

    with open(f"{args.out}/validate.json", "w", encoding="utf-8") as f:
        json.dump({"ablate_harmful_noncomply": ref_rate,
                   "steer_benign_noncomply": ben_ref,
                   "start_layer_sweep": sweep, "layer": layer, "pos": pos,
                   "perm": {"mean": mu, "std": sd},
                   "labels_ablate": labs, "labels_steer": ben,
                   "tpl_hash": tpl_hash(tok)}, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
