from __future__ import annotations

import mimetypes
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from ppx.web.state import get_data_root
from ppx.core.storage import _load_parquet

router = APIRouter()


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _is_page_dir(p: Path) -> bool:
    return all(
        (p / f).exists()
        for f in ("regions.parquet", "blocks.parquet", "line_tokens.parquet", "word_tokens.parquet")
    )


def _page_dirs(doc_dir: Path) -> list[Path]:
    dirs = sorted(
        (d for d in doc_dir.iterdir() if d.is_dir() and _is_page_dir(d)),
        key=lambda d: int(d.name),
    )
    return dirs


def _resolve_doc(filename: str) -> Path:
    doc_dir = get_data_root() / filename
    if not doc_dir.is_dir():
        raise HTTPException(status_code=404, detail=f"Document not found: {filename}")
    return doc_dir


def _resolve_page(filename: str, page_index: int) -> Path:
    doc_dir = _resolve_doc(filename)
    pages = _page_dirs(doc_dir)
    if page_index < 0 or page_index >= len(pages):
        raise HTTPException(status_code=404, detail=f"Page index out of range: {page_index}")
    return pages[page_index]


def _infer_media_type(suffix: str) -> str:
    mime, _ = mimetypes.guess_type(f"file{suffix}")
    return mime or "application/octet-stream"


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class DocumentInfo(BaseModel):
    filename: str
    page_count: int


class DocumentsResponse(BaseModel):
    documents: list[DocumentInfo]


class PageInfo(BaseModel):
    page_index: int
    width: int
    height: int


class PagesResponse(BaseModel):
    filename: str
    pages: list[PageInfo]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/documents", response_model=DocumentsResponse)
def list_documents() -> DocumentsResponse:
    data_root = get_data_root()
    docs = []
    for d in sorted(data_root.iterdir()):
        if not d.is_dir():
            continue
        page_count = sum(1 for p in d.iterdir() if p.is_dir() and _is_page_dir(p))
        docs.append(DocumentInfo(filename=d.name, page_count=page_count))
    return DocumentsResponse(documents=docs)


@router.get("/documents/{filename}/pages", response_model=PagesResponse)
def list_pages(filename: str) -> PagesResponse:
    from PIL import Image

    doc_dir = _resolve_doc(filename)
    pages = []
    for i, page_dir in enumerate(_page_dirs(doc_dir)):
        img_path = page_dir / "np_page.png"
        width, height = Image.open(img_path).size
        pages.append(PageInfo(page_index=i, width=width, height=height))
    return PagesResponse(filename=filename, pages=pages)


@router.get("/documents/{filename}/pages/{page_index}/image")
def get_page_image(filename: str, page_index: int) -> FileResponse:
    page_dir = _resolve_page(filename, page_index)
    img_path = page_dir / "np_page.png"
    if not img_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(img_path, media_type="image/png")


@router.get("/documents/{filename}/pages/{page_index}/markdown/index.md")
def get_markdown_index(filename: str, page_index: int) -> FileResponse:
    page_dir = _resolve_page(filename, page_index)
    md_path = page_dir / "markdown" / "markdown.md"
    if not md_path.exists():
        raise HTTPException(status_code=404, detail="Markdown not found")
    return FileResponse(md_path, media_type="text/markdown")


@router.get("/documents/{filename}/pages/{page_index}/markdown/{resource:path}")
def get_markdown_resource(filename: str, page_index: int, resource: str) -> FileResponse:
    page_dir = _resolve_page(filename, page_index)
    markdown_dir = page_dir / "markdown"
    resolved = (markdown_dir / resource).resolve()
    # Guard against path traversal
    if not str(resolved).startswith(str(markdown_dir.resolve()) + "/"):
        raise HTTPException(status_code=403, detail="Access denied")
    if not resolved.exists():
        raise HTTPException(status_code=404, detail="Resource not found")
    media_type = _infer_media_type(resolved.suffix)
    return FileResponse(resolved, media_type=media_type)


@router.get("/documents/{filename}/pages/{page_index}/visual_tokens")
def get_visual_tokens(filename: str, page_index: int) -> list[dict]:
    page_dir = _resolve_page(filename, page_index)
    layers = [
        ("regions", page_dir / "regions.parquet"),
        ("blocks", page_dir / "blocks.parquet"),
        ("line_tokens", page_dir / "line_tokens.parquet"),
        ("word_tokens", page_dir / "word_tokens.parquet"),
    ]
    dfs = []
    for layer_name, parquet_path in layers:
        df = _load_parquet(parquet_path)
        df = df.copy()
        df["layer"] = layer_name
        dfs.append(df)
    combined = pd.concat(dfs)
    return combined.to_dict(orient="records")


@router.get("/documents/{filename}/pages/{page_index}/layout_tree")
def get_layout_tree(filename: str, page_index: int) -> list[dict]:
    page_dir = _resolve_page(filename, page_index)
    tree_path = page_dir / "layout-tree.parquet"
    if not tree_path.exists():
        raise HTTPException(status_code=404, detail="Layout tree not found")
    tree = pd.read_parquet(tree_path, engine="fastparquet")
    # Replace NaN parent_id with None
    if "parent_id" in tree.columns:
        tree["parent_id"] = tree["parent_id"].where(tree["parent_id"].notna(), other=None)
    records = tree.to_dict(orient="records")
    return records


@router.get("/documents/{filename}/pages/{page_index}/alignment")
def get_alignment(filename: str, page_index: int) -> dict:
    from ppx.core.layout.layout_tree import TreeAlignment

    page_dir = _resolve_page(filename, page_index)
    alignment_path = page_dir / "alignment.json"
    if not alignment_path.exists():
        raise HTTPException(status_code=404, detail="Alignment not found")
    alignment = TreeAlignment.model_validate_json(alignment_path.read_text())
    return alignment.model_dump()
