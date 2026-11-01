"""干预位点全扫描：ablation 起始层 × steering 层，定位拒绝的因果窗口。

判读：
  - 注入在层 L 有效 → L 及之前的信息流足以诱发拒绝（充分性位点）
  - 从层 L 起消融有效 → L 之后的计算依赖该方向（必要性位点）
  - 两者错位 = 方向"必要但不充分"，因果窗口在中段

用法:
  python scripts/run_site_sweep.py --model M --direction out/glm9b/direction.pt --out out/glm9b_sites
"""
import argparse
import json
import os
import sys

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from refusal_geometry.data import load_topics, topic_pairs
from refusal_geometry.hooks import ActivationCapture
from refusal_geometry.judge import classify


def chat_ids(tok, msg):
    return tok.apply_chat_template([{"role": "user", "content": msg}],
                                   add_generation_prompt=True, return_dict=True,
                                   return_tensors="pt").input_ids


@torch.no_grad()
def gen(model, tok, msg, max_new=64):
    ids = chat_ids(tok, msg).to(model.device)
    out = model.generate(ids, max_new_tokens=max_new, do_sample=False,
                         pad_token_id=getattr(tok, "pad_token_id", None) or tok.eos_token_id)
    return tok.decode(out[0][ids.shape[1]:], skip_special_tokens=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--direction", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--n", type=int, default=6)
    ap.add_argument("--alpha", type=float, default=30.0)
    ap.add_argument("--max-new", type=int, default=64)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    tok = AutoTokenizer.from_pretrained(args.model, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        args.model, torch_dtype=torch.bfloat16, device_map="auto",
        trust_remote_code=True).eval()
    ck = torch.load(args.direction, map_location="cpu", weights_only=False)
    d, best = ck["direction"], ck["layer"]
    cap = ActivationCapture(model)
    n_layers = len(cap.layers)

    topics = load_topics()
    benign = [b for t in topics for _, b in topic_pairs(topics, t)][: args.n]
    harmful = [h for t in topics for h, _ in topic_pairs(topics, t)][: args.n]

    # 层点：四分之一到最优层之间均布，末层附近加密
    fracs = [0.25, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    layers = sorted({min(n_layers - 1, int(round(f * best))) for f in fracs})

    results = {"model": args.model, "best_layer": best, "n_layers": n_layers,
               "alpha": args.alpha, "steer": {}, "ablate": {}}

    base_b = [classify(b, gen(model, tok, b, args.max_new)) for b in benign]
    base_h = [classify(h, gen(model, tok, h, args.max_new)) for h in harmful]
    results["baseline"] = {
        "benign_noncomply": sum(l != "COMPLY" for l in base_b) / len(base_b),
        "harmful_noncomply": sum(l != "COMPLY" for l in base_h) / len(base_h)}
    print(f"[baseline] benign_noncomply={results['baseline']['benign_noncomply']:.0%} "
          f"harmful_noncomply={results['baseline']['harmful_noncomply']:.0%}", flush=True)

    for L in layers:
        cap.clear(); cap.attach_steer(d, layer=L, alpha=args.alpha)
        r = sum(classify(b, gen(model, tok, b, args.max_new)) != "COMPLY" for b in benign) / len(benign)
        results["steer"][L] = r
        print(f"[steer ] L={L:>2} alpha={args.alpha:.0f} benign非遵从={r:.0%}", flush=True)

    for L in layers:
        cap.clear(); cap.attach_ablate(d, start_layer=L)
        r = sum(classify(h, gen(model, tok, h, args.max_new)) != "COMPLY" for h in harmful) / len(harmful)
        results["ablate"][L] = r
        print(f"[ablate] start={L:>2} harmful非遵从={r:.0%}", flush=True)

    cap.clear()
    json.dump(results, open(f"{args.out}/site_sweep.json", "w"), indent=2)


if __name__ == "__main__":
    main()
