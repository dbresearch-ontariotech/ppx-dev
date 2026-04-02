- thesis
  - what neural network architectures are used for paddleocr?
  - have a formal data modeling of the output of paddleocr.
    - text segment and word identification
    - layout analysis
  - our framework:
    - visual tokens (VT) (produced by paddleocr), hierarchical organization
    - text tokens (TT) (produced by markdown extraction)
  - alignment problem:
    - define the alignment function as: visual tokens to source spans
    - constraints:
      - alignment must respect reading order, and parent-child relation in layout tree
    - quality of alignment: scoring function based total similarity between VT and TT.
    - algorithms:
      - DP formulation: O(nL^2) where n = |VT|, L = |TT|.  Guarantees optimal solution.
      - GREEDY: O(nL)
      - Hybrid: if L < c, use DP, else use GREEDY.
    - future work:
      - evaluation



# Thesis plan

## Abstract
## 1. Introduction

- What is the problem we are trying to solve? Why is it a problem? Where is the gap in knowledge? Who has worked on this problem? When did this problem surface? How do we propose to solve it? What technologies will we use to solve it?

## 2. Overview of PaddlePaddle (PaddleOCR V3 and PPDocLayout v3)

- What neural network architectures are used for paddleocr?
- Formal data modeling output of paddleocr
- Text, segment, and word identification
- Layout analysis

## 3. Proposed Framework

- Define the framework. Data structures and pipeline.
- Visual Tokens (VT) (produced by paddleocr), hierarchical organization
- Text Tokens (TT) (produced by markdown extraction)
- Layout Tree

## 4. Alignment Problem
- Formal definition
    - Define the alignment function as: Visual Tokens (VT) to Text Token (TT) source spans
- Constraints:
    - Alignment must respect reading order, and parent-child relation in layout tree
- Quality of alignment: scoring function based total similarity between VT and TT.
- Algorithms:
    - DP formulation: O(nL^2) where n = |VT|, L = |TT|.  Guarantees optimal solution.
    - GREEDY: O(nL)
    - Hybrid: if L < c, use DP, else use GREEDY.
## 5. Future Work
- Evaluation

## 6. Conclusion


## 7. References

Begin collecting a list of papers here:

- PubLayNet
    - https://arxiv.org/pdf/1908.07836
- DocLayNet
    - https://arxiv.org/pdf/2206.01062
- PaddleOCR v3 Technical Report
    - https://arxiv.org/pdf/2507.05595
    - Initial PaddleOCR paper - https://arxiv.org/pdf/2009.09941
- READoc
    - https://arxiv.org/pdf/2409.05137
- PP-DocLayout
    - https://arxiv.org/pdf/2503.17213
- PaddlePaddle 
    - PaddlePaddle: An Open-Source Deep Learning Platform from Industrial Practice
    - **Not available in english**: http://www.jfdc.cnic.cn/EN/abstract/abstract2.shtml



# Writing notes

Let's begin by writing some notes on a particular section. For instance, what is the architecture of our proposed framework?

## Preprocessing

- PaddleOCR: We use PaddlePaddle's PPOCRv5 to turn an image in R^HxWx3 space for text detection and recognition. The two models used are `paddleocrv5det` and `paddleocrv5-rec`.
  - Gives Visual Token Layers (lines + words)
- Use PPStructureV3 for full layout analysis. (citation)
  - Gives structured/semantic layout.
  - Layout Layers (regions, blocks, lines, words)

## Data Structures

  - Visual Tokens (VT) are the results of the OCR parsing. They give us:
    - id
    - bbox: *$\mathrm{x_0 }, \mathrm{y_0}, \mathrm{x_1}, \mathrm{y_1}$*
    - parent_id
    - label
    - reading_order
    - 
  - Text Tokens (TT) are markdown $m$

# Pipeline

### Definitions

  A document $d$ is a collection of raster images $d \in \mathbb{R}^{H \times W \times 3}$.

  A bounding box is a tuple $b = (x_0, y_0, x_1, y_1) \in \mathbb{Z}^4$ representing the axis-aligned rectangle $[x_0,
  x_1] \times [y_0, y_1]$. Its area is $|b| = (x_1 - x_0)(y_1 - y_0)$.

  ---
### Step 1: OCR — Visual Token Extraction

  $$\text{OCR}(d) = (\mathcal{L}, \mathcal{W})$$

  - Lines $\mathcal{L} = {(b_i, t_i, s_i)}_{i=1}^{n_L}$ — bounding box, text string, confidence score $s_i \in [0, 1]$
  - Words $\mathcal{W} = {(b_j, t_j, \ell_j)}_{j=1}^{n_W}$ — bounding box, text string, parent line index $\ell_j \in
  {1, \ldots, n_L}$

  Words are pre-assigned to lines by the OCR engine via the foreign key $\ell_j$.

