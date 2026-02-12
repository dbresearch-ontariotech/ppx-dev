import typer

from ppx.cli.commands import ocr, server, align

app = typer.Typer(help="OCR utilities powered by PaddleOCR", pretty_exceptions_enable=False)
app.add_typer(ocr.app, name="ocr", help="Run OCR operations")
app.add_typer(server.app, name="server", help="API server management")
app.add_typer(align.app, name="align", help="Alignment and similarity heatmaps")


if __name__ == "__main__":
    app()
