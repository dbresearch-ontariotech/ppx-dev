import typer
from pathlib import Path
from typing import Annotated, Optional

app = typer.Typer(help="Benchmarking for the ppx OCR pipeline.", pretty_exceptions_enable=False)


@app.callback()
def main():
    pass


BENCHMARK_DIR_NAME = "benchmark"


def _alignment_filename(noise_tag: str | None) -> str:
    return f"alignment_{noise_tag}.json" if noise_tag else "alignment.json"


def _diagrams_dirname(noise_tag: str | None) -> str:
    return f"diagrams_{noise_tag}" if noise_tag else "diagrams"


def _benchmark_dirname(noise_tag: str | None) -> str:
    return f"{BENCHMARK_DIR_NAME}_{noise_tag}" if noise_tag else BENCHMARK_DIR_NAME


def _is_page_dir(p: Path, noise_tag: str | None = None) -> bool:
    return (p / "layout-tree.parquet").exists() and (p / _alignment_filename(noise_tag)).exists()


NOISE_BENCHMARK_DIR_NAME = "noise_benchmark"
PR_BENCHMARK_DIR_NAME = "precision_recall_benchmark"
_RESERVED_DIRS = {NOISE_BENCHMARK_DIR_NAME, PR_BENCHMARK_DIR_NAME}


def _is_document_dir(p: Path, noise_tag: str | None = None) -> bool:
    if not p.is_dir() or p.name.startswith(BENCHMARK_DIR_NAME) or p.name in _RESERVED_DIRS:
        return False
    return any(_is_page_dir(d, noise_tag) for d in p.iterdir() if d.is_dir())


def _is_any_document_dir(p: Path) -> bool:
    """Document dir with at least one alignment file (baseline or any noise variant) on some page."""
    if not p.is_dir() or p.name.startswith(BENCHMARK_DIR_NAME) or p.name in _RESERVED_DIRS:
        return False
    for d in p.iterdir():
        if d.is_dir() and _discover_noise_tags_for_page(d):
            return True
    return False


def _process_document(doc_dir: Path, pages: set[str] | None = None, labels: set[str] | None = None, progress=None, noise_tag: str | None = None):
    import pandas as pd
    from ppx_bench.core.diagram import save_diagrams

    page_dirs = sorted(
        (d for d in doc_dir.iterdir() if d.is_dir() and _is_page_dir(d, noise_tag)),
        key=lambda d: int(d.name) if d.name.isdigit() else d.name,
    )
    if pages:
        page_dirs = [d for d in page_dirs if d.name in pages]
    if not page_dirs:
        return None, None

    all_blocks = []
    all_lines = []
    task = progress.add_task(f"{doc_dir.name}", total=len(page_dirs)) if progress else None
    for page_dir in page_dirs:
        if progress:
            progress.update(task, description=f"{doc_dir.name} / page {page_dir.name}")
        block_df, line_df = _process_page(page_dir, labels=labels, noise_tag=noise_tag)
        all_blocks.append(block_df.assign(page=page_dir.name))
        all_lines.append(line_df.assign(page=page_dir.name))
        if progress:
            progress.advance(task)

    doc_block = pd.concat(all_blocks, ignore_index=True)
    doc_line = pd.concat(all_lines, ignore_index=True)
    page_names = [d.name for d in page_dirs]
    subtitle = f"pages: {', '.join(page_names)}" if len(page_names) <= 10 else f"{len(page_names)} pages: {page_names[0]}…{page_names[-1]}"
    if noise_tag:
        subtitle = f"noise={noise_tag} | {subtitle}"
    save_diagrams(doc_block, doc_line, doc_dir / _diagrams_dirname(noise_tag), title_prefix=doc_dir.name, subtitle=subtitle, labels=labels, overlap_by="page")
    return doc_block, doc_line


