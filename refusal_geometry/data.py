"""数据加载：AdvBench 子集（英文标准）+ 自建中文话题对（topics_zh.yaml）。

成对结构（harmful / benign 仅差话题内核）是差异均值法的关键：
方向捕捉的是"话题危害性"而非"句式"，因此每对必须共享句式模板。
"""

import csv
import os
import urllib.request

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
# AdvBench 官方仓库（Zou et al. 2023, Universal and Transferable Adversarial Attacks）
ADVBENCH_URL = ("https://raw.githubusercontent.com/llm-attacks/llm-attacks/"
                "main/data/advbench/harmful_behaviors.csv")
TOPICS_PATH = os.path.join(HERE, "..", "data", "topics", "topics_zh.yaml")
NEUTRAL_PATH = os.path.join(HERE, "..", "data", "topics", "neutral_zh.yaml")


def load_topics(path: str = TOPICS_PATH):
    """返回 {topic: {"harmful": [...], "benign": [...]}}，两列表逐对配齐。"""
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_advbench(n: int = 100, cache: str = "data/advbench.csv"):
    """AdvBench harmful_behaviors.csv（英文标准，仅作对照子集）。"""
    if not os.path.exists(cache):
        urllib.request.urlretrieve(ADVBENCH_URL, cache)
    with open(cache, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    return [r["goal"].strip() for r in rows if r.get("goal")][:n]


def load_neutral(path: str = NEUTRAL_PATH):
    """中性指令集（话题无关的普通任务）：提取 harmfulness 方向的第二对照。"""
    with open(path, encoding="utf-8") as f:
        return [l.strip() for l in f if l.strip() and not l.strip().startswith("#")]


def topic_pairs(topics: dict, topic: str):
    """单个话题的 (harmful, benign) 指令对列表。"""
    t = topics[topic]
    assert len(t["harmful"]) == len(t["benign"]), f"话题 {topic} 两列表长度不一致"
    return list(zip(t["harmful"], t["benign"]))
