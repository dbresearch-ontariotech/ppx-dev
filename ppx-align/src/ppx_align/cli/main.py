import typer

from ppx_align.cli.commands import process, server

app = typer.Typer(help="Alignment, layout tree, and web server for the ppx OCR pipeline", pretty_exceptions_enable=False)
app.add_typer(process.app, name="process", help="Layout tree and alignment commands")
app.add_typer(server.app, name="server", help="Web server commands")

if __name__ == "__main__":
    app()
