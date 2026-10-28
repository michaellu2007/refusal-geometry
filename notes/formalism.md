# 数学骨架：把"提示词使拒绝向量失效"定理化

目标：blog 不只报告实验，而是给出 3 个命题 + 证明 + 实验检验。这是从"越狱 blog"升级到"可解释性 mini-paper"的关键。

## 记号

- $x \in \mathbb{R}^d$：第 $\ell$ 层残差流在 prompt 末 token 的激活向量
- $r$：拒绝方向（diff-in-means 提取），$\hat r = r/\|r\|$
- $z(x) = \langle x, \hat r \rangle$：投影分数

## 命题 1（提取方向的等价性）

**命题**：设 harmful / benign 激活分别服从 $\mathcal{N}(\mu_h, \Sigma)$、$\mathcal{N}(\mu_b, \Sigma)$（共享协方差）。则 diff-in-means 方向 $\mu_h - \mu_b$ 平行于 Fisher 线性判别分析（LDA）方向 $\Sigma^{-1}(\mu_h - \mu_b)$ 当且仅当 $\Sigma$ 的特征分解在 $(\mu_h-\mu_b)$ 上可交换（特别地，$\Sigma = \sigma^2 I$ 时平凡成立；$\Sigma$ 与单位向量 $u$ 的任意旋转对称亦成立）。

**证明思路**：$\Sigma = Q\Lambda Q^\top$，取 $v = \mu_h - \mu_b$，则 $\Sigma^{-1}v = Q\Lambda^{-1}Q^\top v$。$\Sigma^{-1}v \parallel v \iff Q^\top v$ 是 $\Lambda^{-1}$ 的特征向量组合中仅一个方向非零，即 $v$ 落在 $\Sigma$ 的某特征子空间。∎

**实验角色**：层扫描分数（pooled Cohen's d）就是检验"该层激活是否近似满足此条件"。高分层 = 单方向假设成立的位置。

## 命题 2（拒绝的半空间判决模型）

**命题**：若存在阈值 $\tau$ 使模型拒绝当且仅当 $z(x) > \tau$（半空间判决），则

1. 方向消融（$x \mapsto x - z(x)\hat r$）后所有样本 $z=0$，若 $\tau > 0$ 则拒绝率降为 0；
2. 方向注入（$x \mapsto x + \alpha \hat r$）使 $z$ 平移 $\alpha$，存在 $\alpha_c = \tau - \min_b z(b)$ 使全部良性样本被拒。

**证明**：投影消融后 $z(x - z\hat r) = z(x) - z = 0$；注入后 $z(x+\alpha\hat r) = z(x)+\alpha$。∎

**实验角色**：validate.json 的两个拒绝率就是对该模型的定量检验（消融后残存拒绝率 = 半空间模型误差率）。

## 命题 3（提示词 = 激活空间中的平移向量；核心）

**命题**：设提示改写 $f$（模板拼接，不改变权重）诱导第 $\ell$ 层激活映射 $x \mapsto x + \delta_f(x)$（残差网络中任何 prompt 改写都是输入 token 序列的改变，其效果由后续 transformer 层逐层线性叠加残差构成，故可写成仿射摄动）。定义 $\Delta z = \langle \delta_f(x), \hat r\rangle$。则：

$$P(\text{越狱成功} \mid f, x) = \mathbb{1}\left[z(x) + \Delta z < \tau\right] + \varepsilon$$

其中 $\varepsilon$ 为半空间模型之外的非线性残差。**推论**：$-\Delta z$ 是"越狱成功"的单调预测子，其判别力由 AUC 度量；AUC 显著 > 0.5 ⟺ "提示词使拒绝向量失效"的机制确实是通过把表示平移出拒绝半空间（几何失效），而非绕过该方向（表达抑制，$\varepsilon$ 主导）。

**这是研究问题 3 的可判定形式**：两种机制在行为层不可区分，只有投影分析能把它们分开。

## 话题分解（研究问题 2）

分话题提取 $r_t$，构造余弦矩阵 $C_{ij} = \cos(r_i, r_j)$。Wollschläger et al. 2025 的"拒绝锥"预测 $C_{ij} \approx 1$（共享锥内）；若中文话题出现 $C_{ij} \ll 1$ 的块结构，则是新的可发表发现：**中文安全对齐的拒绝几何是多方向的**。

## 相关理论工作（写 blog 时引用）

- Belrose et al. 2024, *Refusal in LLMs is an affine function of the residual stream*（仿射结构的形式化）
- Wollschläger et al. 2025, *The Geometry of Refusal*（拒绝锥、各向异性）
- *Refusal Direction is Universal Across Safety-Aligned Models*（跨模型方向迁移）
- Marks & Tegmark, *The Geometry of Truth*（线性表示几何的一般方法论）

## 与模型规模的关系（回应"只能小模型吗"）

方法与结论形式对任意规模成立（Arditi 验证到 72B）。规模档位：
1. 1.5B（本地调试）→ 7-9B（主实验，GLM-4-9B-Chat + R1-Distill-7B）→ 
2. GLM-4.5-Air 106B FP8（租 1×H800/H20，验证规模不变性，blog 说服力+1 档）
3. 更大规模只增加成本不改变方法；"规模 × 拒绝几何稳定性"本身可做成第二张图
