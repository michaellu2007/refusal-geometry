# 仓库完善队列（定时任务「仓库完善」按序取项）

> 状态机同 RESEARCH_QUEUE.md：`[ ]→[~]→[x]`，失败 2 次标 `!跳过`。
> 依据：notes/lit_review.md + notes/formalism.md + notes/pain_points.md。
> 改 python 代码后必须跑 `python tests/test_all.py` 验证。
> **禁止删除整个目录或批量删文件；只允许新建/修改单个文件。**

1. [ ] blog/01-background.md：三篇奠基综述（Arditi/概念锥/HARC）+ 中文缺口论证（引 lit_review 主题 4）
2. [ ] blog/02-method.md：成对差分均值图解 + formalism 命题 1-2 + 置换基线说明
3. [ ] blog/03-results-template.md：结果节骨架（层扫描热图/余弦矩阵/双 AUC/平面图四图位 + 空表 + 两种结局的写法预案）
4. [ ] blog/04-defense.md：prompt 级投影监控器设计（引 RAS/Gradient Cuff/Kwon 响应位监控）
5. [ ] blog/05-limitations.md：单轮局限（引 GCAD KV-cache）、judge 偏差、模板敏感性（引 BioRefusalAudit）
6. [ ] topics_zh.yaml 每话题扩到 10-15 对（保持模板化与成对纪律，逐话题分次做）
7. [ ] tests/test_all.py 补：classify_response 三分类边界用例 + permutation_baseline 合成用例
8. [ ] README_EN.md：英文镜像 README
9. [ ] docs/zsrc_template.md 细化：漏洞盒子常见字段（标题/等级/复现步骤/影响范围/修复建议）逐节模板
10. [ ] CLOUD.md 补"评测协议"节：温度=0、关键点 5 样本、翻转率记录（引 2512.12066）
11. [ ] README.md 同步：run_cosine_matrix.py / tests / setup_container.sh 的说明补齐
12. [ ] notes/formalism.md 补命题 3 的证明细节段（仿射摄动的两层论证）
