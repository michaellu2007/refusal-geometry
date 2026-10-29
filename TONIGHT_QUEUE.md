# 今晚队列（2026-10-30 夜间任务专用，全部 CPU 可完成）

> 状态机：`[ ]→[~]→[x]`，失败 2 次标 `!跳过`。每轮取一项，≤20 分钟。
> 完成本文件全部项后，后续轮次静默结束（不写文件），任务次数上限会自动到期。

1. [ ] 深读 Belrose et al. "Refusal in LLMs is an affine function of the residual stream"（LessWrong/OpenReview 搜索全文），更新 lit_review 1.2 为深读版
2. [x] 深读 arXiv 2404.02151（Adaptive Attacks）：模板设计清单 + logprob 随机搜索细节 → lit_review 3.2
3. [ ] 深读 arXiv 2509.15202（DeepRefusal）：概率消融的训练配方 → lit_review 5.1
4. [ ] 深读 arXiv 2610.07023（SSRFT 安全角色内化）→ lit_review 4.4
5. [ ] 深读 arXiv 2609.04482（窄边界对齐，政治说服域）→ lit_review 4.5
6. [ ] 深读 arXiv 2310.00905（XSafety 多语言安全）→ lit_review 4.2
7. [ ] WebFetch https://www.zhipuai.cn 与 https://bigmodel.cn 页脚，找安全/合规联系邮箱；结论写入 docs/zsrc_template.md 路线 B（找不到就如实写"页面未见，需人工"）
8. [ ] 拼装 blog/full_draft.md：TL;DR + 五节合并 + 参考文献表（从 notes/lit_review.md 提取引用条目），结果数字留【】占位
9. [ ] blog/full_draft_en.md：英文镜像骨架（翻译 full_draft 结构，段落级要点即可）

完成后备注：明晚容器到手 → `bash setup_container.sh` → runs/ 结果发回判读。
