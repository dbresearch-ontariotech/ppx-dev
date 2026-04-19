# Benchmark analysis

Based on `benchmark/`, `noise_benchmark/`, and `precision_recall_benchmark/` parquets.

## Dataset

| | count |
|---|---|
| Documents | 6 |
| Pages | 130 |
| Blocks | 1,505 |
| Lines | 13,908 |

**Documents:** PubLayNet, clip, deeplearning, paddleocrv3, resnet, rl.

**Pages per document:**

| doc | pages |
|---|---|
| PubLayNet | 8 |
| clip | 48 |
| deeplearning | 10 |
| paddleocrv3 | 24 |
| resnet | 12 |
| rl | 28 |

**Block labels (visual-layer categories, counted at the block level):**

| label | count | block mean | line count | line mean |
|---|---|---|---|---|
| text | 718 | 0.97 | 5,114 | 0.96 |
| paragraph_title | 144 | 0.82 | 149 | 0.96 |
| figure_title | 119 | 0.80 | 492 | 0.97 |
| number | 118 | 0.02 | 1 | 0.00 |
| header | 77 | 0.39 | 64 | 0.55 |
| formula | 62 | 0.98 | 268 | 0.75 |
| formula_number | 55 | 0.18 | 1 | 0.00 |
| table | 43 | 0.90 | 2,035 | 0.99 |
| image | 37 | 0.37 | 1,291 | 0.42 |
| reference | 31 | 1.00 | 1,416 | 0.96 |
| chart | 30 | 0.41 | 2,137 | 0.45 |
| footer | 26 | 0.02 | 26 | 0.02 |
| footnote | 14 | 0.45 | 43 | 0.52 |
| algorithm | 8 | 1.00 | 204 | 0.95 |
| aside_text | 8 | 0.32 | 14 | 0.58 |
| abstract | 6 | 1.00 | 99 | 0.96 |
| doc_title | 5 | 0.90 | 6 | 1.00 |
| vision_footnote | 3 | 1.00 | 3 | 1.00 |
| reference_content | 1 | 0.00 | 4 | 0.00 |
| `unknown` (lines only) | — | — | 541 | 0.00 |

Line counts exceed block counts for `text`, `table`, `reference`, `image`, `chart` because those blocks contain multiple OCR line tokens; `number` and `formula_number` are typically single-line blocks whose lines fall under a different parent label after tree assignment.

## 1. Vanilla benchmark (uncorrupted)

| | mean | cross-doc σ |
|---|---|---|
| Blocks | 0.79 | 0.07 |
| Lines | 0.80 | 0.08 |

![Per-document line score distribution (uncorrupted)](../output/benchmark/line_overlap.png)

Docs are fairly consistent (σ ≈ 0.07–0.08 across 6 docs) — the pipeline generalizes, no single doc dragging everything down. The per-document KDEs above sit on top of each other with a single shared peak near score=1.0; `rl` is the one visibly flatter curve.

**Strong structural bimodality by block label (line-level means):**

| label group | line mean | what it means |
|---|---|---|
| `text`, `paragraph_title`, `table`, `reference`, `figure_title`, `algorithm`, `abstract` | 0.95–0.99 | text-like content aligns near-perfectly |
| `formula` | 0.75 | block matches well (0.98 block mean) but char spans inside the formula only partially overlap markdown nodes |
| `chart`, `image` | 0.45, 0.42 | non-textual OCR content has no semantic anchor in markdown |
| `header` | 0.55 | running heads are repetitive across pages; some distinctive tokens keep individual lines alignable (block mean 0.39 — block confuses across pages, lines slightly better) |
| `footer` | 0.02 | page numbers / short footers — low-signal for sentence embeddings |
| `unknown` | 0.00 | 541 lines with no block label — structural gap in OCR output |
| `formula_number`, `number` | — (n=1 each, trivial at line level; block means 0.18 / 0.02) | short numeric content fails at the block level; nearly no lines assigned |

![Line score distribution stacked by block label](../output/benchmark/line_combined.png)

The stacked histogram above makes the bimodality concrete: the mass at score=1.0 is almost entirely `text` / `table` / `reference`; the mass at score=0 is `unknown` + `image`.

**Conclusion:** alignment quality is a *function of content type*, not a uniform "good/bad." The low overall score is driven almost entirely by ~20–30% of lines in non-textual blocks (images/charts/numbers), not by poor alignment of actual text. Fundamental limitation of embedding-based alignment, not a regression.

**Outliers:** `rl` has a meaningfully lower baseline (0.638 line mean) — content-heavy with figures. `PubLayNet` and `resnet` lead (~0.88).

## 2. Noise benchmark (line score vs noise)