def _process_page(page_dir: Path, labels: set[str] | None = None, noise_tag: str | None = None):
    import pandas as pd
    from ppx_align.core.types import DocAlignment
    from ppx_bench.core.diagram import compute_block_scores, compute_line_scores, save_diagrams

    tree = pd.read_parquet(page_dir / "layout-tree.parquet", engine="fastparquet")
    doc_alignment = DocAlignment.model_validate_json((page_dir / _alignment_filename(noise_tag)).read_text())

    block_df = compute_block_scores(tree, doc_alignment.block_alignments)
    line_df = compute_line_scores(tree, doc_alignment.line_alignments)

    subtitle = f"noise={noise_tag}" if noise_tag else None
    save_diagrams(block_df, line_df, page_dir / _diagrams_dirname(noise_tag), title_prefix=f"Page {page_dir.name}", subtitle=subtitle, labels=labels)
    return block_df, line_df


def _parse_pages(spec: str) -> set[str]:
    pages: set[str] = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start, end = part.split("-", 1)
            pages.update(str(i) for i in range(int(start), int(end) + 1))
        else:
            pages.add(part)
    return pages


def _parse_labels(spec: str) -> set[str]:
    return {p.strip() for p in spec.split(",") if p.strip()}


def _noise_tag(value: float | None) -> str | None:
    if value is None:
        return None
    val = value / 100.0 if value > 1.0 else value
    if not 0.0 <= val <= 1.0:
        raise typer.BadParameter(f"noise must be in [0, 1] or [1, 100]: got {value}")
    return f"{val:g}"


def _parse_noise_levels(spec: str) -> list[float]:
    levels: list[float] = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        val = float(part)
        if val > 1.0:
            val = val / 100.0
        if not 0.0 <= val <= 1.0:
            raise typer.BadParameter(f"noise level must be in [0, 1] or [1, 100]: got {part}")
        levels.append(val)
    return sorted(set(levels))


def _corrupt_page(page_dir: Path, noise_levels: list[float], seed: int | None) -> int:
    from ppx_align.core.storage import load
    from ppx_align.core.md import build_parsed_doc
    from ppx_align.core.types import DocAlignment
    from ppx_bench.core.corrupt import corrupt_markdown, spans_from_line_alignments

    alignment_path = page_dir / "alignment.json"
    if not alignment_path.exists():
        typer.echo(f"  skipping {page_dir.name}: alignment.json missing", err=True)
        return 0

    _, md_doc = load(str(page_dir))
    doc = build_parsed_doc(md_doc)
    alignment = DocAlignment.model_validate_json(alignment_path.read_text())
    spans = spans_from_line_alignments(alignment.line_alignments, doc)

    for level in noise_levels:
        corrupted = corrupt_markdown(doc.markdown, spans, level, seed=seed)
        (page_dir / f"markdown_{level:g}.md").write_text(corrupted, encoding="utf-8")
    return len(noise_levels)


@app.command(name="diagrams")
def create_diagrams_cmd(
    path: Annotated[Path, typer.Argument(help="Page directory or document directory containing page subdirectories")],
    pages: Annotated[Optional[str], typer.Option("--pages", "-p", help="Comma-separated page names or ranges (e.g. '0,2,5-8'). Default: all pages.")] = None,
    labels: Annotated[Optional[str], typer.Option("--labels", "-l", help="Comma-separated block labels to include (e.g. 'text,paragraph_title'). Default: all labels.")] = None,
    noise: Annotated[Optional[float], typer.Option("--noise", "-n", help="Noise level of alignment to read (fraction 0.05 or percentage 5). Default: the uncorrupted alignment.")] = None,
):
    """Create diagrams for block and line score distributions of a page or document."""
    from rich.progress import Progress, BarColumn, TaskProgressColumn, TimeElapsedColumn, TextColumn

    label_filter = _parse_labels(labels) if labels else None
    page_filter = _parse_pages(pages) if pages else None
    noise_tag = _noise_tag(noise)

    if _is_page_dir(path, noise_tag):
        _process_page(path, labels=label_filter, noise_tag=noise_tag)
        typer.echo(f"Saved diagrams to {path / _diagrams_dirname(noise_tag)}")
        return

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
    ) as progress:
        doc_block, doc_line = _process_document(path, pages=page_filter, labels=label_filter, progress=progress, noise_tag=noise_tag)

    if doc_block is None:
        typer.echo(f"No page directories found under {path}", err=True)
        raise typer.Exit(1)

    typer.echo(f"Saved document summary to {path / _diagrams_dirname(noise_tag)}")


