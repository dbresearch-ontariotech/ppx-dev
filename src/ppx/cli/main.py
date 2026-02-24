import typer

from ppx.cli.commands import ocr, align

app = typer.Typer(help="OCR utilities powered by PaddleOCR", pretty_exceptions_enable=False)
app.command(name="ocr", help="Run OCR and layout analysis on a PDF file")(ocr.run)
app.add_typer(align.app, name="align", help="Alignment and similarity heatmaps")


if __name__ == "__main__":
    app()
