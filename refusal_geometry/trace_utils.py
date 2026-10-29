"""逐 token 投影曲线的统计逻辑（CPU-only，无模型依赖，可单测）。"""

import numpy as np


def summarize(trace: dict) -> dict:
    """trace: {prompt_len, n_resp, think_end, curve}。返回分段统计。

    cliff_drop = 思维链段均值 − 输出段均值；正值即 Refusal Cliff 形态
    （arXiv 2510.06036：拒绝意图在思维链中强劲、输出前骤降）。
    """
    c = np.array(trace["curve"], dtype=float)
    p, n, te = trace["prompt_len"], trace["n_resp"], trace["think_end"]
    resp = c[p:p + n]
    if len(resp) == 0:
        resp = c[-1:]
    out = {
        "prompt_proj": float(c[p - 1]) if p > 0 else None,
        "resp_first": float(resp[0]),
        "resp_last": float(resp[-1]),
        "resp_mean": float(resp.mean()),
    }
    if te and p < te < p + n:
        out["think_mean"] = float(resp[:te - p].mean())
        out["post_mean"] = float(resp[te - p:].mean())
        out["cliff_drop"] = out["think_mean"] - out["post_mean"]
    return out
