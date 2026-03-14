import typer

from ppx.cli.commands import ocr, draw, server

app = typer.Typer(help="OCR utilities powered by PaddleOCR", pretty_exceptions_enable=False)
app.add_typer(ocr.app, name="ocr", help="OCR and layout analysis commands")
app.add_typer(draw.app, name="draw", help="Visualization commands")
app.add_typer(server.app, name="server", help="Web server commands")

if __name__ == "__main__":
    app()