@app.command(name="benchmark")
def benchmark_cmd(
    output_dir: Annotated[Path, typer.Argument(help="Root output directory containing document subdirectories")],
    labels: Annotated[Optional[str], typer.Option("--labels", "-l", help="Comma-separated block labels to include (e.g. 'text,paragraph_title'). Default: all labels.")] = None,
    noise: Annotated[Optional[float], typer.Option("--noise", "-n", help="Noise level of alignment to read (fraction 0.05 or percentage 5). Default: the uncorrupted alignment.")] = None,
):
    """Build diagrams for every document under output_dir and an aggregate summary at output_dir/benchmark."""
    import pandas as pd
    from rich.progress import Progress, BarColumn, TaskProgressColumn, TimeElapsedColumn, TextColumn
    from ppx_bench.core.diagram import save_diagrams

    label_filter = _parse_labels(labels) if labels else None
    noise_tag = _noise_tag(noise)

    doc_dirs = sorted(d for d in output_dir.iterdir() if _is_document_dir(d, noise_tag))
    if not doc_dirs:
        typer.echo(f"No document directories found under {output_dir}", err=True)
        raise typer.Exit(1)

    all_blocks = []
    all_lines = []
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
    ) as progress:
        overall = progress.add_task("All documents", total=len(doc_dirs))
        for doc_dir in doc_dirs:
            progress.update(overall, description=f"Document {doc_dir.name}")
            doc_block, doc_line = _process_document(doc_dir, labels=label_filter, progress=progress, noise_tag=noise_tag)
            if doc_block is None:
                progress.advance(overall)
                continue
            all_blocks.append(doc_block.assign(document=doc_dir.name))
            all_lines.append(doc_line.assign(document=doc_dir.name))
            progress.advance(overall)

    if not all_blocks:
        typer.echo("No documents produced data", err=True)
        raise typer.Exit(1)

    bench_block = pd.concat(all_blocks, ignore_index=True)
    bench_line = pd.concat(all_lines, ignore_index=True)
    doc_names = [d.name for d in doc_dirs]
    subtitle = f"docs: {', '.join(doc_names)}" if len(doc_names) <= 6 else f"{len(doc_names)} documents"
    if noise_tag:
        subtitle = f"noise={noise_tag} | {subtitle}"

    bench_dir = output_dir / _benchmark_dirname(noise_tag)
    save_diagrams(bench_block, bench_line, bench_dir, title_prefix=f"benchmark (noise={noise_tag})" if noise_tag else "benchmark", subtitle=subtitle, labels=label_filter, overlap_by="document")
    typer.echo(f"Saved benchmark summary to {bench_dir}")


def _discover_noise_tags_for_page(page_dir: Path) -> list[str]:
    tags: list[str] = []
    if (page_dir / "alignment.json").exists():
        tags.append("0")
    for f in page_dir.glob("alignment_*.json"):
        tags.append(f.stem.removeprefix("alignment_"))
    return sorted(set(tags), key=lambda t: float(t))


def _discover_noise_tags_for_document(doc_dir: Path) -> list[str]:
    found: set[str] = set()
    for d in doc_dir.iterdir():
        if d.is_dir():
            found.update(_discover_noise_tags_for_page(d))
    return sorted(found, key=lambda t: float(t))


def _line_scores_for_tag(page_dir: Path, noise_tag: str, labels: set[str] | None = None):
    import pandas as pd
    from ppx_align.core.types import DocAlignment
    from ppx_bench.core.diagram import compute_line_scores

    alignment_file = page_dir / _alignment_filename(None if noise_tag == "0" else noise_tag)
    if not alignment_file.exists():
        return None
    tree = pd.read_parquet(page_dir / "layout-tree.parquet", engine="fastparquet")
    alignment = DocAlignment.model_validate_json(alignment_file.read_text())
    return compute_line_scores(tree, alignment.line_alignments)


def _parsed_doc_from_markdown(markdown_path: Path):
    from ppx_align.core.types import MarkdownDocument
    from ppx_align.core.md import build_parsed_doc

    text = markdown_path.read_text(encoding="utf-8")
    return build_parsed_doc(MarkdownDocument(markdown=text, figures={}))


