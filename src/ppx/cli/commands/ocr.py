from pathlib import Path
from typing import Optional

import typer
from rich import print as rprint

from ppx.core import helpers

app = typer.Typer()

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp"}


@app.command("run")
def RunCommand(
    input_file: Path = typer.Argument(..., help="PDF or image input file."),
    page_number: Optional[int] = typer.Argument(None, help="Page to perform OCR (PDF only)"),
    save_path: Path = typer.Option(..., "-o", help="Output directory"),
):
    import cv2
    from ppx.core import ocr

    is_image = input_file.suffix.lower() in IMAGE_SUFFIXES

    if is_image:
        np_page = helpers.get_image_tensor(input_file)
    else:
        if page_number is None:
            page_number = 0
        pages = list(helpers.get_page_tensors(input_file))
        if page_number < 0 or page_number >= len(pages):
            rprint(f"[red]Page {page_number} out of range (0-{len(pages) - 1})[/red]")
            raise typer.Exit(1)
        np_page = pages[page_number]

    # Run OCR and parse results
    rprint("[bold]Running OCR...[/bold]")
    frames = ocr.ocr(np_page)

    basename = input_file.stem
    save_path.mkdir(parents=True, exist_ok=True)

    # Convert RGB to BGR for OpenCV drawing and saving
    np_page_bgr = cv2.cvtColor(frames.output_image, cv2.COLOR_RGB2BGR)

    # Draw text-level bounding boxes in red (BGR: 0,0,255)
    text_img = helpers.annotate(np_page_bgr, frames.texts, color=(0, 0, 255))
    text_path = save_path / f"{basename}_text.png"
    cv2.imwrite(str(text_path), text_img)
    rprint(f"[green]Saved text annotations to {text_path}[/green]")

    # Draw word-level bounding boxes in blue (BGR: 255,0,0)
    words_img = helpers.annotate(np_page_bgr, frames.words, color=(255, 0, 0))
    words_path = save_path / f"{basename}_words.png"
    cv2.imwrite(str(words_path), words_img)
    rprint(f"[green]Saved word annotations to {words_path}[/green]")


@app.command("struct")
def RunStructV3(
    pdf_file: Path = typer.Argument(..., help = "PDF file"),
    page_number: int = typer.Argument(..., help="Page number")
):
    import cv2
    from ppx.core import ocr

    pages = list(helpers.get_page_tensors(pdf_file))
    np_page = pages[page_number]
    model = ocr.get_structv3_model()
    ocr.structv3(np_page, model)