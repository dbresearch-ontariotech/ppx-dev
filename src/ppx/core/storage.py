from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Generator
import numpy as np
import pandas as pd
from PIL import Image
from .types import LayoutLayers, MarkdownDocument, VisualTokenLayers


@dataclass
class WriteStatus:
    path: Path
    size: int
    message: str


def _write_image(arr: np.ndarray, dest: Path) -> WriteStatus:
    dest.parent.mkdir(parents=True, exist_ok=True)
    fmt = "JPEG" if dest.suffix.lower() in (".jpg", ".jpeg") else "PNG"
    Image.fromarray(arr.astype(np.uint8), mode="RGB").save(dest, format=fmt)
    return WriteStatus(path=dest, size=dest.stat().st_size, message=dest.name)


def _write_parquet(df: pd.DataFrame, dest: Path, label: str) -> WriteStatus:
    df.reset_index().to_parquet(dest, engine="fastparquet")
    return WriteStatus(path=dest, size=dest.stat().st_size, message=label)

def _load_parquet(dest: Path) -> pd.DataFrame:
    return pd.read_parquet(dest, engine="fastparquet").set_index('index')

def _write_markdown(md: MarkdownDocument, markdown_dir: Path) -> Generator[WriteStatus, None, None]:
    markdown_dir.mkdir(parents=True, exist_ok=True)
    md_file = markdown_dir / "markdown.md"
    md_file.write_text(md.markdown, encoding="utf-8")
    yield WriteStatus(path=md_file, size=md_file.stat().st_size, message="markdown/markdown.md")
    for filename, arr in md.figures.items():
        s = _write_image(arr, markdown_dir / filename)
        yield WriteStatus(path=s.path, size=s.size, message=f"markdown/{filename}")


def _load_markdown(markdown_dir: Path) -> MarkdownDocument:
    markdown = (markdown_dir / "markdown.md").read_text(encoding="utf-8")
    figures = {}
    for p in markdown_dir.rglob("*"):
        if p.is_file() and p.name != "markdown.md":
            key = str(p.relative_to(markdown_dir))
            figures[key] = np.array(Image.open(p).convert("RGB"))
    return MarkdownDocument(markdown=markdown, figures=figures)


def store(
    page_dir: Path,
    visual_token_layers: VisualTokenLayers,
    layout_layers: LayoutLayers,
    markdown_document: MarkdownDocument,
) -> Generator[WriteStatus, None, None]:
    if visual_token_layers.page_index != layout_layers.page_index:
        raise ValueError(
            f"page_index mismatch: visual_token_layer={visual_token_layers.page_index}, "
            f"layout_layers={layout_layers.page_index}"
        )

    page_dir.mkdir(parents=True, exist_ok=True)

    yield _write_image(visual_token_layers.np_page, page_dir / "np_page.png")
    yield _write_parquet(visual_token_layers.line_tokens, page_dir / "line_tokens.parquet", "line_tokens.parquet")
    yield _write_parquet(visual_token_layers.word_tokens, page_dir / "word_tokens.parquet", "word_tokens.parquet")
    yield _write_parquet(layout_layers.regions, page_dir / "regions.parquet", "regions.parquet")
    yield _write_parquet(layout_layers.layout, page_dir / "layout.parquet", "layout.parquet")
    yield _write_parquet(layout_layers.blocks, page_dir / "blocks.parquet", "blocks.parquet")
    yield _write_parquet(layout_layers.formulas, page_dir / "formulas.parquet", "formulas.parquet")
    yield from _write_markdown(markdown_document, page_dir / "markdown")


def load(path: Path) -> tuple[VisualTokenLayers, LayoutLayers, MarkdownDocument]:
    page_dir = Path(path)
    page_index = int(page_dir.name)

    np_page = np.array(Image.open(page_dir / "np_page.png").convert("RGB"))
    line_tokens = _load_parquet(page_dir / "line_tokens.parquet")
    word_tokens = _load_parquet(page_dir / "word_tokens.parquet")
    regions = _load_parquet(page_dir / "regions.parquet")
    layout = _load_parquet(page_dir / "layout.parquet")
    blocks = _load_parquet(page_dir / "blocks.parquet")
    formulas = _load_parquet(page_dir / "formulas.parquet")

    vtl = VisualTokenLayers(
        np_page=np_page,
        page_index=page_index,
        line_tokens=line_tokens,
        word_tokens=word_tokens,
    )
    ll = LayoutLayers(
        np_page=np_page,
        page_index=page_index,
        regions=regions,
        layout=layout,
        blocks=blocks,
        formulas=formulas,
    )
    md = _load_markdown(page_dir / "markdown")
    return vtl, ll, md

def load_bboxes(page_dir: Path, *names: str) -> pd.DataFrame:
    dataframes = []
    for name in names:
        df = _load_parquet(page_dir / f"{name}.parquet")
        dataframes.append(df[["x0", "y0", "x1", "y1"]])
    return pd.concat(dataframes, axis=0)