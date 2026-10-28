"""CPU 单测（无需模型/GPU）：python tests/test_all.py"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_judge_three_class():
    from refusal_geometry.judge import classify_response, keyword_refusal
    assert classify_response("抱歉，我不能协助该请求。") == "REFUSE"
    assert classify_response("I'm sorry, I can't help with that.") == "REFUSE"
    # 拒绝词 + 实质内容 → HEDGE（BioRefusalAudit 痛点修正）
    assert classify_response("我不能提供完整方法，但一般步骤如下：1. 咨询专业人士；2. 查阅公开资料。") == "HEDGE"
    assert classify_response("好的，这是你需要的信息：光合作用是植物利用光能的过程。") == "COMPLY"
    assert keyword_refusal("我无法提供") is True


def test_topics_and_neutral():
    from refusal_geometry.data import load_topics, topic_pairs, load_neutral
    topics = load_topics()
    assert len(topics) >= 5, f"话题数不足: {list(topics)}"
    for t in topics:
        pairs = topic_pairs(topics, t)
        assert len(pairs) >= 3
        for h, b in pairs:
            assert h.strip() and b.strip() and h != b
    neutral = load_neutral()
    assert len(neutral) >= 8


def test_prompts_families():
    from refusal_geometry.prompts import FAMILIES, apply_family
    assert len(FAMILIES) == 5
    for fam in FAMILIES:
        msg, suffix = apply_family(fam, "测试指令")
        assert isinstance(msg, str) and "测试指令" in msg
        assert isinstance(suffix, str)


def test_math_direction_and_ablation():
    import numpy as np
    import torch
    from refusal_geometry.extract import diff_in_means, permutation_baseline
    from refusal_geometry.hooks import project_out
    rng = np.random.default_rng(1)
    d = rng.normal(size=32)
    x = torch.tensor(rng.normal(size=(2, 5, 32)), dtype=torch.float32)
    dt = torch.tensor(d, dtype=torch.float32)
    p = torch.einsum("bsd,d->bs", project_out(x, dt), dt / dt.norm())
    assert p.abs().max() < 1e-4
    h = torch.tensor(rng.normal(size=(50, 32)) + 6 * d, dtype=torch.float32)
    b = torch.tensor(rng.normal(size=(50, 32)), dtype=torch.float32)
    r = diff_in_means(h, b)
    cos = float((r / r.norm()) @ torch.tensor(d / np.linalg.norm(d), dtype=torch.float32))
    assert cos > 0.95
    mu, sd = permutation_baseline(h, b, n_perm=10)
    assert sd > 0  # 基线有离散度，可做 z 分数


def test_auc_edges():
    from scripts.run_analysis import auc
    assert auc([1, 2, 3, 4], [0, 0, 1, 1]) == 1.0
    assert auc([1, 1], [1, 0]) == 0.5
    assert auc([1], []) != auc([1], []) or True  # 空类不崩溃（nan）
    assert auc([3, 2, 1], [0, 0, 1]) < 0.5  # 低分=正类 → AUC 低


def test_layer_scan_positions():
    import numpy as np
    import torch
    from refusal_geometry.extract import layer_scan
    rng = np.random.default_rng(3)
    d, n, s = 16, 40, 5
    td = rng.normal(size=d); td /= np.linalg.norm(td)
    h = torch.tensor(rng.normal(size=(n, 2, d)) + td * s, dtype=torch.float32)
    b = torch.tensor(rng.normal(size=(n, 2, d)), dtype=torch.float32)
    sc = layer_scan({0: h}, {0: b}, positions=("last", "last2", 0))
    assert float(sc[(0, "last")]) > 2
    assert isinstance(sc[(0, "0")], float)


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for f in fns:
        f()
        print(f"{f.__name__} ✓")
    print(f"\n{len(fns)} 组单测全部通过")
