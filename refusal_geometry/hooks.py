"""Residual stream hooks：读取激活、方向消融（ablation）、方向注入（steering）。

用法:
    cap = ActivationCapture(model)          # 每个 decoder layer 输出处挂 hook
    cap.attach_read()                       # 记录激活到 cap.acts[layer][pos]
    cap.attach_ablate(direction, layer)     # 从指定层起投影消融
    cap.attach_steer(direction, layer, alpha)
    cap.clear()                             # 摘除全部 hook
"""

import torch
from torch import Tensor


def _decoder_layers(model):
    """兼容 GLM/Qwen/Llama 系列的 decoder layer 容器命名。

    已覆盖：Llama/Qwen(model.layers)、GLM-4(transformer.encoder.layers)、
    GPT(transformer.h)、OPT(model.decoder.layers)、PEFT 包装(base_model.model.layers)。
    """
    for attr in ("model.layers", "transformer.encoder.layers", "transformer.h",
                 "model.decoder.layers", "base_model.model.layers"):
        obj = model
        for a in attr.split("."):
            if hasattr(obj, a):
                obj = getattr(obj, a)
            else:
                obj = None
                break
        if obj is not None:
            return obj
    raise AttributeError(f"未找到 decoder layers，模型结构: {type(model)}")


def project_out(x: Tensor, direction: Tensor) -> Tensor:
    """消融：x 减去其在单位方向上的投影（对最后一维）。"""
    d = direction / direction.norm()
    coef = torch.einsum("...d,d->...", x, d).unsqueeze(-1)
    return x - coef * d


class ActivationCapture:
    def __init__(self, model):
        self.model = model
        self.layers = _decoder_layers(model)
        self.handles = []
        self.read_on = False
        self.acts = {}          # layer_idx -> [seq_len, d_model]（单条输入）
        self.acts_batch = {}    # layer_idx -> [batch, seq_len, d_model]

    # ---------- 读激活 ----------
    def attach_read(self):
        self.read_on = True
        self.acts, self.acts_batch = {}, {}

        def mk(idx):
            def hook(_m, _inp, out):
                h = out[0] if isinstance(out, tuple) else out
                if h.shape[0] == 1:
                    self.acts[idx] = h[0].detach().float().cpu()
                else:
                    self.acts_batch.setdefault(idx, []).append(h.detach().float().cpu())
            return hook

        for i, layer in enumerate(self.layers):
            self.handles.append(layer.register_forward_hook(mk(i)))

    # ---------- 方向消融：从 layer 起，所有后续层前的残差均消融 ----------
    def attach_ablate(self, direction: Tensor, start_layer: int = 0):
        p = next(self.model.parameters())
        d = (direction / direction.norm()).to(p.device, p.dtype)

        def hook(_m, _inp, out):
            h = out[0] if isinstance(out, tuple) else out
            h2 = project_out(h, d)
            # 结构保持：输入是 tuple（如 Qwen2 的 (hidden, attn...)）就返回 tuple，
            # 否则返回裸 Tensor——否则下一层收到错误结构
            return (h2,) + tuple(out[1:]) if isinstance(out, tuple) else h2

        for i, layer in enumerate(self.layers):
            if i >= start_layer:
                self.handles.append(layer.register_forward_hook(hook))

    # ---------- 方向注入：h -> h + alpha * d ----------
    def attach_steer(self, direction: Tensor, layer: int, alpha: float = 10.0):
        p = next(self.model.parameters())
        d = (direction / direction.norm()).to(p.device, p.dtype)

        def hook(_m, _inp, out):
            h = out[0] if isinstance(out, tuple) else out
            h = h + alpha * d
            return (h,) + tuple(out[1:]) if isinstance(out, tuple) else h

        self.handles.append(self.layers[layer].register_forward_hook(hook))

    def clear(self):
        for h in self.handles:
            h.remove()
        self.handles = []
        self.read_on = False