def _compute_page_precision_recall(page_dir: Path, noise_tags: list[str]):
    import pandas as pd
    from ppx_align.core.types import DocAlignment
    from ppx_bench.core.precision_recall import compute_line_precision_recall

    gold_path = page_dir / "alignment.json"
    gold_md = page_dir / "markdown" / "markdown.md"
    if not gold_path.exists() or not gold_md.exists():
        return None

    tree = pd.read_parquet(page_dir / "layout-tree.parquet", engine="fastparquet")
    gold_doc = _parsed_doc_from_markdown(gold_md)
    gold_alignment = DocAlignment.model_validate_json(gold_path.read_text())

    frames = []
    for tag in noise_tags:
        if tag == "0":
            df = compute_line_precision_recall(tree, gold_doc, gold_doc, gold_alignment, gold_alignment, "0")
            frames.append(df.assign(page=page_dir.name))
            continue
        noise_align_path = page_dir / f"alignment_{tag}.json"
        noise_md_path = page_dir / f"markdown_{tag}.md"
        if not noise_align_path.exists() or not noise_md_path.exists():
            continue
        noise_alignment = DocAlignment.model_validate_json(noise_align_path.read_text())
        noise_doc = _parsed_doc_from_markdown(noise_md_path)
        df = compute_line_precision_recall(tree, gold_doc, noise_doc, gold_alignment, noise_alignment, tag)
        df = df.assign(page=page_dir.name)
        frames.append(df)

    if not frames:
        return None
    return pd.concat(frames, ignore_index=True)


def _compute_document_precision_recall(doc_dir: Path, noise_tags: list[str], page_filter: set[str] | None = None, progress=None):
    import pandas as pd

    page_dirs = sorted(
        (d for d in doc_dir.iterdir() if d.is_dir() and (d / "layout-tree.parquet").exists()),
        key=lambda d: int(d.name) if d.name.isdigit() else d.name,
    )
    if page_filter:
        page_dirs = [d for d in page_dirs if d.name in page_filter]

    task = progress.add_task(f"{doc_dir.name}", total=len(page_dirs)) if progress else None
    frames = []
    for page_dir in page_dirs:
        if progress:
            progress.update(task, description=f"{doc_dir.name} / page {page_dir.name}")
        df = _compute_page_precision_recall(page_dir, noise_tags)
        if df is not None:
            frames.append(df)
        if progress:
            progress.advance(task)
    if not frames:
        return None
    return pd.concat(frames, ignore_index=True)


def _collect_document_noise_scores(
    doc_dir: Path,
    noise_tags: list[str],
    page_filter: set[str] | None = None,
    labels: set[str] | None = None,
):
    """For a document dir, load line scores at each (page, noise_tag) and return a concatenated DataFrame with page + noise columns."""
    import pandas as pd

    page_dirs = sorted(
        (d for d in doc_dir.iterdir() if d.is_dir() and (d / "layout-tree.parquet").exists()),
        key=lambda d: int(d.name) if d.name.isdigit() else d.name,
    )
    if page_filter:
        page_dirs = [d for d in page_dirs if d.name in page_filter]

    collected = []
    for tag in noise_tags:
        for page_dir in page_dirs:
            df = _line_scores_for_tag(page_dir, tag, labels=labels)
            if df is None:
                continue
            collected.append(df.assign(page=page_dir.name, noise=tag))
    if not collected:
        return None
    return pd.concat(collected, ignore_index=True)


def _subsample_tags(tags: list[str], max_curves: int) -> list[str]:
    if max_curves <= 0 or len(tags) <= max_curves:
        return tags
    import numpy as np
    idx = sorted(set(np.linspace(0, len(tags) - 1, max_curves).round().astype(int).tolist()))
    return [tags[i] for i in idx]


def _resolve_noise_tags(path: Path, levels: str | None) -> list[str]:
    if levels is not None:
        return sorted({_noise_tag(v) or "0" for v in _parse_noise_levels(levels)} | {"0"}, key=float)
    if (path / "layout-tree.parquet").exists():
        return _discover_noise_tags_for_page(path)
    return _discover_noise_tags_for_document(path)


