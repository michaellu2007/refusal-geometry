# 今晚队列（2026-10-30 夜间任务专用，全部 CPU 可完成）

> 状态机：`[ ]→[~]→[x]`，失败 2 次标 `!跳过`。每轮取一项，≤20 分钟。
> 完成本文件全部项后，后续轮次静默结束（不写文件），任务次数上限会自动到期。

1. [x] 深读 ACE（arXiv 2411.09003，Marshall/Scherlis/Belrose——署名已修正）→ lit_review 1.2 深读版 + formalism 命题2 加 ACE 阈值校准注记
2. [x] 深读 arXiv 2404.02151（Adaptive Attacks）：模板设计清单 + logprob 随机搜索细节 → lit_review 3.2
3. [x] 深读 arXiv 2509.15202（DeepRefusal）→ lit_review 5.1 深读版（PAA 配方/LoRA 45分钟/ASR-95%/前缀增强必要性）
4. [x] 深读 arXiv 2610.07023（SSRFT）→ lit_review 4.4 深读版（SRQA 构造/JRS-RPS 分解/prefilling 增幅减半/过拒改善/单卡可训）
5. [x] 深读 arXiv 2609.04482（窄边界对齐）→ lit_review 4.5 深读版（边界对=我们成对设计的独立收敛/SC2 自生成回答降过拒/FakeHarm 18 类语义）
6. [x] 深读 arXiv 2310.00905（XSafety）→ lit_review 4.2 深读版（中文不安全率 8.1% vs 英 1.0%/语料谱系修正：中文侧源自 SafetyPrompts 原文/think-in-English 技巧）
7. [x] 官网页脚核查 → zsrc_template 路线 B 已更新（zhipuai.cn 无安全专用邮箱、漏洞导向 ZSRC；bigmodel.cn JS 页面需人工核查；实用告知链三条）
8. [x] 拼装 blog/full_draft.md：TL;DR + 五节合并 + 参考文献表（从 notes/lit_review.md 提取引用条目），结果数字留【】占位
9. [x] blog/full_draft_en.md：英文镜像骨架（翻译 full_draft 结构，段落级要点即可）

完成后备注：明晚容器到手 → `bash setup_container.sh` → runs/ 结果发回判读。
