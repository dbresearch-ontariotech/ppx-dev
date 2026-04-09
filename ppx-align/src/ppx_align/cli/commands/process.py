import typer
from pathlib import Path
from typing import Annotated

app = typer.Typer()


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
    from ppx_align.core.layout import align_tree, get_largest_region

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
def align_layout_tree_cmd(
    path: Annotated[Path, typer.Argument(help="Page directory or document directory containing page subdirectories")],
    root_id: Annotated[str, typer.Option("--root-id", help="Root node id to align from (default: largest region)")] = None,
    overwrite: Annotated[bool, typer.Option("--overwrite", help="Overwrite existing output")] = False,
):
    """Align the layout tree to the markdown text and save as alignment.json."""
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
