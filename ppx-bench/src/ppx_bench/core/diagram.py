from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from ppx_align.core.align import BlockAlignmentTarget
from ppx_align.core.types import CharAlignmentTarget


def _aggregate_mean_std(df: pd.DataFrame, value_col: str) -> tuple[float, float, str]:
    """Return (mean, std, level) where mean is the mean of per-group means and std is across groups.

    Prefers 'document' > 'page' > per-row fallback. Returns level label for display.
    """
    for level in ("document", "page"):
        if level in df.columns and df[level].nunique() > 1:
            group_means = df.groupby(level)[value_col].mean()
            return float(group_means.mean()), float(group_means.std(ddof=0)), f"cross-{level}"
    return float(df[value_col].mean()), float(df[value_col].std(ddof=0)), "per-line"


def _plot_combined(summary_df: pd.DataFrame, title: str, subtitle: str | None = None, top_n_labels: int = 8) -> None:
    import numpy as np
    from scipy.stats import gaussian_kde

    all_groups = sorted(summary_df.groupby("block_label"), key=lambda kv: -len(kv[1]))
    if len(all_groups) > top_n_labels:
        top = all_groups[:top_n_labels]
        rest = all_groups[top_n_labels:]
        rest_rows = pd.concat([g for _, g in rest], ignore_index=True)
        groups = top + [(f"other ({len(rest)} labels)", rest_rows)]
    else:
        groups = all_groups

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

    mean_score, std_score, std_level = _aggregate_mean_std(summary_df, "score")
    ax.axvline(mean_score, color="black", linestyle="--", linewidth=2.0, label=f"μ = {mean_score:.2f}, σ = {std_score:.2f} ({std_level})", zorder=5)
    ymax = ax.get_ylim()[1]
    ax.annotate(
        f"μ = {mean_score:.2f}",
        xy=(mean_score, ymax * 0.92),
        xytext=(6, 0), textcoords="offset points",
        fontsize=10, fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.25", facecolor="white", edgecolor="black", linewidth=0.8),
        zorder=6,
    )

    full_title = f"{title}\n{subtitle}" if subtitle else title
    ax.set_xlabel("Alignment score")
    ax.set_ylabel("Percentage of lines (%)")
    ax.set_title(full_title)
    ax.set_xlim(0, 1)
    ax.grid(axis="y", alpha=0.3)
    ax.set_axisbelow(True)
    ax.legend(title="Block label (n)", bbox_to_anchor=(1.02, 1), loc="upper left", frameon=False, fontsize=9)
    fig.tight_layout()