@app.command(name="noise-diagrams")
def noise_diagrams_cmd(
    path: Annotated[Path, typer.Argument(help="Page or document directory")],
    levels: Annotated[Optional[str], typer.Option("--levels", "-n", help="Comma-separated noise levels (fractions or percentages). Default: auto-detect all available.")] = None,
    pages: Annotated[Optional[str], typer.Option("--pages", "-p", help="Comma-separated page names or ranges (document mode only).")] = None,
    labels: Annotated[Optional[str], typer.Option("--labels", "-l", help="Comma-separated block labels to include.")] = None,
):
    """Line-level diagrams overlapping multiple noise levels."""
    import pandas as pd
    from ppx_bench.core.diagram import save_line_noise_diagrams

    label_filter = _parse_labels(labels) if labels else None
    page_filter = _parse_pages(pages) if pages else None
    noise_tags = _resolve_noise_tags(path, levels)

    if not noise_tags:
        typer.echo(f"No alignment files found under {path}", err=True)
        raise typer.Exit(1)

    is_page = (path / "layout-tree.parquet").exists()
    if is_page:
        collected = []
        for tag in noise_tags:
            df = _line_scores_for_tag(path, tag, labels=label_filter)
            if df is None:
                continue
            collected.append(df.assign(page=path.name, noise=tag))
        line_df = pd.concat(collected, ignore_index=True) if collected else None
    else:
        line_df = _collect_document_noise_scores(path, noise_tags, page_filter=page_filter, labels=label_filter)

    if line_df is None:
        typer.echo("No line scores collected", err=True)
        raise typer.Exit(1)

    out = path / "noise_diagrams"
    subtitle = f"noise levels: {', '.join(noise_tags)}"
    save_line_noise_diagrams(line_df, out, title_prefix=path.name, subtitle=subtitle, labels=label_filter)
    typer.echo(f"Saved noise diagrams to {out}")


@app.command(name="noise-benchmark")
def noise_benchmark_cmd(
    output_dir: Annotated[Path, typer.Argument(help="Root output directory containing document subdirectories")],
    levels: Annotated[Optional[str], typer.Option("--levels", "-n", help="Comma-separated noise levels. Default: auto-detect all available across all documents.")] = None,
    pages: Annotated[Optional[str], typer.Option("--pages", "-p", help="Comma-separated page names or ranges applied to every document.")] = None,
    labels: Annotated[Optional[str], typer.Option("--labels", "-l", help="Comma-separated block labels to include.")] = None,
    min_docs: Annotated[Optional[int], typer.Option("--min-docs", help="Only include noise levels present in at least this many documents. Default: all discovered documents (strict comparability).")] = None,
    max_curves: Annotated[int, typer.Option("--max-curves", help="If more noise levels remain after filtering, evenly subsample down to this count. 0 disables.")] = 6,
):
    """Build noise diagrams for every document and an aggregate summary at output_dir/noise_benchmark."""
    import pandas as pd
    from rich.progress import Progress, BarColumn, TaskProgressColumn, TimeElapsedColumn, TextColumn
    from ppx_bench.core.diagram import save_line_noise_diagrams

    label_filter = _parse_labels(labels) if labels else None
    page_filter = _parse_pages(pages) if pages else None

    doc_dirs = sorted(d for d in output_dir.iterdir() if _is_any_document_dir(d))
    if not doc_dirs:
        typer.echo(f"No document directories found under {output_dir}", err=True)
        raise typer.Exit(1)

    doc_tags = {d: set(_discover_noise_tags_for_document(d)) for d in doc_dirs}
    if levels is not None:
        noise_tags = _resolve_noise_tags(output_dir, levels)
    else:
        all_tags = sorted({t for tags in doc_tags.values() for t in tags}, key=float)
        threshold = min_docs if min_docs is not None else len(doc_dirs)
        before = len(all_tags)
        noise_tags = [t for t in all_tags if sum(t in tags for tags in doc_tags.values()) >= threshold]
        dropped = [t for t in all_tags if t not in noise_tags]
        if dropped:
            typer.echo(f"Filtered out {len(dropped)}/{before} noise levels with < {threshold} doc coverage: {dropped}", err=True)

    if not noise_tags:
        typer.echo(f"No alignment files found under {output_dir} (after --min-docs filtering)", err=True)
        raise typer.Exit(1)

    if levels is None and max_curves > 0 and len(noise_tags) > max_curves:
        full = noise_tags
        noise_tags = _subsample_tags(noise_tags, max_curves)
        skipped = [t for t in full if t not in noise_tags]
        typer.echo(f"Subsampled {len(full)} → {len(noise_tags)} noise levels for readability; skipped: {skipped}", err=True)

    all_dfs = []
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
    ) as progress:
        task = progress.add_task("All documents", total=len(doc_dirs))
        for doc_dir in doc_dirs:
            progress.update(task, description=f"Document {doc_dir.name}")
            line_df = _collect_document_noise_scores(doc_dir, noise_tags, page_filter=page_filter, labels=label_filter)
            if line_df is None:
                progress.advance(task)
                continue
            doc_subtitle = f"noise levels: {', '.join(sorted(line_df['noise'].unique(), key=float))}"
            save_line_noise_diagrams(line_df, doc_dir / "noise_diagrams", title_prefix=doc_dir.name, subtitle=doc_subtitle, labels=label_filter)
            all_dfs.append(line_df.assign(document=doc_dir.name))
            progress.advance(task)
        progress.update(task, description="Done")

    if not all_dfs:
        typer.echo("No documents produced data", err=True)
        raise typer.Exit(1)

    bench_df = pd.concat(all_dfs, ignore_index=True)
    doc_names = [d.name for d in doc_dirs]
    subtitle_parts = [
        f"docs: {', '.join(doc_names)}" if len(doc_names) <= 6 else f"{len(doc_names)} documents",
        f"noise levels: {', '.join(sorted(bench_df['noise'].unique(), key=float))}",
    ]
    subtitle = " | ".join(subtitle_parts)

    out = output_dir / NOISE_BENCHMARK_DIR_NAME
    save_line_noise_diagrams(bench_df, out, title_prefix="benchmark (noise)", subtitle=subtitle, labels=label_filter)
    typer.echo(f"Saved noise benchmark to {out}")


