"""


What do we want?

We currently have:
per document, page
- alignment: list of match(visual_token, markdown_span, score) in alignment.json
- block.parquet, line.parquet, word.parquet, also formula.parquet
  => we can get block.content, line.content, but also we know which line contains formula by overlapping with formula visual tokens.

Metrics for quality:
Per document and page:
- score distribution/histogram for blocks
- score distribution for lines, *missing alignment should count as score 0*
- overlay the score distribution of multiple pages
- overlap the score distribution of lines containing math vs no math.
- overlap the score distribution of lines belonging to different block label

We can also assess the quality by the mean and standard deviation of the score distribution of lines, call this y=mean-score.  This allows us to compare the end-to-end performance of different scenarios:

- levels of noise to the markdown source (change x% characters at random position to another random character).
  x = 5%, 10%, 20%, 30%, ...
  plot the noise level vs y.

- Use 0% noise as gold standard, and compare the *CHANGE* in alignment markdown span.
  for line_7, the span_true = (a0:i0, b0:j0).
  but if we have noise level = 30%.  span_noise = (a1:i1, b1:j1)
  => if blocks are different => block alignment error => (noise_level, line_id, 0, 0)
  => if (i0,j0) != (i1,j1) => precision = (i0,j0) intersect (i1,j1) / (i1,j1), recall = (i0,j0) intersect (i1,j1) / (i0, j0)
  => row (noise_level, line_id, precision, recall)

The noise experiment:
- create markdown with x% noise, save as markdown_<noise_level>.md
  `uv run ppx-bench corrupt --page-path ../output/resnet/0 --noise-level 5,10,20,30,40`

- perform alignment using the `uv run ppx-align build --page-path ../output/resnet/0 --markdown ../output/resnet/0/markdown/noise_level.md --save ../output/resnet/0/alignment_noise_level.json

- [optional] multi-lingual alignment: plot EN/CN/FR/ etc.  What about the mean-score for each language?

Milestones

[Benchmark]
- write the code for ppx-bench to analyze metric qualities (saved as pandas dataframe .parquet)
- generate plots for the metric qualities
- write code for ppx-bench corrupt
- patch up ppx-align for corrupted markdown
- write code for ppx-bench to analyze the noise_level prec/recall (.parquet)
- plot the noise level effects

[Demo]
- Reverse alignment
- Visual highlight of low score matches

[Presentation]
- Recorded video of the interface
- Google slides

"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from ppx_align.core.align import BlockAlignmentTarget
from ppx_align.core.types import CharAlignmentTarget


def _plot_stacked_hist(summary_df: pd.DataFrame, title: str, subtitle: str | None = None) -> None:
    import numpy as np
    from scipy.stats import gaussian_kde

    groups = sorted(summary_df.groupby("block_label"), key=lambda kv: -len(kv[1]))
    data = [group["score"].values for _, group in groups]
    counts = [f"{label} ({len(group)})" for label, group in groups]
    bins = 20

    fig, ax = plt.subplots(figsize=(11, 5))
    ax.hist(data, bins=bins, range=(0, 1), stacked=True, label=counts, edgecolor="white", linewidth=0.5)

    all_scores = summary_df["score"].values
    if len(all_scores) > 1 and np.ptp(all_scores) > 0:
        xs = np.linspace(0, 1, 200)
        kde = gaussian_kde(all_scores)
        bin_width = 1.0 / bins
        ax.plot(xs, kde(xs) * len(all_scores) * bin_width, color="black", linewidth=1.5, label="density")

    mean_score = summary_df["score"].mean()
    ax.axvline(mean_score, color="red", linestyle="--", linewidth=1, label=f"mean = {mean_score:.2f}")

    full_title = f"{title}\n{subtitle}" if subtitle else title
    ax.set_xlabel("Alignment score")
    ax.set_ylabel("Count")
    ax.set_title(full_title)
    ax.set_xlim(0, 1)
    ax.grid(axis="y", alpha=0.3)
    ax.set_axisbelow(True)
    ax.legend(title="Block label (n)", bbox_to_anchor=(1.02, 1), loc="upper left", frameon=False)
    fig.tight_layout()


def compute_block_scores(
    tree: pd.DataFrame,
    alignment: dict[str, BlockAlignmentTarget],
) -> pd.DataFrame:
    blocks = tree[tree["level_name"] == "block"]
    summary = []
    for _, block in blocks.iterrows():
        node_id = block["node_id"]
        score = alignment[node_id].score if node_id in alignment else 0.0
        summary.append({
            "block_id": node_id,
            "block_label": block["label"] if block["label"] else "unknown",
            "score": score,
        })
    return pd.DataFrame(summary)


def compute_line_scores(
    tree: pd.DataFrame,
    alignment: dict[str, CharAlignmentTarget],
) -> pd.DataFrame:
    lines = tree[tree["level_name"] == "line"]
    blocks = tree[tree["level_name"] == "block"][["node_id", "label"]].rename(
        columns={"node_id": "parent_id", "label": "block_label"}
    )
    summary = []
    for _, line in lines.iterrows():
        node_id = line["node_id"]
        score = alignment[node_id].score if node_id in alignment else 0.0
        summary.append({
            "line_id": node_id,
            "parent_id": line["parent_id"],
            "score": score,
        })
    df = pd.DataFrame(summary).merge(blocks, on="parent_id", how="left")
    df["block_label"] = df["block_label"].fillna("unknown")
    return df


def save_diagrams(
    block_df: pd.DataFrame,
    line_df: pd.DataFrame,
    output_dir: Path,
    title_prefix: str = "",
    subtitle: str | None = None,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    block_df.to_parquet(output_dir / "block_scores.parquet", index=False)
    line_df.to_parquet(output_dir / "line_scores.parquet", index=False)

    prefix = f"{title_prefix} — " if title_prefix else ""
    _plot_stacked_hist(block_df, f"{prefix}Block score distribution", subtitle=subtitle)
    plt.savefig(output_dir / "block_score_dist.png", dpi=150)
    plt.close()

    _plot_stacked_hist(line_df, f"{prefix}Line score distribution", subtitle=subtitle)
    plt.savefig(output_dir / "line_score_dist.png", dpi=150)
    plt.close()