| noise | mean line score | drop from baseline |
|---|---|---|
| 0.000 | 0.787 | — |
| 0.005 | 0.792 | +0.6% |
| 0.006 | 0.782 | –0.6% |
| 0.007 | 0.784 | –0.4% |
| 0.008 | 0.774 | –1.7% |
| 0.009 | 0.760 | –3.5% |
| 0.010 | 0.750 | –4.8% |
| 0.020 | 0.734 | –6.8% |
| 0.030 | 0.702 | –10.8% |
| 0.040 | 0.690 | –12.4% |
| 0.050 | 0.669 | –15.0% |
| 0.100 | 0.590 | –25.1% |
| 0.200 | 0.469 | –40.5% |

Line score at noise=0.005 is *slightly higher* than baseline (+0.6%); at 0.006–0.007 it barely moves (<1% drop). The aligner still finds high-scoring matches even when some blocks are placed incorrectly — the score measures how well a line matched *wherever* it ended up, not whether it ended up in the right place. Block error rate (Section 3) is the earlier-warning metric.

![Per-noise line score distribution](../output/noise_benchmark/line_overlap.png)

Each curve above is a KDE of line scores at one noise level. The peak at score=1.0 (baseline, dark purple) progressively shifts leftward and flattens — mass moves from the 1-peak toward the middle of the range as noise increases.

Degradation is monotonic across the sampled range. All 6 documents share parallel trajectories — same slope, offset by baseline quality. `PubLayNet` and `resnet` remain on top (0.89 → 0.49 / 0.88 → 0.58); `rl` remains at the bottom (0.64 → 0.45). No doc "breaks" before others.

## 3. Precision/recall benchmark

| noise | precision | recall | F1 | block error rate | regime |
|---|---|---|---|---|---|
| 0.000 | 1.00 | 1.00 | 1.00 | 0% | intact |
| 0.005 | 0.90 | 0.90 | 0.90 | 3% | early shoulder |
| 0.006 | 0.85 | 0.85 | 0.85 | 10% | block-error triples |
| 0.007 | 0.83 | 0.82 | 0.82 | 12% | smooth |
| 0.008 | 0.81 | 0.81 | 0.81 | 11% | smooth |
| 0.009 | 0.73 | 0.72 | 0.72 | 18% | **step #1** |
| 0.01 | 0.70 | 0.68 | 0.68 | 22% | smooth |
| 0.02 | 0.64 | 0.61 | 0.62 | 26% | smooth |
| 0.03 | 0.53 | 0.50 | 0.51 | 36% | **step #2** |
| 0.04 | 0.50 | 0.46 | 0.47 | 39% | smooth |
| 0.05 | 0.45 | 0.41 | 0.42 | 41% | smooth |
| 0.10 | 0.32 | 0.29 | 0.29 | 48% | tail |
| 0.20 | 0.14 | 0.12 | 0.13 | 64% | tail |

![Precision, recall, F1 and block error rate vs noise (bars, with cross-doc σ)](../output/precision_recall_benchmark/pr_mean_vs_noise_bar.png)

![Same metrics as lines with continuous noise axis](../output/precision_recall_benchmark/pr_mean_vs_noise_line.png)

The bar chart (above, top) gives the per-level numbers with error bars. The line chart (above, bottom) places each noise level at its true x-position — the step-changes appear as visual bends in otherwise-smooth descents. Together: the bars quantify the step, the lines show its shape.

**Degradation is a staircase, not a smooth curve.** Two discrete step-changes separate the descent:
- **Step #1** between 0.008 and 0.009: F1 drops from 0.81 → 0.72 (–0.09), block errors jump from 11% → 18%.
- **Step #2** between 0.02 and 0.03: F1 drops from 0.62 → 0.51 (–0.11), block errors climb from 26% → 36%.

There is also an **earlier shoulder between 0.005 and 0.006**: block error rate triples (3% → 10%) even though F1 only moves 0.05 and mean line score barely changes. This marks the first point where blocks begin placing incorrectly; the damage hasn't yet propagated into the line-level metric.

Between these thresholds the system decays gently; at them the block-alignment mechanism loses a discrete cohort of matches in a single doubling of noise. The staircase pattern suggests *discrete failure modes* — different subsets of blocks flipping at different noise thresholds — most likely gated by content length and distinctiveness (short/sparse-token blocks fail first, medium blocks fail next, long blocks are more robust).

**Different documents flip at different thresholds.** Looking at per-document block error rates in the transition zone (0.006 – 0.009):
- `paddleocrv3` and `rl` cross 25% block error *already at noise=0.006* — their first step happens early.
- `PubLayNet`, `resnet`, `clip`, `deeplearning` stay below 10% through 0.008 and only step up at 0.009.

The aggregate step at ~0.009 is the average of docs that cross earlier and docs that cross later — individual docs have sharper, shifted staircases of their own. Weaker-baseline documents fail at lower noise, which is consistent with (but does not prove) the content-distinctiveness hypothesis.