@app.command(name="summary")
def summary_cmd(
    output_dir: Annotated[Path, typer.Argument(help="Root output directory containing benchmark/, noise_benchmark/, precision_recall_benchmark/")],
):
    """Print a text summary of the three benchmark parquets."""
    import pandas as pd

    bench = output_dir / BENCHMARK_DIR_NAME
    noise_bench = output_dir / NOISE_BENCHMARK_DIR_NAME
    pr_bench = output_dir / PR_BENCHMARK_DIR_NAME

    def _hdr(title):
        typer.echo("=" * 70)
        typer.echo(title)
        typer.echo("=" * 70)

    if bench.exists():
        _hdr("1. VANILLA BENCHMARK (uncorrupted alignment)")
        for name, fn in [("BLOCKS", "block_scores.parquet"), ("LINES", "line_scores.parquet")]:
            path = bench / fn
            if not path.exists():
                continue
            df = pd.read_parquet(path)
            typer.echo(f"\n--- {name} ---")
            per_doc = df.groupby("document")["score"].agg(["mean", "std", "count"]).round(3)
            typer.echo(str(per_doc))
            typer.echo(f"\ncross-doc mean of means: {per_doc['mean'].mean():.3f}")
            typer.echo(f"cross-doc std of means:  {per_doc['mean'].std(ddof=0):.3f}")
            typer.echo(f"\nby block_label (top 10 by count):")
            typer.echo(str(df.groupby("block_label")["score"].agg(["mean", "count"]).round(3).sort_values("count", ascending=False).head(10)))
        typer.echo("")

    if noise_bench.exists():
        path = noise_bench / "line_scores.parquet"
        if path.exists():
            _hdr("2. NOISE BENCHMARK (line scores by noise level)")
            nb = pd.read_parquet(path)
            typer.echo(f"\nnoise levels present: {sorted(nb['noise'].unique(), key=float)}")
            typer.echo(f"documents: {sorted(nb['document'].unique())}")
            typer.echo("\nMean line score by noise level (across all docs):")
            typer.echo(str(nb.groupby("noise")["score"].agg(["mean", "std", "count"]).round(3).sort_index(key=lambda x: x.astype(float))))
            typer.echo("\nMean line score by (document, noise):")
            pivot = nb.groupby(["document", "noise"])["score"].mean().unstack("noise")
            pivot = pivot[sorted(pivot.columns, key=float)]
            typer.echo(str(pivot.round(3)))
            typer.echo("")

    if pr_bench.exists():
        path = pr_bench / "precision_recall.parquet"
        if path.exists():
            _hdr("3. PRECISION / RECALL BENCHMARK")
            pr = pd.read_parquet(path)
            typer.echo(f"\nnoise levels: {sorted(pr['noise_level'].unique(), key=float)}")
            typer.echo(f"documents: {sorted(pr['document'].unique())}")
            typer.echo(f"total rows: {len(pr)}")
            typer.echo("\nPer noise_level summary:")
            summary = pr.groupby("noise_level").agg(
                precision_mean=("precision", "mean"),
                recall_mean=("recall", "mean"),
                block_error_rate=("is_block_error", "mean"),
                n=("line_id", "count"),
            ).round(3).sort_index(key=lambda x: x.astype(float))
            typer.echo(str(summary))
            typer.echo("\nPer document, precision at each noise:")
            pp = pr.groupby(["document", "noise_level"])["precision"].mean().unstack("noise_level")
            pp = pp[sorted(pp.columns, key=float)]
            typer.echo(str(pp.round(3)))
            typer.echo("\nPer document, block_error_rate at each noise:")
            bp = pr.groupby(["document", "noise_level"])["is_block_error"].mean().unstack("noise_level")
            bp = bp[sorted(bp.columns, key=float)]
            typer.echo(str(bp.round(3)))