### Step 2: Layout Parsing — Structural Extraction

  $$\text{Layout}(d) = (\mathcal{R}, \mathcal{B}, \mathcal{F}, m)$$

  - Regions $\mathcal{R} = {(b_i, \lambda_i, s_i)}_{i=1}^{n_R}$ — coarse page zones with semantic label $\lambda_i$ and
  score $s_i$
  - Blocks $\mathcal{B} = {(b_j, \lambda_j, o_j, c_j)}_{j=1}^{n_B}$ — content blocks with label $\lambda_j$, reading
  order $o_j \in \mathbb{Z} \cup {\bot}$, and text content $c_j$
  - Formulas $\mathcal{F} = {(b_k, t_k, r_k)}_{k=1}^{n_F}$ — LaTeX strings $t_k$ with region assignment $r_k$
  - Markdown $m \in \Sigma^*$ — rendered markdown text of the page

  ---
### Step 3: Layout Tree Construction

  Define the intersection-over-child between a child box $b_c$ and a parent box $b_p$:

  $$\text{IoC}(b_c, b_p) = \frac{|b_c \cap b_p|}{|b_c|}$$

  where $b_c \cap b_p$ is the axis-aligned intersection rectangle (area 0 if disjoint).

  Given a threshold $\tau \in [0, 1]$ (default $\tau = 0.8$), define the parent assignment of a child $c$ with respect
  to candidate parents $P$:

  $$\text{parent}(c, P) = \underset{p \in P}{\arg\max}\;\text{IoC}(b_c, b_p) \quad \text{s.t.} \quad \text{IoC}(b_c, b_p) \geq \tau$$

  (returns $\bot$ if no candidate meets the threshold.)

  The tree $T = (V, E)$ is built level by level:

  | Level | Nodes | Parent set |
  |-------|-------|------------|
  | 0 | $\mathcal{R}$ (sorted by descending area) | $\bot$ (roots) |
  | 1 | $\mathcal{B}$ (sorted by reading order $o_j$) | $\mathcal{R}$ |
  | 2 | $\mathcal{L}$ (sorted by $y_0$) | $\mathcal{B}$ |
  | 3 | $\mathcal{W}$ (preserving original order) | $\mathcal{L}$ via FK $\ell_j$ |

  Note that levels 1–2 use spatial IoC assignment, while level 3 uses the pre-computed foreign key.

  ---
### Step 4: Tree-to-Text Alignment

  Given a reference text $m$, let $\mathbf{t} = (t_1, \ldots, t_N)$ be its tokenization (TreebankWordTokenizer), with
  character spans $\phi(i) = (s_i, e_i)$ recording where each token sits in the original string.

  Define a similarity function $\sigma: V \times \Sigma^* \to [0, 1]$ (default: fuzzy token-sort ratio between the
  node's content and the candidate span).

  For a node $v$ with children $(c_1, \ldots, c_n)$ assigned to token interval $[a, b)$, find a partition $a = k_0 \leq
  k_1 \leq \cdots \leq k_n = b$ maximizing:

  $$\sum_{i=1}^{n} \sigma\left(c_i, \mathbf{t}_{k_{i-1}:k_i}\right)$$

  This is solved by DP. Let $L = b - a$. Define:

  $$J(i, k) = \max_{0 \leq r \leq k} \Big[J(i-1, r) + \sigma\left(c_i, \mathbf{t}_{a+r:a+k}\right)\Big]$$

  with base case $J(0, k) = \sigma(c_1, \mathbf{t}_{a:a+k})$. Traceback from $J(n-1, L)$ recovers the optimal split
  points. Complexity is $O(nL^2)$ per node; for $L > 100$ a greedy $O(nL)$ fallback is used instead.

  The full alignment is computed by recursing from the root with interval $[0, N)$:

  $$\alpha: V \to \{(a, b) \mid 0 \leq a \leq b \leq N\}$$

  mapping every node to its token span, and by extension (via $\phi$) to its character span in $m$.

  ---
### Step 5: Reverse Alignment

  Given a query character span $[q_s, q_e)$ in $m$, find all nodes whose aligned character span overlaps the query:

  $$\text{ReverseAlign}(q_s, q_e) = \left\{\left(v, \frac{|[q_s, q_e) \cap [n_s, n_e)|}{n_e - n_s}\right) \;\middle|\; v \in V, \alpha(v) \mapsto [n_s, n_e), [q_s, q_e) \cap [n_s, n_e) \neq \emptyset\right\}$$


