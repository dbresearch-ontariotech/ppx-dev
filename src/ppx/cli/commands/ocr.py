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

def _is_page_dir(p: Path) -> bool:
    return all((p / f).exists() for f in ("regions.parquet", "blocks.parquet", "line_tokens.parquet", "word_tokens.parquet"))


def _build_layout_tree_for_page(page_dir: Path, overwrite: bool):
    from ppx.core.storage import _load_parquet
    from ppx.core.layout.layout_tree import build_layout_tree

    dest = page_dir / "layout-tree.parquet"
    if dest.exists() and not overwrite:
        typer.echo(f"  Skipping {dest} (already exists)")
        return

    regions = _load_parquet(page_dir / "regions.parquet")
    blocks  = _load_parquet(page_dir / "blocks.parquet")
    lines   = _load_parquet(page_dir / "line_tokens.parquet")
    words   = _load_parquet(page_dir / "word_tokens.parquet")

    tree = build_layout_tree(regions, blocks, lines, words)
    tree.to_parquet(dest, engine="fastparquet", index=False)
    typer.echo(f"  Saved {dest} ({dest.stat().st_size:,} B, {len(tree)} nodes)")


@app.command(name="build-layout-tree")
def BuildLayoutTreeCommand(
    path: Annotated[Path, typer.Argument(help="Page directory or document directory containing page subdirectories")],
    overwrite: Annotated[bool, typer.Option("--overwrite", help="Overwrite existing output")] = False,
):
    """Build the layout tree and save as layout-tree.parquet.

    PATH can be a single page directory (containing parquet files directly) or a
    document directory whose subdirectories are page directories.
    """
    if _is_page_dir(path):
        _build_layout_tree_for_page(path, overwrite)
    else:
        page_dirs = sorted(d for d in path.iterdir() if d.is_dir() and _is_page_dir(d))
        if not page_dirs:
            typer.echo(f"No page directories found under {path}", err=True)
            raise typer.Exit(1)
        for page_dir in page_dirs:
            typer.echo(f"[{page_dir.name}]")
            _build_layout_tree_for_page(page_dir, overwrite)

def _is_align_page_dir(p: Path) -> bool:
    return (p / "layout-tree.parquet").exists() and (p / "markdown" / "markdown.md").exists()


def _align_layout_tree_for_page(page_dir: Path, root_id: str | None, overwrite: bool):
    import pandas as pd
    from ppx.core.layout.layout_tree import align_tree, get_largest_region

    dest = page_dir / "alignment.json"
    if dest.exists() and not overwrite:
        typer.echo(f"  Skipping {dest} (already exists)")
        return

    tree = pd.read_parquet(page_dir / "layout-tree.parquet", engine="fastparquet")
    text = (page_dir / "markdown" / "markdown.md").read_text(encoding="utf-8")

    effective_root_id = root_id if root_id is not None else get_largest_region(tree)
    typer.echo(f"  root_id: {effective_root_id}")

    if effective_root_id not in tree["node_id"].values:
        typer.echo(f"  Error: node_id '{effective_root_id}' not found in layout tree.", err=True)
        return

    alignment = align_tree(tree, effective_root_id, text)

    dest.write_text(alignment.model_dump_json(indent=2), encoding="utf-8")
    typer.echo(f"  Saved {dest} ({dest.stat().st_size:,} B)")


@app.command(name="align-layout-tree")
def AlignLayoutTreeCommand(
    path: Annotated[Path, typer.Argument(help="Page directory or document directory containing page subdirectories")],
    root_id: Annotated[str, typer.Option("--root-id", help="Root node id to align from (default: largest region)")] = None,
    overwrite: Annotated[bool, typer.Option("--overwrite", help="Overwrite existing output")] = False,
):
    """Align the layout tree to the markdown text and save as alignment.json.

    PATH can be a single page directory (containing layout-tree.parquet) or a
    document directory whose subdirectories are page directories.
    """
    if _is_align_page_dir(path):
        _align_layout_tree_for_page(path, root_id, overwrite)
    else:
        page_dirs = sorted(d for d in path.iterdir() if d.is_dir() and _is_align_page_dir(d))
        if not page_dirs:
            typer.echo(f"No page directories found under {path}", err=True)
            raise typer.Exit(1)
        for page_dir in page_dirs:
            typer.echo(f"[{page_dir.name}]")
            _align_layout_tree_for_page(page_dir, root_id, overwrite)