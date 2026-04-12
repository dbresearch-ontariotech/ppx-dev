import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse

app = FastAPI()


def _output() -> Path:
    val = os.environ.get("PPX_OUTPUT")
    if not val:
        raise RuntimeError("PPX_OUTPUT environment variable is not set")
    return Path(val)


@app.get("/hello")
def hello():
    return {"message": "hello"}


@app.get("/api/ppx")
def list_files():
    output = _output()
    names = sorted(p.name for p in output.iterdir() if p.is_dir())
    return names


@app.get("/api/ppx/{filename}/")
def list_pages(filename: str):
    doc_dir = _output() / filename
    if not doc_dir.is_dir():
        raise HTTPException(status_code=404, detail=f"Document '{filename}' not found")
    pages = sorted(
        (p.name for p in doc_dir.iterdir() if p.is_dir() and (p / "np_page.png").exists()),
        key=lambda n: int(n),
    )
    return {"filename": filename, "pages": len(pages)}


@app.get("/api/ppx/{filename}/{page_index}/image")
def page_image(filename: str, page_index: int):
    image_path = _output() / filename / str(page_index) / "np_page.png"
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(image_path, media_type="image/png")


@app.get("/api/ppx/{filename}/{page_index}/thumbnail")
def page_thumbnail(filename: str, page_index: int):
    from PIL import Image
    import io
    from fastapi.responses import Response

    image_path = _output() / filename / str(page_index) / "np_page.png"
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    img = Image.open(image_path)
    img.thumbnail((256, 256))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return Response(content=buf.getvalue(), media_type="image/png")


@app.get("/api/ppx/{filename}/{page_index}/markdown/index.md")
def page_markdown(filename: str, page_index: int):
    md_path = _output() / filename / str(page_index) / "markdown" / "markdown.md"
    if not md_path.exists():
        raise HTTPException(status_code=404, detail="Markdown not found")
    return PlainTextResponse(md_path.read_text())


@app.get("/api/ppx/{filename}/{page_index}/markdown/{path:path}")
def page_markdown_resource(filename: str, page_index: int, path: str):
    resource_path = _output() / filename / str(page_index) / "markdown" / path
    if not resource_path.exists():
        raise HTTPException(status_code=404, detail="Resource not found")
    return FileResponse(resource_path)


@app.get("/api/ppx/{filename}/{page_index}/layout")
def page_layout(filename: str, page_index: int):
    from ppx_align.core.storage import load
    from ppx_align.core.layout import build_layout_tree

    page_dir = _output() / filename / str(page_index)
    if not page_dir.is_dir():
        raise HTTPException(status_code=404, detail="Page not found")
    import pandas as pd
    vl, _ = load(str(page_dir))
    tree = build_layout_tree(vl)
    tree = tree.where(pd.notna(tree), None)
    return {"visual_tokens": tree.to_dict(orient="records")}


@app.get("/api/ppx/{filename}/{page_index}/alignment")
def page_alignment(filename: str, page_index: int):
    from fastapi.responses import Response
    alignment_path = _output() / filename / str(page_index) / "alignment.json"
    if not alignment_path.exists():
        raise HTTPException(status_code=404, detail="Alignment not found")
    return Response(content=alignment_path.read_bytes(), media_type="application/json")