**Block error rate is the earliest warning metric.** At noise=0.006, mean line score barely moves (0.787 → 0.782, –0.6%), while block error rate triples (3% → 10%) and precision drops from 0.90 to 0.85. Lines that survive to produce any alignment still receive high scores; the damage shows up first as blocks landing in the wrong AST range. Monitoring line-score alone would underestimate early-stage degradation.

> **Aside (wording for the paper):** the staircase observation is empirical and directly supported by the data. The *content-length / distinctiveness* explanation is a hypothesis and is not verified in this work. Paper language should be along the lines of: *"we observe two discrete noise thresholds at ~0.009 and ~0.025. We hypothesize this staircase is driven by content-length variation in block embeddings (short blocks lose margin earlier than long blocks), but validating this per-label mechanism remains future work."* State the observation as fact, the mechanism as a candidate explanation.

**The first step lives just below 1% noise, near 0.009.** Below 0.008 the system is genuinely near-intact (F1 ≥ 0.85). "≤ 1% noise" straddles the first cliff rather than sitting safely below it.

**Block-level misalignment is the dominant failure mode.** Precision drops to 0.14 at noise=0.2 because 64% of lines have their parent block reassigned to a different AST range — those zero out precision and recall regardless of char-span behavior.

**Precision ≈ recall ≈ F1 at every noise level.** The non-block-error span overlap is symmetric, and the three metrics stay within 0.03 of each other across all 13 noise levels. Consequence of the char-span overlap metric combined with largely exact matches.

**Precision distribution is strongly bimodal at every noise level** — most lines are either ~0 (block error / miss) or ~1 (exact overlap). Increasing noise *shifts mass between the two peaks*, it doesn't smear the middle. Alignment succeeds or fails per line; there is little partial credit.

![Per-noise precision distribution](../output/precision_recall_benchmark/precision_overlap.png)

Each curve above has two peaks (near 0 and near 1) at every noise level. As noise grows, the 1-peak shrinks and the 0-peak grows — but the middle of the range stays nearly empty throughout.

**Cross-doc σ peaks in the transition zone, not the extremes.** Near-zero at noise=0 (by definition), ~0.08 at noise=0.005, widest (0.10–0.14) at noise=0.02–0.05, and shrinking again to ~0.04 at noise=0.2. Documents diverge most in the middle band — that's where content-specific resilience shows up; at the extremes everyone is either fine or broken.

## Cross-cutting observations

- **Alignment is a binary per-line success/failure, gated by block-level correctness.** Get the block right → char span usually lands exactly; get the block wrong → score 0.
- **The block-alignment stage is the fragile link.** Embedding-based block matching flips easily when a handful of distinguishing tokens change, cascading into line-level failure.
- **Text-like content aligns near-perfectly; non-textual content (images, charts, raw numbers, footers) is a structural blind spot** unrelated to noise.
- **All 6 documents share the same degradation trajectory** — differences are in baseline difficulty, not sensitivity to noise.
- **Degradation is a staircase with discrete thresholds** (~0.009 and ~0.025), not a smooth curve. Block error first rises at 0.006 (early shoulder), steps up at 0.009, erodes gradually to 0.02, steps up again at 0.03, then slowly decays through the long tail. Weaker documents (`paddleocrv3`, `rl`) cross the first step earlier than stronger ones.
- **Block error rate is the earliest-warning metric.** It moves significantly at 0.006 while line-score and F1 are still near-healthy. Monitoring line-score alone would understate early degradation.

## Document-specific notes

- **`rl`** is the structural weak point (baseline 0.64 line mean, already 26% block error at noise=0.006) — dense with figures and short labels; crosses step #1 at the earliest noise level of any doc.
- **`paddleocrv3`** is the other early-flipper (29% block error at noise=0.006 vs <5% for the stronger docs). Same pattern as `rl` — short/repetitive content pushes its first step to 0.006 instead of 0.009.
- **`PubLayNet`, `resnet`, `clip`, `deeplearning`** stay below 10% block error through noise=0.008 and only cross step #1 at 0.009. `resnet` in particular keeps span-level precision cleaner than the aggregate at every noise level (precision 0.29 at noise=0.1 vs 0.32 mean).

## Follow-ups worth running

- **Per-label breakdown of each step.** Group precision by `block_label` at noise ∈ {0.008, 0.009, 0.02, 0.03} and check whether the two steps are driven by specific label classes flipping together (expected: short / low-distinctiveness labels at step #1, medium at step #2).
- **Block-alignment diagnostics.** Which embedding tokens dominate each block's match? If one or two tokens carry the match, corrupting them explains the threshold structure and why the system fails in chunks rather than gradually.
- **Finer sampling around step #2 (0.021–0.029).** Same question as the 0.006–0.009 run answered — is the second step as sharp as the first, or does it have internal structure?