def _plot_overlap(
    summary_df: pd.DataFrame,
    title: str,
    subtitle: str | None = None,
    group_col: str = "page",
    score_col: str = "score",
    x_label: str = "Alignment score",
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
        scores = summary_df.loc[summary_df[group_col] == g, score_col].values
        if len(scores) == 0:
            continue
        mean, std = float(np.mean(scores)), float(np.std(scores))
        label = f"{group_col} {g} (n={len(scores)}, μ={mean:.2f}, σ={std:.2f})"
        if len(scores) >= 2 and np.ptp(scores) > 0:
            kde = gaussian_kde(scores)
            ax.plot(xs, kde(xs) * scale, color=cmap(i), linewidth=1.5, label=label)
        else:
            ax.axvline(mean, color=cmap(i), linewidth=1.5, linestyle=":", label=label)

    full_title = f"{title}\n{subtitle}" if subtitle else title
    ax.set_xlabel(x_label)
    ax.set_ylabel(f"% of lines (per {bin_width:g} interval)" if y_mode == "percent" else "Density")
    ax.set_title(full_title)
    ax.set_xlim(0, 1)
    ax.grid(axis="y", alpha=0.3)
    ax.set_axisbelow(True)
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", frameon=False)
    fig.tight_layout()


def _plot_pr_mean_vs_noise(pr_df: pd.DataFrame, title: str, subtitle: str | None = None, style: str = "bar") -> None:
    import numpy as np

    pr_df = pr_df.copy()
    denom = pr_df["precision"] + pr_df["recall"]
    pr_df["f1"] = np.where(denom > 0, 2 * pr_df["precision"] * pr_df["recall"] / denom.replace(0, 1), 0.0)

    group_level = next((lvl for lvl in ("document", "page") if lvl in pr_df.columns and pr_df[lvl].nunique() > 1), None)

    summary = pr_df.groupby("noise_level").agg(
        precision_mean=("precision", "mean"),
        recall_mean=("recall", "mean"),
        f1_mean=("f1", "mean"),
        block_error_rate=("is_block_error", "mean"),
        n=("line_id", "count"),
    ).reset_index()
    summary["noise_num"] = summary["noise_level"].astype(float)
    summary = summary.sort_values("noise_num")

    if group_level is not None:
        per_group = pr_df.groupby(["noise_level", group_level]).agg(
            precision=("precision", "mean"),
            recall=("recall", "mean"),
            f1=("f1", "mean"),
            block_error=("is_block_error", "mean"),
        ).reset_index()
        cross_std = per_group.groupby("noise_level").agg(
            precision_std=("precision", lambda s: s.std(ddof=0)),
            recall_std=("recall", lambda s: s.std(ddof=0)),
            f1_std=("f1", lambda s: s.std(ddof=0)),
            block_error_std=("block_error", lambda s: s.std(ddof=0)),
        ).reset_index()
        summary = summary.merge(cross_std, on="noise_level", how="left")

    x_labels = [f"{v:g}" for v in summary["noise_num"].values]
    x_pos = np.arange(len(x_labels))
    x_num = summary["noise_num"].values

    fig, axes = plt.subplots(2, 2, figsize=(12, 8), sharex=True)
    full_title = f"{title}\n{subtitle}" if subtitle else title
    fig.suptitle(full_title)

    panels = [
        (axes[0, 0], "precision_mean", "precision_std", "Precision", "#1f77b4", "o"),
        (axes[0, 1], "recall_mean", "recall_std", "Recall", "#2ca02c", "s"),
        (axes[1, 0], "f1_mean", "f1_std", "F1", "#9467bd", "D"),
        (axes[1, 1], "block_error_rate", "block_error_std", "Block error rate", "#d62728", "x"),
    ]

    for ax, mean_col, std_col, label, color, marker in panels:
        y_mean = summary[mean_col].values
        y_std = summary[std_col].fillna(0).values if (group_level is not None and std_col in summary.columns) else None
        err_label = f"±σ (cross-{group_level})" if group_level is not None else None

        if style == "bar":
            ax.bar(
                x_pos, y_mean,
                yerr=y_std,
                color=color, alpha=0.75, edgecolor=color, linewidth=1.2,
                error_kw=dict(ecolor="black", capsize=3, elinewidth=1),
                label=err_label,
            )
        else:  # line
            if y_std is not None:
                ax.fill_between(x_num, np.clip(y_mean - y_std, 0, 1), np.clip(y_mean + y_std, 0, 1), color=color, alpha=0.15, label=err_label)
            ax.plot(x_num, y_mean, marker=marker, linewidth=1.8, color=color, label=f"{label} (mean)")

        ax.set_title(label)
        ax.set_ylim(0, 1.05)
        ax.grid(axis="y" if style == "bar" else "both", alpha=0.3)
        ax.set_axisbelow(True)
        ax.legend(loc="best", frameon=False, fontsize=8)

    if style == "bar":
        for ax in axes[1]:
            ax.set_xticks(x_pos)
            ax.set_xticklabels(x_labels, rotation=45, ha="right")
    for ax in axes[1]:
        ax.set_xlabel("Noise level")
    for ax in axes[:, 0]:
        ax.set_ylabel("Value (0–1)")

    fig.tight_layout(rect=(0, 0, 1, 0.96))


def save_precision_recall_diagrams(
    pr_df: pd.DataFrame,
    output_dir: Path,
    title_prefix: str = "",
    subtitle: str | None = None,
) -> None:
    """Precision/recall diagrams. pr_df must have columns: noise_level, line_id, precision, recall, is_block_error."""
    output_dir.mkdir(parents=True, exist_ok=True)
    pr_df.to_parquet(output_dir / "precision_recall.parquet", index=False)

    prefix = f"{title_prefix} — " if title_prefix else ""

    _plot_pr_mean_vs_noise(pr_df, f"{prefix}Precision / recall vs noise level", subtitle=subtitle, style="bar")
    plt.savefig(output_dir / "pr_mean_vs_noise_bar.png", dpi=150)
    plt.close()

    _plot_pr_mean_vs_noise(pr_df, f"{prefix}Precision / recall vs noise level", subtitle=subtitle, style="line")
    plt.savefig(output_dir / "pr_mean_vs_noise_line.png", dpi=150)
    plt.close()

    _plot_overlap(pr_df, f"{prefix}Precision distribution (per-noise)", subtitle=subtitle, group_col="noise_level", score_col="precision", x_label="Precision", y_mode="percent")
    plt.savefig(output_dir / "precision_overlap.png", dpi=150)
    plt.close()

    _plot_overlap(pr_df, f"{prefix}Recall distribution (per-noise)", subtitle=subtitle, group_col="noise_level", score_col="recall", x_label="Recall", y_mode="percent")
    plt.savefig(output_dir / "recall_overlap.png", dpi=150)
    plt.close()


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
        _plot_overlap(block_plot, f"{prefix}Block score distribution (per-{overlap_by} overlap)", subtitle=full_subtitle, group_col=overlap_by, y_mode="percent")
        plt.savefig(output_dir / f"block_overlap{suffix}.png", dpi=150)
        plt.close()

        _plot_overlap(line_plot, f"{prefix}Line score distribution (per-{overlap_by} overlap)", subtitle=full_subtitle, group_col=overlap_by, y_mode="percent")
        plt.savefig(output_dir / f"line_overlap{suffix}.png", dpi=150)
        plt.close()