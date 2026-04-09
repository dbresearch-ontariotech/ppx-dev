from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Generator
import numpy as np
import pandas as pd
from PIL import Image
from .types import MarkdownDocument, VisualLayers


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


def _write_markdown(md: MarkdownDocument, markdown_dir: Path) -> Generator[WriteStatus, None, None]:
    markdown_dir.mkdir(parents=True, exist_ok=True)
    md_file = markdown_dir / "markdown.md"
    md_file.write_text(md.markdown, encoding="utf-8")
    yield WriteStatus(path=md_file, size=md_file.stat().st_size, message="markdown/markdown.md")
    for filename, arr in md.figures.items():
        s = _write_image(arr, markdown_dir / filename)
        yield WriteStatus(path=s.path, size=s.size, message=f"markdown/{filename}")


def store(
    page_dir: Path,
    layers: VisualLayers,
    markdown_document: MarkdownDocument,
) -> Generator[WriteStatus, None, None]:
    page_dir.mkdir(parents=True, exist_ok=True)

    yield _write_image(layers.np_page, page_dir / "np_page.png")
    yield _write_parquet(layers.line_tokens, page_dir / "line_tokens.parquet", "line_tokens.parquet")
    yield _write_parquet(layers.word_tokens, page_dir / "word_tokens.parquet", "word_tokens.parquet")
    yield _write_parquet(layers.regions, page_dir / "regions.parquet", "regions.parquet")
    yield _write_parquet(layers.layout, page_dir / "layout.parquet", "layout.parquet")
    yield _write_parquet(layers.blocks, page_dir / "blocks.parquet", "blocks.parquet")
    yield _write_parquet(layers.formulas, page_dir / "formulas.parquet", "formulas.parquet")
    yield from _write_markdown(markdown_document, page_dir / "markdown")
