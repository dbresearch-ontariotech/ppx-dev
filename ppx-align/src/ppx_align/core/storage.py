from __future__ import annotations
from pathlib import Path
from typing import Generator
import numpy as np
import pandas as pd
from PIL import Image
from .types import MarkdownDocument, VisualLayers


def _load_parquet(dest: Path) -> pd.DataFrame:
    return pd.read_parquet(dest, engine="fastparquet").set_index('index')


def _load_markdown(markdown_dir: Path) -> MarkdownDocument:
    markdown = (markdown_dir / "markdown.md").read_text(encoding="utf-8")
    figures = {}
    for p in markdown_dir.rglob("*"):
        if p.is_file() and p.name != "markdown.md":
            key = str(p.relative_to(markdown_dir))
            figures[key] = np.array(Image.open(p).convert("RGB"))
    return MarkdownDocument(markdown=markdown, figures=figures)


def load(path: str) -> tuple[VisualLayers, MarkdownDocument]:
    page_dir = Path(path)
    page_index = int(page_dir.name)

    np_page = np.array(Image.open(page_dir / "np_page.png").convert("RGB"))
    line_tokens = _load_parquet(page_dir / "line_tokens.parquet")
    word_tokens = _load_parquet(page_dir / "word_tokens.parquet")
    regions = _load_parquet(page_dir / "regions.parquet")
    layout = _load_parquet(page_dir / "layout.parquet")
    blocks = _load_parquet(page_dir / "blocks.parquet")
    formulas = _load_parquet(page_dir / "formulas.parquet")

    vl = VisualLayers(
        np_page=np_page,
        page_index=page_index,
        regions=regions,  # type: ignore
        layout=layout,  # type: ignore
        blocks=blocks,  # type: ignore
        formulas=formulas,  # type: ignore
        line_tokens=line_tokens,  # type: ignore
        word_tokens=word_tokens,  # type: ignore
    )
    md = _load_markdown(page_dir / "markdown")
    return vl, md
