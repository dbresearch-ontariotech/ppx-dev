import typer

from ppx.cli.commands import ocr, server

app = typer.Typer(help="OCR utilities powered by PaddleOCR")
app.add_typer(ocr.app, name="ocr", help="Run OCR operations")
app.add_typer(server.app, name="server", help="API server management")


if __name__ == "__main__":
    app()
