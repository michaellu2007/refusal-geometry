# 文献精读队列（定时任务「文献积累」按序取项）

> 状态机：`[ ]` 待做 → `[~]` 进行中（动工前先改状态！）→ `[x]` 完成 → `!跳过`（失败 2 次后）
> 每项 = 一个原子轮次（≤25 分钟）。产出写入 notes/lit_review.md 对应小节（更新该条目的
> "痛点/对我们"两行为全文深读版），并在 PROGRESS.md 追加一行日志。
> 网络降级链见 notes/pain_points.md 末尾。

1. [ ] 精读 arXiv 2607.14147（Kwon prefill）：三种因果探针的实现细节与数字；给我们 prefix 族判读标准补充 3 条操作规则
2. [ ] 精读 arXiv 2607.00572（HARC）：harm/refusal 两方向各自的提取配方（数据构造！）；校准我们 neutral 对照的做法
3. [ ] 精读 arXiv 2505.17306（PolyRefuse）：确认中文覆盖与话题类别清单；写"定位差异三点"终稿
4. [ ] 查证 Wollschläger 概念锥（ICML 2025）官方代码库链接与 arXiv 号，补进 lit_review 1.3 与代码资产表
5. [ ] 精读 arXiv 2502.09674（Hidden Dimensions）：次级方向的提取步骤；若 persona 族 dr≈0 的解释预案
6. [ ] 精读 arXiv 2512.12066（Instability）：SSI 协议细节；把"5 样本重复"具体化为我们 CLOUD.md 协议条款
7. [ ] 精读 arXiv 2606.25750（RAS）：层窗选择算法；写"模型级分数→prompt 级监控器"的 blog 段落素材到 notes/
8. [ ] 精读 arXiv 2608.28233（REINS/GUISE）：复杂包装分类学；把与我们 5 提示族的映射表写入 lit_review 2.3
9. [ ] 精读 arXiv 2610.29555（WRDO）：逐提示方向方差量级；我们余弦矩阵的预期对照值
10. [ ] 查 SafetyPrompts（2304.10436）数据发布地址/许可证/harmful-benign 成对结构；结论写入 lit_review 4.3 与 README 数据节
11. [ ] 检索 HarmBench 中文子集与 2024-2026 中文越狱基准新论文，补主题 4 至少 2 条
12. [ ] 检索 DeepSeek-R1/推理模型安全性论文（CoT 拒绝、safety reasoning），补主题 3 或 4 至少 2 条
13. [ ] 检索 GLM-4/GLM-4.5 技术报告安全对齐章节要点，写入主题 4
14. [ ] 检索 CLS（2606.22686）"系统提示对比提取"配方，评估作为我们的对照提取法（进阶实验设计 1 段）
15. [ ] arXiv cs.CL 近 60 天 "refusal" 新论文扫一遍（≥5 条新发现入队或直记）
16. [ ] 查 Z.ai ZSRC（zcode.z.ai/cn/zsrc）提交字段与范围，把 docs/zsrc_template.md 对齐官方字段
17. [ ] 查 6 个代码资产仓库的开源许可证，补全 lit_review 表格"许可证待查"列
