import tempfile
from pathlib import Path

from fastapi import APIRouter, UploadFile

from ppx.core.ocr import run_ocr
from ppx.models import OCRResult

router = APIRouter()


@router.post("/run", response_model=OCRResult)
async def ocr_run(file: UploadFile):
    """Upload an image and run OCR on it."""
    suffix = Path(file.filename or "image.png").suffix
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        result = run_ocr(tmp_path)
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    return result
