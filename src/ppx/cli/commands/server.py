from pathlib import Path

import typer

app = typer.Typer()


@app.command()
def start(
    host: str = typer.Option("0.0.0.0", help="Bind host"),
    port: int = typer.Option(8000, help="Bind port"),
    reload: bool = typer.Option(False, help="Enable auto-reload"),
    data: Path = typer.Option(
        ...,
        envvar="PPX_DATA_DIR",
        help="Root data directory produced by `ppx ocr run`",
        exists=True,
        file_okay=False,
        resolve_path=True,
    ),
):
    """Start the FastAPI server."""
    import uvicorn

    from ppx.api.app import app as fastapi_app, configure

    static_dir = Path(__file__).resolve().parents[4] / "web" / "out"
    configure(data, static_dir if static_dir.is_dir() else None)
    uvicorn.run(fastapi_app, host=host, port=port)
