# 文献精读队列（定时任务「文献积累」按序取项）

> 状态机：`[ ]` 待做 → `[~]` 进行中（动工前先改状态！）→ `[x]` 完成 → `!跳过`（失败 2 次后）
> 每项 = 一个原子轮次（≤25 分钟）。产出写入 notes/lit_review.md 对应小节（更新该条目的
> "痛点/对我们"两行为全文深读版），并在 PROGRESS.md 追加一行日志。
> 网络降级链见 notes/pain_points.md 末尾。

1. [x] 精读 arXiv 2607.14147（Kwon prefill）：三种因果探针的实现细节与数字；给我们 prefix 族判读标准补充 3 条操作规则 → 已完成（见 lit_review 3.1，含状态转移加分实验设计）
2. [x] 精读 arXiv 2607.00572（HARC）：harm/refusal 两方向各自的提取配方（数据构造！）；校准我们 neutral 对照的做法 → 已完成（见 lit_review 1.7；已落地 8-token 池化 + 模板位待加）
3. [x] 精读 arXiv 2505.17306（PolyRefuse）：确认中文覆盖与话题类别清单；写"定位差异三点"终稿 → 已完成（关键修正：zh 是提取源语言之一；定位收窄为"原生话题类别+话题分解+提示族机制+推理模型"；代码库 mainlp/Multilingual-Refuse）
4. [x] 查证 Wollschläger 概念锥官方代码库链接与 arXiv 号，补进 lit_review 1.3 与代码资产表 → 已完成：arXiv 2502.17420；无官方代码（arXiv 页无链接）；venue 待查证（原"ICML 2025"说法降级）
5. [x] 精读 arXiv 2502.09674（Hidden Dimensions）：次级方向的提取步骤；若 persona 族 dr≈0 的解释预案 → 已完成（安全残差空间 SVD + PLRP 归因；L14-C2 假设叙事/L14-C6 PAIR 选择性消融；触发词删除 40% 鲁棒性；venue 确认 ICML 2025）
6. [x] 精读 arXiv 2512.12066（Instability）：SSI 协议细节；把"5 样本重复"具体化为我们 CLOUD.md 协议条款 → 已完成（SSI=max_c(n_c)/N；greedy 1 样本 98.7% 可靠，关键点 5 样本应配 t≤0.3；judge κ=0.62 且 judge 自身有 0.44-3.61% 噪声；协议写入 CLOUD.md 见仓库 #10）
6b. [ ] HARC 响应位 32-token 池化与 8-token 的 AUC 对比（改 RESP_POOL=32 复跑一次 run_prompt_experiment 即可）
7. [x] 精读 arXiv 2606.25750（RAS）：层窗选择算法；写"模型级分数→prompt 级监控器"的 blog 段落素材到 notes/ → 已完成（层窗 Llama 22-30/Gemma 27-29/Qwen 22-26；g_l 分离度选窗法；快 judge 216.88×；我们层扫描峰值的对照区间已写入 lit_review 6.1）
8. [x] 精读 arXiv 2608.28233（REINS/GUISE）：复杂包装分类学；把与我们 5 提示族的映射表写入 lit_review 2.3 → 已完成（GUISE 900 条三层分类；虚构 36.8%+学术权威 22.5% 验证我们族选型；repo Geralt1020/REINS CC BY 4.0）
9. [x] 精读 arXiv 2610.29555（WRDO）：逐提示方向方差量级；我们余弦矩阵的预期对照值 → 已完成（**论文未量化异质性**——正好是我们的空位；学习权重 vs 均匀平均 0.91 vs 0.002；修复 0.94→≤0.03）
10. [x] 查 SafetyPrompts（2304.10436）数据发布地址/许可证/harmful-benign 成对结构；结论写入 lit_review 4.3 与 README 数据节 → 已完成（**不作数据源**：非成对结构、HF 受限、许可不明；分类学与攻击类型已并入 4.3 对照表）
11. [x] 检索 HarmBench 中文子集与 2024-2026 中文越狱基准新论文，补主题 4 至少 2 条 → 已完成（HarmBench 中文子集未检出公开版；新入池 CSRT 2406.15481 + SearchAttack 2601.04093，均为我们提示族的旁证；lit_review 4.6/4.7）
12. [x] 检索 DeepSeek-R1/推理模型安全性论文（CoT 拒绝、safety reasoning），补主题 3 或 4 至少 2 条 → 已完成（Refusal Cliff 2510.06036/H-CoT 2502.12893/Batch 2608.02681 三条入池 → lit_review 3.8-3.10；R1 逐 token 曲线=REPO_QUEUE #13；文献总量 45）
13. [x] 检索 GLM-4/GLM-4.5 技术报告安全对齐章节要点，写入主题 4 → 已完成（披露极薄：仅 SafetyBench 89.9 分；无红队/拒答策略/数据细节；自曝 bias 77.4 → lit_review 4.8）
14. [x] 检索 CLS（2606.22686）"系统提示对比提取"配方，评估作为我们的对照提取法 → 已完成（三路系统提示 logit 级配方；拓扑判定法=层扫描峰位；反向加固 68.8%→9.4%；→ lit_review 1.6b）
15. [x]  arXiv cs.CL 近 60 天 "refusal" 新论文扫一遍（≥5 条新发现入队或直记） → 已完成（结论：arXiv API 日期排序不尊重查询词、扫描效率低；近 60 天主线已由本轮入池的 2026 新作覆盖：Refusal Cliff/REINS/CLS/RAS/WRDO/GLM-4.5 报告等 8 篇；唯一新捕获 HoS 2610.37657 → 5.12；**文献总量 48 篇**）。建议后续扫描改用 cs.CL 分类过滤而非日期排序
16. [x]  查 Z.ai ZSRC（zcode.z.ai/cn/zsrc）提交字段与范围，把 docs/zsrc_template.md 对齐官方字段 → 已完成（**重大修正**：ZCode ZSRC scope=ZCode 产品非 GLM API；纯违规文本不算漏洞；仅 agent 场景实际安全影响收录 → 模板置顶 Scope 告警 + 路线 A/B/C 修正）
17. [x]  查 6 个代码资产仓库的开源许可证，补全 lit_review 表格"许可证待查"列 → 已完成（GitHub API 一次查全 8 仓库：Apache×3/MIT×2/无许可证×3——无许可仓库只引用不复用）
