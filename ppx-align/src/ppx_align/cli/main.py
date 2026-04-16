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


def _normalize_noise(value: float) -> float:
    val = value / 100.0 if value > 1.0 else value
    if not 0.0 <= val <= 1.0:
        raise typer.BadParameter(f"noise must be in [0, 1] or [1, 100]: got {value}")
    return val


def _parse_noise_spec(spec: str) -> list[float]:
    levels = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        levels.append(_normalize_noise(float(part)))
    return sorted(set(levels))


@app.command(name="build")
def build_cmd(
    output: Path = typer.Argument(..., help="Document output directory containing page subdirectories"),
    page: Optional[int] = typer.Option(None, "--page", help="Process only this page number"),
    blocks_only: bool = typer.Option(False, "--blocks-only", help="Align blocks only, skip line alignment"),
    markdown: Optional[Path] = typer.Option(None, "--markdown", help="Override markdown source path (single page only)"),
    save: Optional[Path] = typer.Option(None, "--save", help="Override alignment output path (single page only)"),
    noise: Optional[str] = typer.Option(None, "--noise", help="Comma-separated noise levels (e.g. '0.01,0.02,0.05' or '1,2,5'). Uses markdown_{level}.md and saves alignment_{level}.json per page."),
    gpu: Optional[int] = typer.Option(None, "--gpu", help="CUDA device index to use (0..N-1). Defaults to GPU 0."),
):
    """Build DocAlignment for all pages, or a single page with --page."""
    if gpu is not None:
        import os
        os.environ["CUDA_VISIBLE_DEVICES"] = str(gpu)

    from rich.progress import Progress, BarColumn, TaskProgressColumn, TimeElapsedColumn, TextColumn
    from ppx_align.core.storage import load
    from ppx_align.core.layout import build_layout_tree
    from ppx_align.core.md import build_parsed_doc
    from ppx_align.core.align import align_tree

    if noise is not None and (markdown is not None or save is not None):
        typer.echo("--noise cannot be combined with --markdown or --save", err=True)
        raise typer.Exit(1)
    if (markdown is not None or save is not None) and page is None:
        typer.echo("--markdown / --save require --page", err=True)
        raise typer.Exit(1)

    noise_fracs = _parse_noise_spec(noise) if noise else []
    noise_tags: list[str | None] = [f"{f:g}" for f in noise_fracs] if noise_fracs else [None]

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

    total_work = len(pages) * len(noise_tags)
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
    ) as progress:
        task = progress.add_task("Building alignments", total=total_work)
        for noise_tag in noise_tags:
            for page_dir in pages:
                label = f"noise={noise_tag} " if noise_tag else ""
                progress.update(task, description=f"{label}Page {page_dir.name}")

                if noise_tag is not None:
                    md_src = page_dir / f"markdown_{noise_tag}.md"
                    dest = page_dir / f"alignment_{noise_tag}.json"
                    if not md_src.exists():
                        typer.echo(f"  skipping {page_dir.name}: {md_src.name} missing", err=True)
                        progress.advance(task)
                        continue
                else:
                    md_src = markdown
                    dest = save if save is not None else page_dir / "alignment.json"

                vl, md_doc = load(str(page_dir))
                if md_src is not None:
                    md_doc.markdown = Path(md_src).read_text(encoding="utf-8")
                tree = build_layout_tree(vl)
                doc = build_parsed_doc(md_doc)
                alignment = align_tree(tree, doc, blocks_only=blocks_only)
                dest.write_text(alignment.model_dump_json(indent=2))
                scores = (
                    [t.score for t in alignment.block_alignments.values()] +
                    [t.score for t in alignment.line_alignments.values()]
                )
                avg_score = sum(scores) / len(scores) if scores else 0.0
                progress.update(task, description=f"{label}Page {page_dir.name} | avg: {avg_score:.3f}")
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