@app.command(name="precision-recall")
def precision_recall_cmd(
    path: Annotated[Path, typer.Argument(help="Page or document directory")],
    levels: Annotated[Optional[str], typer.Option("--levels", "-n", help="Comma-separated noise levels (fractions or percentages). Default: auto-detect all available.")] = None,
    pages: Annotated[Optional[str], typer.Option("--pages", "-p", help="Comma-separated page names or ranges (document mode only).")] = None,
):
    """Compute precision/recall per line by comparing each noise-level alignment to the 0% gold standard."""
    from rich.progress import Progress, BarColumn, TaskProgressColumn, TimeElapsedColumn, TextColumn
    from ppx_bench.core.diagram import save_precision_recall_diagrams

    page_filter = _parse_pages(pages) if pages else None
    noise_tags = _resolve_noise_tags(path, levels)
    if not noise_tags or noise_tags == ["0"]:
        typer.echo("No noise-level alignments found to compare against the gold standard", err=True)
        raise typer.Exit(1)

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
    ) as progress:
        if (path / "layout-tree.parquet").exists():
            pr_df = _compute_page_precision_recall(path, noise_tags)
        else:
            pr_df = _compute_document_precision_recall(path, noise_tags, page_filter=page_filter, progress=progress)

    if pr_df is None or pr_df.empty:
        typer.echo("No precision/recall data collected", err=True)
        raise typer.Exit(1)

    compared_tags = sorted([t for t in noise_tags if t != "0"], key=float)
    subtitle = f"gold: 0 | noise levels: {', '.join(compared_tags)}"
    out = path / "precision_recall"
    save_precision_recall_diagrams(pr_df, out, title_prefix=path.name, subtitle=subtitle)
    typer.echo(f"Saved precision/recall diagrams to {out}")


