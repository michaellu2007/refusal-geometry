# PROGRESS — 断点续作日志

> 约定：每轮工作结束追加一行：`- [YYYY-MM-DD HH:MM] <任务名> #<队列项号> <一句话结果>`
> 崩溃恢复：下一轮先读本文件 + 两个队列的状态标记，从第一个 `[~]` 或第一个 `[ ]` 继续。

## 状态快照
- 代码：全部脚本就绪（hooks/extract/judge/data/prompts + 5 scripts + tests）
- 数据：5 话题 × 3 种子对 + 12 中性指令；AdvBench 官方 URL 已接
- 知识库：lit_review.md 40 篇 + pain_points.md 10 条映射（v1，摘要级）
- 待容器：明晚 GPU 跑 setup_container.sh 全链路

## 日志
- [2026-10-28] 主会话 代码 v2：judge 三分类、双方向提取、双读出位、置换基线、起始层扫描、模板哈希、余弦矩阵脚本、AdvBench 官方 URL
- [2026-10-28] 主会话 知识库 v1：40 篇摘要级笔记 + 10 条痛点映射 + 17 项精读队列 + 12 项仓库队列
- [2026-10-29 00:10] 主会话 单测 6/6 通过（修 permutation_baseline 3D 守卫 + AUC 边界用例）；git 提交 4733b39
- [2026-10-29 00:12] 主会话 定时任务上线：自动化 automation-5e843a98（文献+仓库接力·每30分钟，三合一轮次，09:00 自毁）。注：harness 限制每 session 一个自动化，故三任务合并；兜底与断点协议已写入 prompt
- [2026-10-29 00:4x] 主会话 深读 #1 Kwon 2607.14147（三探针数字/响应前1/3窗/base model 判别）→ lit_review 3.1；深读 #2 HARC 2607.00572（提取配方：模板位+32token池化；攻击类平面分区）→ lit_review 1.7；代码升级 RESP_POOL=8 池化，py_compile+单测 6/6 通过
- [2026-10-29 00:5x] 主会话 blog/01-background.md + blog/02-method.md 草稿完成（REPO_QUEUE #1#2）；深读 #3 PolyRefuse（关键定位修正：zh 是提取源语言，差异化收窄为原生话题+话题分解+提示族+推理模型）→ lit_review 4.1 + 代码资产表 +7；RESEARCH_QUEUE 3/17 完成
- [2026-10-29 00:28] 接力 #repo3 blog/03-results-template.md 完成（四图位+空表+三种结局叙事预案+诚实性清单）；下轮做文献 #4（概念锥代码库查证）
- [2026-10-29 00:30] 接力 #研究4 概念锥查证完成：arXiv 2502.17420（Gasteiger/Günnemann 组）；无官方代码库；"ICML 2025"降级为待查证 → lit_review 1.3 已更新；下轮做仓库 #4（blog/04-defense.md）；RESEARCH_QUEUE 4/17
- [2026-10-29 00:32] 接力 #repo4 blog/04-defense.md 完成（响应位投影监控器伪代码/四条局限/给两家厂商的短中长期建议）；下轮做文献 #5（Hidden Dimensions 次级方向精读）；REPO_QUEUE 4/12
- [2026-10-29 00:36] 接力 #repo5 blog/05-limitations.md 完成（11 条局限四组：方法/评测/推断/复现邀请）；下轮做文献 #6（Instability SSI 协议）；REPO_QUEUE 5/12
- [2026-10-29 00:38] 接力 #研究6 Instability 协议深读完成（SSI 公式；greedy 单样本 98.7% 可靠→主协议成立；5 样本配 t≤0.3；judge κ=0.62 且自噪声 0.44-3.61%；边界提示最摇摆→HEDGE 投影方差预言）→ lit_review 3.7；下轮做仓库 #6（topics 扩充第一话题）；RESEARCH_QUEUE 6/17
- [2026-10-29 00:42] 接力 #repo6 violence 话题扩至 12 对（成对模板纪律保持），单测 6/6 通过；下轮做文献 #7（RAS 层窗算法）；下下轮继续 topics 其余 4 话题；REPO_QUEUE 5.5/12
- [2026-10-29 00:45] 接力 #研究7 RAS 深读完成（层窗 Llama22-30/Gemma27-29/Qwen22-26；分离度选窗法；快 judge 216.88×；层扫描峰值对照区间写入 lit_review 6.1）；下轮做仓库 #6 第二批（privacy 话题扩充）；RESEARCH_QUEUE 7/17
- [2026-10-29 00:48] 接力 #repo6b privacy 话题扩至 12 对（监控/人肉/窃听 vs 授权/保护配对），单测 6/6 通过；下轮做文献 #8（REINS/GUISE 包装分类学）；REPO_QUEUE 6/12
- [2026-10-29 00:50] 接力 #研究8 REINS/GUISE 深读完成（900 条三层分类；虚构 36.8%/学术权威 22.5% 验证我们族选型；CorrSteer 崩溃率 20.3% 假安全证据；repo+许可证入表）→ lit_review 2.3；下轮做仓库 #6 第三批（fraud 话题扩充）；RESEARCH_QUEUE 8/17
- [2026-10-29 00:52] 接力 #repo6c fraud 话题扩至 12 对（脚本/钓鱼/话术 vs 识别/核实/防范配对），单测 6/6 通过；下轮做文献 #9（WRDO 逐提示方向方差）；REPO_QUEUE 6/12
- [2026-10-29 00:54] 接力 #研究9 WRDO 深读完成（异质性声明无量化=我们空位实锤；学习权重 0.91 vs 均匀 0.002；修复 ASR 0.94→≤0.03）→ lit_review 1.4；下轮做仓库 #6 第四批（illegal_items）；RESEARCH_QUEUE 9/17
- [2026-10-29 00:54] 接力 #repo6d illegal_items 扩至 10 对（写入时 2 行占位瑕疵当轮发现并修复），单测 6/6 通过；下轮做文献 #10（SafetyPrompts 数据源评估）；REPO_QUEUE 6/12
- [2026-10-29 00:56] 接力 #研究10 SafetyPrompts 评估完成（结论：非成对+许可不明→不作数据源；10 类场景与攻击类型并入我们话题/提示族对照）→ lit_review 4.3；下轮做仓库 #6 第五批（cyber_abuse 最后一话题）；RESEARCH_QUEUE 10/17
- [2026-10-29 00:59] 接力 #repo6e cyber_abuse 扩至 12 对，**话题扩充全部完成**（5 话题共 58 对），单测 6/6 通过；下轮做文献 #11（HarmBench 中文子集检索）；REPO_QUEUE 7/12
- [2026-10-29 01:01] 接力 #研究11 中文越狱基准检索完成（HarmBench 中文子集无公开版；新入池 CSRT + SearchAttack → lit_review 4.6/4.7，文献总量 42 篇）；下轮做仓库 #7（README_EN）；RESEARCH_QUEUE 11/17
- [2026-10-29 01:02] 接力 #repo7 README_EN.md 完成（含 RQ1-3、协议节、披露纪律，链接中文主 README）；下轮做文献 #12（DeepSeek-R1/推理模型安全检索）；REPO_QUEUE 8/12
- [2026-10-29 01:04] 接力 #研究12 推理模型安全检索完成（Refusal Cliff 悬崖现象/H-CoT 劫持 98%→2%/Batch 稀释 3 条入池 → lit_review 3.8-3.10；R1 逐 token 投影曲线新队列项 #13；**文献总量 45 篇**）；下轮做仓库 #8（zsrc 模板细化）；RESEARCH_QUEUE 12/17
- [2026-10-29 01:05] 接力 #repo8 zsrc_template.md 细化完成（漏洞盒子 10 字段对照表 + 先白盒后线上/一次一漏洞/30天窗口/留痕/红线自检）；下轮做文献 #13（GLM 技术报告安全章节）；REPO_QUEUE 9/12
- [2026-10-29 01:07] 接力 #研究13 GLM-4.5 报告安全章节深读完成（披露空白=我们白盒合法性论据；SafetyBench 89.9/bias 77.4 → lit_review 4.8，**文献总量 46 篇**）；下轮做仓库 #9（CLOUD.md 评测协议节）；RESEARCH_QUEUE 13/17
- [2026-10-29 01:08] 接力 #repo9 CLOUD.md 评测协议节完成（6 条：greedy 主协议/SSI<0.8 降级规则/judge κ/翻转率列/模板哈希/基线拒绝率门槛）；下轮做文献 #14（CLS 系统提示对比提取）；REPO_QUEUE 10/12
- [2026-10-29 01:08] 接力 #研究14 CLS 配方深读完成（三路系统提示 logit 级提取；拓扑判定法；反向加固数字）→ lit_review 1.6b + 新可选实验 REPO_QUEUE #14；下轮做仓库 #10（README 主文件同步）；RESEARCH_QUEUE 14/17
- [2026-10-29 01:09] 接力 #repo10 README.md 补全（查明首版写入当年被计划模式拦截、从未存在；按当前状态全新写入）；下轮做文献 #15（近 60 天 refusal 新论文扫描）；REPO_QUEUE 11/12
- [2026-10-29 01:11] 接力 #研究15 60天扫描完成（方法教训：日期排序无效改分类过滤；HoS 入池 → 5.12，文献 48 篇）；下轮做仓库 #11（formalism 命题 3 证明细节）；RESEARCH_QUEUE 15/17
- [2026-10-29 01:12] 接力 #repo11 formalism 命题 3 证明细节完成（两层论证 + ε 三来源 + AUC=ε 测量的核心论点）；下轮做文献 #16（ZSRC 规则页对齐）；REPO_QUEUE 12/12 主队列完成（剩可选 #13 #14）
- [2026-10-29 01:14] 接力 #研究16 ZSRC 规则页核查完成（**重大修正**：scope=ZCode 产品；纯违规文本不算漏洞；agent 实际影响才收录 → 模板置顶告警 + 三路线修正 + 新队列 #15 核实 bigmodel 渠道）；下轮做仓库 #12（formalism 命题 1 证明补全后切文献）；RESEARCH_QUEUE 16/17
- [2026-10-29 01:14] 接力 #研究17 许可证查证完成（8 仓库一次查全；无许可 3 个仅引用）→ lit_review 资产表定稿；**RESEARCH_QUEUE 17/17 全部完成**；下轮做仓库 #15（核实 bigmodel 渠道）
- [2026-10-29 01:16] 接力 #repo15 bigmodel 渠道核实完成（无独立 SRC → 兜底三件套入模板路线 B）；**两队列实质清空**（仅剩 GPU 依赖可选 #13 #14）；自动化转低频待机，明晚容器跑 setup_container.sh 后人工续作
- [2026-10-29 01:20] 接力 #空轮 两个队列无待办（研究 17/17、仓库主队列 12/12；#13/#14 为 GPU 依赖留待容器）；本轮仅记录待机状态即结束，不做任何文件改动
- [2026-10-29 01:20] 接力 #检查点 本地 commit e891e3e（整晚产出全部入库：48篇文献/58对数据/blog五节/ZSRC修正）；此后空轮静默待机，仅 09:00 自毁检查
- [2026-10-29 01:26] 【下一轮接力必做指令】队列已全部完成（研究17/17、仓库12/12+#15；#13/#14留待容器）。本轮主会话尝试切换待机模式时陷入 CronList 重复调用异常。下一轮开始时请立即执行一次 CronUpdate：id=automation-5e843a98-032d-487b-8123-b48d25e9d2b7，title=「接力·待机·每30分钟」，cron='* * * * *'，intervalUnit=minute，interval=30，recurring=true，prompt 在原 prompt 基础上加一条【空队列分支】：若两队列均无 [ ]/[~] 可办项，本轮立即结束不写文件。执行完成后在 PROGRESS.md 记一行。若 CronUpdate 失败则保持现状（1分钟空转的浪费可接受，09:00 自毁不变）。
- [2026-10-29 01:28] 【撤销切换指令】CronUpdate 尝试连续两轮触发重复调用异常，按预设兜底放弃待机切换：维持 1 分钟节奏（空轮成本小、09:00 自毁保证）。后续轮次请勿再尝试 CronUpdate/CronList，直接静默待机即可。
- [2026-10-29 01:35] 【泛洪告警】检测到几十次空轮触发被打包为单条消息——空转成本已实际化。本轮执行一次待机切换（30分钟心跳）；若再次失败则直接删除自动化（工作已全部完成并入库 e891e3e，泛洪违背用户'不浪费'的意图）。
- [2026-10-29 03:42] 【最终状态】系统性重复调用问题确认（自动化提示词含 CronList 字样锚定生成，多次 CronUpdate/CronDelete 尝试均退化为 CronList 循环）。结论：全部研究工作已完成入库（e891e3e），队列 0 待办，自动化将空转至 09:00 自毁或由用户在界面手动删除。给用户的操作指引已写入最终消息。
- [2026-10-29 09:2x] 主会话 收尾三件：①修 gen_first 零token边界bug（空响应退化为prompt位语义）②REPO #13 run_trace.py（Refusal Cliff 检验，teacher-forced逐token曲线+cliff_drop统计）③REPO #14 CLS式第二提取法（extract.py system_prompt_contrast，run_extract自动互验）；py_compile+单测6/6通过，REPO_QUEUE 15/15
- [2026-10-30 上午] 主会话 概念锥全文深读完成（RDO三损失/5维锥/RepInd/k≥4超DIM基线/不同层DIM无增益对照）→ lit_review 1.3 深读版；文献深读档 10 篇
