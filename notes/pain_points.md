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

---

# v2 增补（2026-11-04，基于深读 26 篇 + 两轮 GPU 实验）
> 纯追加，v1 十行表与上方协议未动。备份：pain_points.backup_2026-11-04.md

## A. 论文 bug 清单（深读发现的学术缺陷 → 我们的改进机会）

| 论文 | bug / 缺陷 | 我们的改进机会 |
|---|---|---|
| Over-Refusal Subspaces 2603.27518 | **过度声明**："过拒高维子空间"在 3 模型中 2 个不成立（Qwen/Gemma 单方向覆盖 74.6%/67.3%）；主实验过拒仅 48 条、n80 无良性对照；有害消融残 20% 全文未解释 | 我们报覆盖率/n80 前先自测模型相关性，单模型结论不作普适声明——GLM 数据按此纪律报 |
| Rational 2503.05021 | 摘要 "0/135" 与表 1 非零格（至 0.015）矛盾；**缺"等量无 rationale"SFT 对照**——"推理内容起效"未被隔离；判官偏连贯性：Circuit Breaker 乱码被判不安全="更安全"部分是伪影 | 采纳其良性等量消融为模板；引其数字时注"判官伪影"风险——我们 judge κ 一致性协议正好是补丁 |
| Health-ORSC 2601.17642 | Hard-1K 按"≥10/30 模型拒绝"**反选循环**——81.1% 过拒是选择的峰值不是总体的；金标靠模型集成（人评 Fleiss' κ≈0）；关键词匹配无 HEDGE 档 | 引用必须注"Hard 档峰值≠全量"；我们三分类 judge 已解决 HEDGE 档；人评 κ≈0 反证"方向泛化而非内容判断"解释 |
| SafeSteer 2506.04250 | "无需配对"名不副实——最强结果实靠 GPT-4 同题配对+拒绝标签筛选回收信噪比；**类别向量相似度零测量**；通用 Alpaca 向量反超类别特定=核心主张自弱 | 我们成对 diff-in-means 免疫话题混淆 + 0.886 余弦矩阵直接补其空位；其失败是我们的方法论反证 |
| MSFT SAE Steering 2411.11296 | 纠缠只有定性结论、无定量分解 | 我们"注入 100× 不伤通用能力"= diff-in-means vs SAE 特征纯度的现成定量对比 |
| SELFDEFEND 2402.15727 | vision paper 无大规模定量、影子栈延迟成本未测 | 我们输出侧投影监控器 = 1 次点积 + 可量化 AUC，正好补其定量半边 |
| Gradient Cuff 2403.00867 | 110 次生成+嵌入扰动，零阶梯度 4096 维需 P=10 方向近似 | 110 次查询 vs 1 次点积——成本对比是 blog 防御节核心数字 |
| Latent Jailbreak 2307.08487 | 纯行为层、无表征分析 | 我们给出 GLM 两代几何对照（ChatGLM2 75.3% → GLM-4-9B encoding 30%）|
| refusal SAE 2505.23556 | 仅 2 模型、仅英文、未按话题分解 F_H | "中文 + 分话题 F_H 分解"是直给的 follow-up 空位 |
| A-MESS 2607.17152 | AttackSHAP 预设"攻击选择会反哺防御再训练"——对静态评测/无再训练流程不适用 | 引用时限定语境；我们 5 族排序≠防守价值排序的论点保留 |

## B. 我们管线 bug 复盘（全部已修复，教训入协议）

| bug | 根因 | 教训 |
|---|---|---|
| CPU 复现 5 连（BatchEncoding×4 处/变长 stack/assert 过严/dtype·tuple/json 写入） | smoke test 用假张量，真数据才暴露 | 接真模型前先跑 1 条真数据端到端 |
| gen_first 零 token 边界：空响应误用 | 边界未守卫 | 生成类函数必须守空输出分支 |
| GPU 环境 7 坑（根分区满/cu132→cu124/transformers5→4.46/GLM 层路径/tiktoken/pad_token_id/nohup 被杀） | 容器裸装、版本漂移 | 版本全部固化进 setup_container.sh + MODELS.lock.json |
| judge κ 除零 rc=1：think=False 未生效→思考段占满 num_predict=64→290 条全 UNKNOWN | 思考型模型判官未显式关思考 | valid 空时 κ=None + 预算给足；判官必须冒烟 2 条再全量 |
| Ollama 思考型 num_predict 过小→正文为空被判 COMPLY | 同上（27B abliterated 实验） | 同上 |
| stage4 重复拉起→CPU offload 卡死 30min | 上一会话重复拉起无单例守卫 | 后台任务用 CHAIN_DONE 哨兵 + 查活再拉起 |
| illegal_items 10 对占位瑕疵 | 扩充脚本写入时序 | 写入后立即读回校验（当轮已修） |
| L38 产物缺失致 S3/S5/S7 判空 | 服务器失联、产物未取回 | 本地 results/ROUND2/ 双备份 + 每阶段落盘即取回 |

## C. 新分析方法清单（深读提取，标状态）

| 方法 | 来源 | 状态 |
|---|---|---|
| n80 解释方差谱 + 单方向覆盖率 | OR-Subspaces 1.10 | **待跑**——纯线性代数，GLM 现有方向集即可算，检验"拒绝锥"维数；GLM 需先自测再下结论 |
| 框架不变探针（多框架同义表述联合拟合差分） | **本项目原创**（11-02 决定性实验） | 已完成——d_std 塌到 −0.1 而 d_inv 保持 +28.7 |
| SSI 翻转率协议（t≤0.3×5 样本 + judge κ 入报告） | Instability 3.7 | 已采纳（CLOUD.md 协议节） |
| ACE 仿射阈值 τ̂=⟨r̂, μ_benign⟩ | ACE 1.2 | 已采纳（formalism 命题 2） |
| RAS 稳定层窗选层（g_l 分离度+稳定性连续窗口） | RAS 6.1 | 已采纳（层扫描解读模板：GLM 预期 L25-35） |
| 状态转移向量：消融 v_ref 强制续写→前 8 token 均值→注入 | Kwon 3.1 探针② + HARC 响应侧配方 | 加分实验（REPO_QUEUE #13 延伸） |
| 逐 token 投影曲线（思维链内→输出前，悬崖形态） | Refusal Cliff 3.8 | REPO_QUEUE #13 已排（R1-Distill 对照） |
| 等数据量消融（良性侧 vs 全量，分离"内容 vs 数据量"贡献） | Rational 5.9 | 消融设计模板，主实验收尾后可用 |
| 意图×有用性双轴 SCR 判分 | Health-ORSC 5.10 | HEDGE 细分"有/无实质内容"两档——judge 升级候选 |
| PLRP token→方向归因 | Hidden Dimensions 1.5 | future work 一句（方向→token 归因升级路线） |
| CosSim+AP 混合特征筛选 | refusal SAE 2.1 | SAE 分支 future work |
| 范数中位数剪枝提取 | SafeSteer 2.5 | 提取变体对照——预期比成对法差，作我们方法论的反证实验 |
