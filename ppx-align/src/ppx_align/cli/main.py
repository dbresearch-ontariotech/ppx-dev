import logging
import warnings
# logging.disable(logging.CRITICAL)
logging.getLogger("uvicorn").setLevel(logging.INFO)
logging.getLogger("uvicorn.access").setLevel(logging.INFO)
logging.getLogger("uvicorn.error").setLevel(logging.INFO)
warnings.filterwarnings("ignore")

import typer
from pathlib import Path
from typing import Annotated, Optional

app = typer.Typer(help="Alignment and layout tree for the ppx OCR pipeline", pretty_exceptions_enable=False)


def _is_page_dir(p: Path) -> bool:
    return all((p / f).exists() for f in ("regions.parquet", "blocks.parquet", "line_tokens.parquet", "word_tokens.parquet"))


def _build_layout_tree_for_page(page_dir: Path, overwrite: bool):
    import pandas as pd
    from ppx_align.core.storage import load
    from ppx_align.core.layout import build_layout_tree

    dest = page_dir / "layout-tree.parquet"
    if dest.exists() and not overwrite:
        typer.echo(f"  Skipping {dest} (already exists)")
        return

    vl, _ = load(str(page_dir))
    tree = build_layout_tree(vl)
    tree.to_parquet(dest, engine="fastparquet", index=False)
    typer.echo(f"  Saved {dest} ({dest.stat().st_size:,} B, {len(tree)} nodes)")


@app.command(name="build-layout-tree")
def build_layout_tree_cmd(
    path: Annotated[Path, typer.Argument(help="Page directory or document directory containing page subdirectories")],
    overwrite: Annotated[bool, typer.Option("--overwrite", help="Overwrite existing output")] = False,
):
    """Build the layout tree and save as layout-tree.parquet."""
    if _is_page_dir(path):
        _build_layout_tree_for_page(path, overwrite)
    else:
        page_dirs = sorted((d for d in path.iterdir() if d.is_dir() and _is_page_dir(d)), key=lambda d: int(d.name))
        if not page_dirs:
            typer.echo(f"No page directories found under {path}", err=True)
            raise typer.Exit(1)
        for page_dir in page_dirs:
            typer.echo(f"[{page_dir.name}]")
            _build_layout_tree_for_page(page_dir, overwrite)


@app.command(name="build")
def build_cmd(
    output: Path = typer.Argument(..., help="Document output directory containing page subdirectories"),
    page: Optional[int] = typer.Option(None, "--page", help="Process only this page number"),
    blocks_only: bool = typer.Option(False, "--blocks-only", help="Align blocks only, skip line alignment"),
    tokenizer_name: str = typer.Option("treebank", "--tokenizer", help="Tokenizer to use: 'treebank' or a pretrained model name (e.g. google-bert/bert-base-chinese)"),
):
    """Build DocAlignment for all pages, or a single page with --page."""
    from rich.progress import Progress, BarColumn, TaskProgressColumn, TimeElapsedColumn, TextColumn
    from ppx_align.core.storage import load
    from ppx_align.core.layout import build_layout_tree
    from ppx_align.core.md import build_parsed_doc
    from ppx_align.core.align import align_tree
    from ppx_align.core.tokenizers import TreebankTokenizer, PretrainedAutoTokenizer
    tokenizer = TreebankTokenizer() if tokenizer_name == "treebank" else PretrainedAutoTokenizer(tokenizer_name)

    all_pages = sorted((d for d in output.iterdir() if d.is_dir() and _is_page_dir(d)), key=lambda d: int(d.name))
    if not all_pages:
        typer.echo(f"No page directories found under {output}", err=True)
        raise typer.Exit(1)

    if page is not None:
        page_dir = output / str(page)
        if not _is_page_dir(page_dir):
            typer.echo(f"Page {page} not found or incomplete under {output}", err=True)
            raise typer.Exit(1)
        pages = [page_dir]
    else:
        pages = all_pages

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
    ) as progress:
        task = progress.add_task("Building alignments", total=len(pages))
        for page_dir in pages:
            progress.update(task, description=f"Page {page_dir.name}")
            vl, md_doc = load(str(page_dir))
            tree = build_layout_tree(vl)
            doc = build_parsed_doc(md_doc, tokenizer=tokenizer)
            alignment = align_tree(tree, doc, blocks_only=blocks_only)
            dest = page_dir / "alignment.json"
            dest.write_text(alignment.model_dump_json(indent=2))
            scores = (
                [t.score for t in alignment.block_alignments.values()] +
                [t.score for t in alignment.line_alignments.values()]
            )
            avg_score = sum(scores) / len(scores) if scores else 0.0
            progress.update(task, description=f"Page {page_dir.name} | avg score: {avg_score:.3f}")
            progress.advance(task)


@app.command(name="serve")
def serve_cmd(
    output: Path = typer.Argument(..., help="Document output directory"),
    port: Annotated[int, typer.Option("--port", help="Port to listen on")] = 8000,
    slow: Annotated[bool, typer.Option("--slow", help="Add random 0.5–2s delay to all responses (simulates slow connection)")] = False,
):
    """Start the web server."""
    import os
    import uvicorn
    os.environ["PPX_OUTPUT"] = str(output.resolve())
    if slow:
        os.environ["PPX_SLOW"] = "1"
    uvicorn.run("ppx_align.web:app", host="0.0.0.0", port=port, log_level="info", reload=True)


if __name__ == "__main__":
    app()
