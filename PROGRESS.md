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
