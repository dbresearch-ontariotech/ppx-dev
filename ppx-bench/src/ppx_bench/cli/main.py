import typer
from pathlib import Path
from typing import Annotated, Optional

app = typer.Typer(help="Benchmarking for the ppx OCR pipeline.", pretty_exceptions_enable=False)


@app.callback()
def main():
    pass


def _is_page_dir(p: Path) -> bool:
    return (p / "layout-tree.parquet").exists() and (p / "alignment.json").exists()


def _process_page(page_dir: Path):
    import pandas as pd
    from ppx_align.core.types import DocAlignment
    from ppx_bench.core.diagram import compute_block_scores, compute_line_scores, save_diagrams

    tree = pd.read_parquet(page_dir / "layout-tree.parquet", engine="fastparquet")
    doc_alignment = DocAlignment.model_validate_json((page_dir / "alignment.json").read_text())

    block_df = compute_block_scores(tree, doc_alignment.block_alignments)
    line_df = compute_line_scores(tree, doc_alignment.line_alignments)

    save_diagrams(block_df, line_df, page_dir / "diagrams", title_prefix=f"Page {page_dir.name}")
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


@app.command(name="diagrams")
def create_diagrams_cmd(
    path: Annotated[Path, typer.Argument(help="Page directory or document directory containing page subdirectories")],
    pages: Annotated[Optional[str], typer.Option("--pages", "-p", help="Comma-separated page names or ranges (e.g. '0,2,5-8'). Default: all pages.")] = None,
):
    """Create diagrams for block and line score distributions."""
    import pandas as pd
    from rich.progress import Progress, BarColumn, TaskProgressColumn, TimeElapsedColumn, TextColumn
    from ppx_bench.core.diagram import save_diagrams

    if _is_page_dir(path):
        _process_page(path)
        typer.echo(f"Saved diagrams to {path / 'diagrams'}")
        return

    page_dirs = sorted(
        (d for d in path.iterdir() if d.is_dir() and _is_page_dir(d)),
        key=lambda d: int(d.name) if d.name.isdigit() else d.name,
    )
    if pages:
        selected = _parse_pages(pages)
        page_dirs = [d for d in page_dirs if d.name in selected]
        missing = selected - {d.name for d in page_dirs}
        if missing:
            typer.echo(f"Warning: pages not found: {sorted(missing)}", err=True)

    if not page_dirs:
        typer.echo(f"No page directories found under {path}", err=True)
        raise typer.Exit(1)

    all_blocks = []
    all_lines = []
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
    ) as progress:
        task = progress.add_task("Building diagrams", total=len(page_dirs))
        for page_dir in page_dirs:
            progress.update(task, description=f"Page {page_dir.name}")
            block_df, line_df = _process_page(page_dir)
            block_df = block_df.assign(page=page_dir.name)
            line_df = line_df.assign(page=page_dir.name)
            all_blocks.append(block_df)
            all_lines.append(line_df)
            progress.advance(task)

    doc_block = pd.concat(all_blocks, ignore_index=True)
    doc_line = pd.concat(all_lines, ignore_index=True)
    page_names = [d.name for d in page_dirs]
    subtitle = f"pages: {', '.join(page_names)}" if len(page_names) <= 10 else f"{len(page_names)} pages: {page_names[0]}…{page_names[-1]}"
    save_diagrams(doc_block, doc_line, path / "diagrams", title_prefix=path.name, subtitle=subtitle)
    typer.echo(f"Saved document summary to {path / 'diagrams'}")


if __name__ == "__main__":
    app()
