from fastapi import FastAPI

from ppx.api.routes import ocr

app = FastAPI(title="OCR Utilities API")
app.include_router(ocr.router, prefix="/ocr", tags=["ocr"])


@app.get("/health")
def health():
    return {"status": "ok"}
