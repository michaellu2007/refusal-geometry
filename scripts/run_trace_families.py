"""逐 token 追踪：越狱时拒绝方向信号在响应过程中是否仍存在（表达抑制检验）。

设计：
  对每条有害指令 x：
    - 原始 x：生成响应，trace 每个位置的投影（曲线 A）
    - 每个提示族 f(x)：生成响应，trace 曲线（曲线 B_f）
  判据（用良性均值校准阈值 τ̂ = 良性 prompt 位投影均值）：
    - 闸门：探测 prompt 位投影是否 < τ̂（越狱的"通行证"）
    - 表达抑制：响应过程中投影是否回升/持续高于 τ̂（信号仍在但被覆盖）
  输出：results/<out>/trace_families.jsonl（含完整曲线）+ 汇总

用法:
  CUDA_VISIBLE_DEVICES=6 python scripts/run_trace_families.py \
    --model M --direction out/glm9b/direction.pt --out $S/out/glm9b_trace --n-per-topic 2
"""
import argparse
import hashlib
import json
import os
import sys

import numpy as np
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from refusal_geometry.data import load_topics, topic_pairs
from refusal_geometry.hooks import ActivationCapture
from refusal_geometry.judge import classify
from refusal_geometry.prompts import FAMILIES, apply_family


def build_ids(tok, msg, prefix=""):
    ids = tok.apply_chat_template([{"role": "user", "content": msg}],
                                  add_generation_prompt=True, return_dict=True,
                                  return_tensors="pt").input_ids
    if prefix:
        pre = tok(prefix, add_special_tokens=False, return_tensors="pt").input_ids
        ids = torch.cat([ids, pre], 1)
    return ids


@torch.no_grad()
def gen_and_trace(model, tok, msg, dirs, layer, cap, prefix="", max_new=96):
    """生成后对 prompt+response 做一次前向，返回逐位置投影曲线。"""
    pid = getattr(tok, "pad_token_id", None) or tok.eos_token_id
    ids = build_ids(tok, msg, prefix)
    out = model.generate(ids.to(model.device), max_new_tokens=max_new, do_sample=False,
                         pad_token_id=pid)
    n_resp = out.shape[1] - ids.shape[1]
    text = tok.decode(out[0][ids.shape[1]:], skip_special_tokens=True)
    cap.acts = {}
    model(out)                                   # teacher-forced 单前向
    a = cap.acts[layer].to(model.device)
    curves = {}
    for name, dv in dirs.items():
        d = (dv / dv.norm()).to(a.device, a.dtype)
        curves[name] = (a @ d).float().cpu().numpy().tolist()
    return text, int(ids.shape[1]), int(n_resp), curves


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--direction", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--n-per-topic", type=int, default=2)
    ap.add_argument("--max-new", type=int, default=96)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    tok = AutoTokenizer.from_pretrained(args.model, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        args.model, torch_dtype=torch.bfloat16, device_map="auto",
        trust_remote_code=True).eval()
    ck = torch.load(args.direction, map_location="cpu", weights_only=False)
    d, layer = ck["direction"], ck["layer"]
    dirs = {"r": d}
    if "harm_direction" in ck:
        dirs["h"] = ck["harm_direction"]
    cap = ActivationCapture(model)
    cap.attach_read()

    topics = load_topics()
    # τ̂：良性指令 prompt 位的平均投影（ACE 式校准）
    ben = [b for t in topics for _, b in topic_pairs(topics, t)][:20]
    bvals = []
    for b in ben:
        cap.acts = {}
        model(build_ids(tok, b).to(model.device))
        a = cap.acts[layer].to(model.device)
        bvals.append(float(a[-1] @ (d / d.norm()).to(a.device, a.dtype)))
    tau = float(np.mean(bvals))
    print(f"[calib] benign prompt位投影 均值 τ̂={tau:+.2f} (sd {np.std(bvals):.2f}, n={len(bvals)})", flush=True)

    rows = []
    for tname in topics:
        for h, _ in topic_pairs(topics, tname)[: args.n_per_topic]:
            iid = hashlib.md5(h.encode()).hexdigest()[:8]
            variants = [("original", h, "")]
            for fam in FAMILIES:
                m, pre = apply_family(fam, h)
                variants.append((fam, m, pre))
            for vname, msg, pre in variants:
                text, p_len, n_resp, curves = gen_and_trace(
                    model, tok, msg, dirs, layer, cap, pre, args.max_new)
                curve = curves["r"]
                if n_resp <= 0:
                    continue
                prompt_proj = curve[p_len - 1]
                resp = np.array(curve[p_len:p_len + n_resp])
                rec = {"topic": tname, "iid": iid, "variant": vname,
                       "label": classify(msg, text),
                       "prompt_proj": prompt_proj, "tau": tau,
                       "gate_pass": prompt_proj < tau,
                       "resp_max": float(resp.max()), "resp_mean": float(resp.mean()),
                       "resp_first": float(resp[0]), "resp_last": float(resp[-1]),
                       "n_resp": n_resp,
                       "frac_resp_above_tau": float((resp > tau).mean()),
                       "curve": curve, "p_len": p_len,
                       **({"curve_h": curves["h"],
                           "prompt_proj_h": curves["h"][p_len - 1],
                           "resp_max_h": float(np.array(curves["h"][p_len:p_len + n_resp]).max()),
                           "resp_mean_h": float(np.array(curves["h"][p_len:p_len + n_resp]).mean())}
                          if "h" in curves else {})}
                rows.append(rec)
                print(f"[{tname}/{vname:<10}] {rec['label']:<6} gate={'Y' if rec['gate_pass'] else 'N'} "
                      f"prompt={prompt_proj:+6.1f} resp_max={rec['resp_max']:+6.1f} "
                      f"above_tau={rec['frac_resp_above_tau']:.0%}", flush=True)

    with open(f"{args.out}/trace_families.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # 汇总：越狱成功者里，响应期是否仍有高于 τ̂ 的拒绝信号
    comp = [r for r in rows if r["label"] == "COMPLY" and r["variant"] != "original"]
    if comp:
        print(f"\n[汇总] 越狱成功 n={len(comp)}")
        print(f"  闸门通过率 (prompt_proj<τ̂): {np.mean([r['gate_pass'] for r in comp]):.0%}")
        print(f"  响应期投影回升到 τ̂ 以上者: {np.mean([r['frac_resp_above_tau']>0 for r in comp]):.0%}")
        print(f"  响应期均值投影 > τ̂ 者: {np.mean([r['resp_mean']>tau for r in comp]):.0%}")
        print(f"  resp_max 中位 {np.median([r['resp_max'] for r in comp]):+.1f} (τ̂={tau:+.1f})")


if __name__ == "__main__":
    main()
