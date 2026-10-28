# 痛点综合 → 本项目改进映射

> 来源：lit_review.md 40 篇的"痛点"列。每条映射到具体代码位置或协议条款。

| # | 痛点 | 证据论文 | 我们的改进 | 落点 |
|---|---|---|---|---|
| 1 | 单方向假设在多话题下存疑（方向异质、锥结构、复杂包装击穿） | WRDO / 概念锥 / REINS / Hidden Dimensions | 分话题方向余弦矩阵，三结局判据 | scripts/run_cosine_matrix.py |
| 2 | prompt 侧监控对响应位攻击盲（prefill 攻击 prompt 表示不变） | Kwon 2607.14147 / HARC | 双读出位投影（prompt + 响应首 token） | run_prompt_experiment.py |
| 3 | 只追踪拒绝方向，漏掉 harmfulness 方向（攻击类在平面可分） | HARC 2607.00572 | 双方向提取（harmful vs 配对良性 + harmful vs 中性）+ 2D 平面图 | run_extract.py / run_analysis.py |
| 4 | 单次评测 18-28% 判定翻转，多数论文仍单次 greedy | Instability 2512.12066 | 温度=0 全程 + 关键点 5 样本 + 翻转率入报告 | CLOUD.md 协议节 |
| 5 | hedging 被误分类，拒绝≠拒绝（拒绝跟踪合法性而非危害） | BioRefusalAudit 2605.30162 | judge 三分类 REFUSE/HEDGE/COMPLY | refusal_geometry/judge.py |
| 6 | chat 模板格式可完全翻转拒绝行为（65/75→0/75） | BioRefusalAudit | 固定模板 + 模板哈希写入所有输出 | run_extract/run_prompt_experiment |
| 7 | 层选择多重比较（噪声层 d≈0.6 被误选） | smoke test 实测 + Arditi 未处理 | 置换检验基线，最优层报 z 分数 | extract.py permutation_baseline |
| 8 | 消融/注入只做单层起始、均匀施加 | Depth Gaussian 2512.07667 / AG-GCG | 起始层扫描曲线（--start-layer-sweep）；高斯调度列加分项 | run_extract.py |
| 9 | 中文原生话题缺口（跨语言工作全是翻译语料） | PolyRefuse / XSafety | 中文原生话题对 + 定位声明 | data/topics/topics_zh.yaml |
| 10 | ASR 饱和、攻击者中心指标无助于防守 | A-MESS / Adaptive Attacks | 投影分数=防守者友好型机制指标（prompt 级越狱检测器） | run_analysis.py AUC + blog 防御节 |

## 空白（= 我们的差异化卖点）
1. 中文原生话题的拒绝几何（话题间余弦结构）——无人做过
2. 提示词改写=激活平移的定量刻画（Δproj 与越狱成败的 AUC）——黑盒提示词与白盒几何之间缺这座桥
3. 推理模型（R1 系）思维链中的拒绝方向读出位置——Kwon 只做了 1.5-14B 非推理模型
4. GLM 系模型的"早分歧/晚决策"拓扑分类——CLS 只分了 Llama/Qwen

## 失败兜底协议（防"系统繁忙/重试超限"）
- 每轮定时任务 = 一个原子单元；先标 `[~]` 再动工，写完标 `[x]`；崩溃留 `[~]` 下一轮接管
- 网络降级链：WebFetch 全文 → paper-search 摘要 → WebSearch 摘要 → 标 `!跳过` 记日志
- 文件写入策略：逐条追加（append per unit），绝不在内存攒批
- 重试上限：同一项失败 2 次标 `!跳过`，绝不死循环消耗额度
