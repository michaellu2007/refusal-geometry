"""方向注入的 alpha × layer 扫描：定位 GLM 上"注不进"的原因。

用法: python scripts/run_steer_sweep.py --model M --direction out/glm9b/direction.pt --out out/glm9b_sweep
"""
import argparse
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
    ap.add_argument("--max-new", type=int, default=64)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    tok = AutoTokenizer.from_pretrained(args.model, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        args.model, torch_dtype=torch.bfloat16, device_map="auto",
        trust_remote_code=True).eval()
    ck = torch.load(args.direction, map_location="cpu", weights_only=False)
    d, best_layer = ck["direction"], ck["layer"]
    n_layers = len(ActivationCapture(model).layers)

    topics = load_topics()
    benign = [b for t in topics for _, b in topic_pairs(topics, t)][: args.n]
    harmful = [h for t in topics for h, _ in topic_pairs(topics, t)][: args.n]

    cap = ActivationCapture(model)
    # 基线：良性请求本应被遵从
    base = [classify(b, gen(model, tok, b, args.max_new)) for b in benign]
    print(f"[baseline] 良性非遵从率 = {sum(l != 'COMPLY' for l in base)/len(base):.0%}", flush=True)

    layers = sorted({max(0, best_layer - 18), best_layer // 2, best_layer})
    for layer in layers:
        for alpha in (15.0, 30.0, 60.0):
            cap.clear()
            cap.attach_steer(d, layer=layer, alpha=alpha)
            labs = [classify(b, gen(model, tok, b, args.max_new)) for b in benign]
            rate = sum(l != "COMPLY" for l in labs) / len(labs)
            print(f"[steer] layer={layer:>2} alpha={alpha:>5.0f} 良性非遵从率={rate:.0%}", flush=True)
    cap.clear()

    # 对照：注哪些层消融最有效（起始层扫描，少量样本）
    cap.attach_ablate(d, start_layer=best_layer)
    labs = [classify(h, gen(model, tok, h, args.max_new)) for h in harmful]
    print(f"[ablate@L{best_layer}] 有害非遵从率 = {sum(l != 'COMPLY' for l in labs)/len(labs):.0%}", flush=True)
    cap.clear()


if __name__ == "__main__":
    main()
