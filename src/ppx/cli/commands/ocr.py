import typer
from pathlib import Path
from typing import Annotated

app = typer.Typer()

@app.command()
def run(
    pdf_file: Annotated[Path, typer.Argument(help="PDF file to process")],
    output: Annotated[Path, typer.Option("-o", "--output", help="Output directory")] = Path("."),
    overwrite: Annotated[bool, typer.Option("--overwrite", help="Overwrite existing output")] = False,
):
    """Run OCR and layout analysis on a PDF file, storing results to disk."""
    from ppx.core.helpers import get_page_tensors
    from ppx.core.ocr import get_visual_tokens, get_structv3
    from ppx.core.storage import store

    doc_dir = output / pdf_file.stem
    typer.echo(f"Input:  {pdf_file}")
    typer.echo(f"Output: {doc_dir}")

    doc = get_page_tensors(pdf_file)
    n = len(doc.pages)
    typer.echo(f"Pages:  {n}")

    for i, np_page in enumerate(doc.pages):
        page_dir = doc_dir / str(i)
        if page_dir.exists() and not overwrite:
            typer.echo(f"\n[page {i}/{n - 1}]")
            typer.echo("  Skipping (exists)")
            continue

        typer.echo(f"\n[page {i}/{n - 1}]")

        typer.echo("  Running OCR ...")
        vtl = get_visual_tokens(np_page, page_index=i)

        typer.echo("  Running layout analysis ...")
        ll, md = get_structv3(np_page, page_index=i)

        typer.echo("  Storing ...")
        for status in store(page_dir, vtl, ll, md):
            typer.echo(f"    {status.message}  ({status.size:,} B)")

    typer.echo("\nDone.")

@app.command(name="build-layout-tree")
def BuildLayoutTreeCommand(
    path: Annotated[Path, typer.Argument(help="Page directory containing parquet files")],
    overwrite: Annotated[bool, typer.Option("--overwrite", help="Overwrite existing output")] = False,
):
    """Build the layout tree from a page directory and save as layout-tree.parquet."""
    import pandas as pd
    from ppx.core.storage import _load_parquet
    from ppx.core.layout.layout_tree import build_layout_tree

    dest = path / "layout-tree.parquet"
    if dest.exists() and not overwrite:
        typer.echo(f"Skipping {dest} (already exists)")
        return

    regions = _load_parquet(path / "regions.parquet")
    blocks  = _load_parquet(path / "blocks.parquet")
    lines   = _load_parquet(path / "line_tokens.parquet")
    words   = _load_parquet(path / "word_tokens.parquet")

    tree = build_layout_tree(regions, blocks, lines, words)
    tree.to_parquet(dest, engine="fastparquet", index=False)
    typer.echo(f"Saved {dest} ({dest.stat().st_size:,} B, {len(tree)} nodes)")