@app.command(name="precision-recall-benchmark")
def precision_recall_benchmark_cmd(
    output_dir: Annotated[Path, typer.Argument(help="Root output directory containing document subdirectories")],
    levels: Annotated[Optional[str], typer.Option("--levels", "-n", help="Comma-separated noise levels. Default: auto-detect all available.")] = None,
    pages: Annotated[Optional[str], typer.Option("--pages", "-p", help="Comma-separated page names or ranges applied to every document.")] = None,
):
    """Build precision/recall diagrams for every document and an aggregate summary at output_dir/precision_recall_benchmark."""
    import pandas as pd
    from rich.progress import Progress, BarColumn, TaskProgressColumn, TimeElapsedColumn, TextColumn
    from ppx_bench.core.diagram import save_precision_recall_diagrams

    page_filter = _parse_pages(pages) if pages else None

    doc_dirs = sorted(d for d in output_dir.iterdir() if _is_any_document_dir(d))
    if not doc_dirs:
        typer.echo(f"No document directories found under {output_dir}", err=True)
        raise typer.Exit(1)

    noise_tags = _resolve_noise_tags(output_dir, levels) if levels is not None else sorted(
        {t for d in doc_dirs for t in _discover_noise_tags_for_document(d)}, key=float
    )
    compared_tags = [t for t in noise_tags if t != "0"]
    if not compared_tags:
        typer.echo("No noise-level alignments found to compare against the gold standard", err=True)
        raise typer.Exit(1)

    all_dfs = []
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
    ) as progress:
        task = progress.add_task("All documents", total=len(doc_dirs))
        for doc_dir in doc_dirs:
            progress.update(task, description=f"Document {doc_dir.name}")
            pr_df = _compute_document_precision_recall(doc_dir, noise_tags, page_filter=page_filter, progress=progress)
            if pr_df is None or pr_df.empty:
                progress.advance(task)
                continue
            doc_subtitle = f"gold: 0 | noise levels: {', '.join(sorted(pr_df['noise_level'].unique(), key=float))}"
            save_precision_recall_diagrams(pr_df, doc_dir / "precision_recall", title_prefix=doc_dir.name, subtitle=doc_subtitle)
            all_dfs.append(pr_df.assign(document=doc_dir.name))
            progress.advance(task)
        progress.update(task, description="Done")

    if not all_dfs:
        typer.echo("No documents produced precision/recall data", err=True)
        raise typer.Exit(1)

    bench_df = pd.concat(all_dfs, ignore_index=True)
    doc_names = [d.name for d in doc_dirs]
    subtitle_parts = [
        f"docs: {', '.join(doc_names)}" if len(doc_names) <= 6 else f"{len(doc_names)} documents",
        f"noise levels: {', '.join(sorted(bench_df['noise_level'].unique(), key=float))}",
    ]
    out = output_dir / "precision_recall_benchmark"
    save_precision_recall_diagrams(bench_df, out, title_prefix="precision-recall benchmark", subtitle=" | ".join(subtitle_parts))
    typer.echo(f"Saved precision/recall benchmark to {out}")


@app.command(name="corrupt")
def corrupt_cmd(
    path: Annotated[Path, typer.Argument(help="Page directory or document directory containing page subdirectories")],
    noise_level: Annotated[str, typer.Option("--noise-level", "-n", help="Comma-separated noise levels. Accepts fractions (0.05) or percentages (5).")],
    pages: Annotated[Optional[str], typer.Option("--pages", "-p", help="Comma-separated page names or ranges (e.g. '0,2,5-8'). Default: all pages.")] = None,
    seed: Annotated[Optional[int], typer.Option("--seed", help="RNG seed for reproducible corruption.")] = None,
):
    """Inject synthetic character-level noise into aligned markdown line spans."""
    from rich.progress import Progress, BarColumn, TaskProgressColumn, TimeElapsedColumn, TextColumn

    levels = _parse_noise_levels(noise_level)
    if not levels:
        typer.echo("No noise levels provided", err=True)
        raise typer.Exit(1)

    if _is_page_dir(path):
        _corrupt_page(path, levels, seed)
        typer.echo(f"Wrote {len(levels)} corrupted markdown file(s) to {path}")
        return

    page_filter = _parse_pages(pages) if pages else None
    page_dirs = sorted(
        (d for d in path.iterdir() if d.is_dir() and _is_page_dir(d)),
        key=lambda d: int(d.name) if d.name.isdigit() else d.name,
    )
    if page_filter:
        page_dirs = [d for d in page_dirs if d.name in page_filter]
        missing = page_filter - {d.name for d in page_dirs}
        if missing:
            typer.echo(f"Warning: pages not found: {sorted(missing)}", err=True)

    if not page_dirs:
        typer.echo(f"No page directories found under {path}", err=True)
        raise typer.Exit(1)

    total = 0
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
    ) as progress:
        task = progress.add_task("Corrupting", total=len(page_dirs))
        for page_dir in page_dirs:
            progress.update(task, description=f"Page {page_dir.name}")
            total += _corrupt_page(page_dir, levels, seed)
            progress.advance(task)

    typer.echo(f"Wrote {total} corrupted markdown file(s) across {len(page_dirs)} page(s) under {path}")


if __name__ == "__main__":
    app()
