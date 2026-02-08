import typer

app = typer.Typer()


@app.command()
def start(
    host: str = typer.Option("0.0.0.0", help="Bind host"),
    port: int = typer.Option(8000, help="Bind port"),
    reload: bool = typer.Option(False, help="Enable auto-reload"),
):
    """Start the FastAPI server."""
    import uvicorn

    uvicorn.run("ppx.api.app:app", host=host, port=port, reload=reload)
