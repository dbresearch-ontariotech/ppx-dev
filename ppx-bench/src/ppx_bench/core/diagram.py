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

We can also assess the quality by the mean and standard deviation of the score distribution of lines, call this y=mean-score.  
This allows us to compare the end-to-end performance of different scenarios:

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


def _plot_combined(summary_df: pd.DataFrame, title: str, subtitle: str | None = None) -> None:
    import numpy as np
    from scipy.stats import gaussian_kde

    groups = sorted(summary_df.groupby("block_label"), key=lambda kv: -len(kv[1]))
    data = [group["score"].values for _, group in groups]
    counts = [f"{label} ({len(group)})" for label, group in groups]
    bins = 20
    total = sum(len(d) for d in data)
    weights = [np.full_like(d, 100.0 / total, dtype=float) for d in data] if total else None

    fig, ax = plt.subplots(figsize=(11, 5))
    ax.hist(data, bins=bins, range=(0, 1), stacked=True, weights=weights, label=counts, edgecolor="white", linewidth=0.5)

    all_scores = summary_df["score"].values
    if len(all_scores) > 1 and np.ptp(all_scores) > 0:
        xs = np.linspace(0, 1, 200)
        kde = gaussian_kde(all_scores)
        bin_width = 1.0 / bins
        ax.plot(xs, kde(xs) * bin_width * 100.0, color="black", linewidth=1.5, label="density")

    mean_score = summary_df["score"].mean()
    ax.axvline(mean_score, color="red", linestyle="--", linewidth=1, label=f"mean = {mean_score:.2f}")

    full_title = f"{title}\n{subtitle}" if subtitle else title
    ax.set_xlabel("Alignment score")
    ax.set_ylabel("Percentage of lines (%)")
    ax.set_title(full_title)
    ax.set_xlim(0, 1)
    ax.grid(axis="y", alpha=0.3)
    ax.set_axisbelow(True)
    ax.legend(title="Block label (n)", bbox_to_anchor=(1.02, 1), loc="upper left", frameon=False)
    fig.tight_layout()


def _plot_overlap(
    summary_df: pd.DataFrame,
    title: str,
    subtitle: str | None = None,
    group_col: str = "page",
    y_mode: str = "density",
    bin_width: float = 0.05,
) -> None:
    import numpy as np
    from scipy.stats import gaussian_kde

    fig, ax = plt.subplots(figsize=(11, 5))
    xs = np.linspace(0, 1, 200)

    def _sort_key(g):
        try:
            return (0, float(g))
        except (TypeError, ValueError):
            return (1, str(g))
    groups = sorted(summary_df[group_col].unique(), key=_sort_key)
    cmap = plt.get_cmap("viridis", max(len(groups), 2))
    scale = bin_width * 100.0 if y_mode == "percent" else 1.0
    for i, g in enumerate(groups):
        scores = summary_df.loc[summary_df[group_col] == g, "score"].values
        if len(scores) < 2 or np.ptp(scores) == 0:
            continue
        kde = gaussian_kde(scores)
        ax.plot(xs, kde(xs) * scale, color=cmap(i), linewidth=1.5, label=f"{group_col} {g} (n={len(scores)})")

    full_title = f"{title}\n{subtitle}" if subtitle else title
    ax.set_xlabel("Alignment score")
    ax.set_ylabel(f"% of lines (per {bin_width:g} score interval)" if y_mode == "percent" else "Density")
    ax.set_title(full_title)
    ax.set_xlim(0, 1)
    ax.grid(axis="y", alpha=0.3)
    ax.set_axisbelow(True)
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", frameon=False)
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


def _filter_labels(df: pd.DataFrame, labels: set[str] | None) -> pd.DataFrame:
    if not labels:
        return df
    return df[df["block_label"].isin(labels)]


def _label_suffix(labels: set[str] | None) -> str:
    if not labels:
        return ""
    return "_" + "+".join(sorted(labels))


def save_line_noise_diagrams(
    line_df: pd.DataFrame,
    output_dir: Path,
    title_prefix: str = "",
    subtitle: str | None = None,
    labels: set[str] | None = None,
) -> None:
    """Line-score diagrams with one KDE per noise level. line_df must have a `noise` column."""
    output_dir.mkdir(parents=True, exist_ok=True)
    line_df.to_parquet(output_dir / "line_scores.parquet", index=False)

    line_plot = _filter_labels(line_df, labels)
    suffix = _label_suffix(labels)
    prefix = f"{title_prefix} — " if title_prefix else ""
    label_subtitle = f"labels: {', '.join(sorted(labels))}" if labels else None
    full_subtitle = " | ".join(s for s in (subtitle, label_subtitle) if s)

    _plot_combined(line_plot, f"{prefix}Line score distribution (combined across noise levels)", subtitle=full_subtitle)
    plt.savefig(output_dir / f"line_combined{suffix}.png", dpi=150)
    plt.close()

    _plot_overlap(line_plot, f"{prefix}Line score distribution (per-noise)", subtitle=full_subtitle, group_col="noise", y_mode="percent")
    plt.savefig(output_dir / f"line_overlap{suffix}.png", dpi=150)
    plt.close()


def save_diagrams(
    block_df: pd.DataFrame,
    line_df: pd.DataFrame,
    output_dir: Path,
    title_prefix: str = "",
    subtitle: str | None = None,
    labels: set[str] | None = None,
    overlap_by: str = "page",
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    block_df.to_parquet(output_dir / "block_scores.parquet", index=False)
    line_df.to_parquet(output_dir / "line_scores.parquet", index=False)

    block_plot = _filter_labels(block_df, labels)
    line_plot = _filter_labels(line_df, labels)
    suffix = _label_suffix(labels)
    prefix = f"{title_prefix} — " if title_prefix else ""
    label_subtitle = f"labels: {', '.join(sorted(labels))}" if labels else None
    full_subtitle = " | ".join(s for s in (subtitle, label_subtitle) if s)

    _plot_combined(block_plot, f"{prefix}Block score distribution (combined)", subtitle=full_subtitle)
    plt.savefig(output_dir / f"block_combined{suffix}.png", dpi=150)
    plt.close()

    _plot_combined(line_plot, f"{prefix}Line score distribution (combined)", subtitle=full_subtitle)
    plt.savefig(output_dir / f"line_combined{suffix}.png", dpi=150)
    plt.close()

    if overlap_by in block_df.columns and block_df[overlap_by].nunique() > 1:
        _plot_overlap(block_plot, f"{prefix}Block score distribution (per-{overlap_by} overlap)", subtitle=full_subtitle, group_col=overlap_by)
        plt.savefig(output_dir / f"block_overlap{suffix}.png", dpi=150)
        plt.close()

        _plot_overlap(line_plot, f"{prefix}Line score distribution (per-{overlap_by} overlap)", subtitle=full_subtitle, group_col=overlap_by)
        plt.savefig(output_dir / f"line_overlap{suffix}.png", dpi=150)
        plt.close()