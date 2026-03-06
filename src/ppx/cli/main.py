import typer

from ppx.cli.commands import ocr, draw

app = typer.Typer(help="OCR utilities powered by PaddleOCR", pretty_exceptions_enable=False)
app.command(name="ocr", help="Run OCR and layout analysis on a PDF file")(ocr.run)
app.add_typer(draw.app, name="draw")

if __name__ == "__main__":
    app()
