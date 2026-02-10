from pathlib import Path
from typing import Optional

import struct

import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

router = APIRouter()

# Set by app.py at startup
data_dir: Path = Path(".")


def get_page_dir(document: str, page: int) -> Path:
    page_dir = data_dir / document / str(page)
    if not page_dir.is_dir():
        raise HTTPException(404, detail=f"Page not found: {document}/{page}")
    return page_dir


def read_parquet(path: Path, query: Optional[str] = None) -> dict:
    if not path.exists():
        raise HTTPException(404, detail=f"File not found: {path.name}")
    df = pd.read_parquet(path)
    if query:
        try:
            df = df.query(query)
        except Exception as e:
            raise HTTPException(400, detail=f"Invalid query expression: {e}")
    return df.to_dict(orient="split")


@router.get("/")
def list_documents():
    return sorted(
        d.name for d in data_dir.iterdir() if d.is_dir()
    )


@router.get("/{document}/pages")
def list_pages(document: str):
    doc_dir = data_dir / document
    if not doc_dir.is_dir():
        raise HTTPException(404, detail=f"Document not found: {document}")
    pages = sorted(
        int(d.name) for d in doc_dir.iterdir() if d.is_dir() and d.name.isdigit()
    )
    return pages


@router.get("/{document}/pages/{page}/page.png")
def get_page_image(document: str, page: int):
    page_dir = get_page_dir(document, page)
    img = page_dir / "page.png"
    if not img.exists():
        raise HTTPException(404, detail="page.png not found")
    return FileResponse(img, media_type="image/png")


@router.get("/{document}/pages/{page}/page.png/info")
def get_page_image_info(document: str, page: int):
    page_dir = get_page_dir(document, page)
    img_path = page_dir / "page.png"
    if not img_path.exists():
        raise HTTPException(404, detail="page.png not found")
    # Read width/height from PNG IHDR chunk (bytes 16-23)
    with open(img_path, "rb") as f:
        f.seek(16)
        width, height = struct.unpack(">II", f.read(8))
    return {"width": width, "height": height}


@router.get("/{document}/pages/{page}/imgs/{name:path}")
def get_extracted_image(document: str, page: int, name: str):
    page_dir = get_page_dir(document, page)
    img = page_dir / "markdown_output" / "imgs" / name
    if not img.exists():
        raise HTTPException(404, detail=f"Image not found: {name}")
    suffix = img.suffix.lower()
    media = "image/jpeg" if suffix in (".jpg", ".jpeg") else "image/png"
    return FileResponse(img, media_type=media)


@router.get("/{document}/pages/{page}/ocr/texts")
def get_ocr_texts(document: str, page: int, q: Optional[str] = Query(None)):
    page_dir = get_page_dir(document, page)
    return read_parquet(page_dir / "ocr_texts.parquet", q)


@router.get("/{document}/pages/{page}/ocr/words")
def get_ocr_words(document: str, page: int, q: Optional[str] = Query(None)):
    page_dir = get_page_dir(document, page)
    return read_parquet(page_dir / "ocr_words.parquet", q)


@router.get("/{document}/pages/{page}/structv3/layout")
def get_structv3_layout(document: str, page: int, q: Optional[str] = Query(None)):
    page_dir = get_page_dir(document, page)
    return read_parquet(page_dir / "structv3_layout.parquet", q)


@router.get("/{document}/pages/{page}/markdown")
def get_markdown(document: str, page: int):
    page_dir = get_page_dir(document, page)
    md_path = page_dir / "markdown_output" / "markdown.md"
    if not md_path.exists():
        raise HTTPException(404, detail="markdown.md not found")
    return {"markdown": md_path.read_text()}
