# 仓库完善队列（定时任务「仓库完善」按序取项）

> 状态机同 RESEARCH_QUEUE.md：`[ ]→[~]→[x]`，失败 2 次标 `!跳过`。
> 依据：notes/lit_review.md + notes/formalism.md + notes/pain_points.md。
> 改 python 代码后必须跑 `python tests/test_all.py` 验证。
> **禁止删除整个目录或批量删文件；只允许新建/修改单个文件。**

1. [x] blog/01-background.md：三篇奠基综述（Arditi/概念锥/HARC）+ 中文缺口论证（引 lit_review 主题 4）
2. [x] blog/02-method.md：成对差分均值图解 + formalism 命题 1-2 + 置换基线说明
3. [x] blog/03-results-template.md：结果节骨架（层扫描热图/余弦矩阵/双 AUC/平面图四图位 + 空表 + 两种结局的写法预案）
4. [x] blog/04-defense.md：prompt 级投影监控器设计（引 RAS/Gradient Cuff/Kwon 响应位监控）
5. [x] blog/05-limitations.md：单轮局限（引 GCAD KV-cache）、judge 偏差、模板敏感性（引 BioRefusalAudit）
6. [x] topics_zh.yaml 每话题扩到 10-15 对（保持模板化与成对纪律，逐话题分次做）→ **全部完成**：violence/privacy/fraud 各 12 对、illegal_items 10 对、cyber_abuse 12 对，共 58 对
7. [ ] tests/test_all.py 补：classify_response 三分类边界用例 + permutation_baseline 合成用例
8. [x] README_EN.md：英文镜像 README
9. [x] docs/zsrc_template.md 细化：漏洞盒子常见字段（标题/等级/复现步骤/影响范围/修复建议）逐节模板 → 已完成（含字段对照表 + 提交节奏与红线自检 5 条）
10. [x] CLOUD.md 补"评测协议"节 → 已完成（greedy 主协议 + SSI 复核 + judge κ + 翻转率列 + 模板哈希 + 基线拒绝率门槛 6 条）
11. [x] README.md 同步 → 已完成（**发现原 README 从未写入成功——首轮创建时被计划模式拦截，本轮补全**：目录/快速开始/协议摘要/发布纪律全为当前状态）
12. [x] notes/formalism.md 补命题 3 证明细节 → 已完成（单步仿射性一阶论证/Δz 逐样本分布解释/ε 项三来源与 AUC 的关系/与 HARC 分类的衔接）
13. [ ]（GPU 依赖·留待明晚容器）R1 对照组升级：run_prompt_experiment.py 加"逐 token 投影曲线"模式（思维链内逐步记录 refusal 方向投影，检验 Refusal Cliff 2510.06036 在 R1-Distill 上的存在性）
14. [ ]（GPU 依赖·留待明晚容器）可选实验：run_extract.py 加"系统提示对比"第二提取法（CLS 式三路前向），与成对指令法提取的方向算余弦互验
15. [x] 核实 bigmodel 渠道 → 已完成（无独立 SRC/公开邮箱；兜底三件套写入模板路线 B）
