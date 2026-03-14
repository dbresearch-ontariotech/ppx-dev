import os
from pathlib import Path
from typing import Annotated

import typer

app = typer.Typer()


@app.command()
def start(
    data: Annotated[
        Path,
        typer.Option("--data", envvar="PPX_DATA_DIR", exists=True, file_okay=False, resolve_path=True),
    ],
    host: str = "0.0.0.0",
    port: int = 8000,
    reload: bool = False,
):
    """Start the PPX web server."""
    import uvicorn
    from ppx.web.state import configure

    os.environ["PPX_DATA_DIR"] = str(data)
    configure(data)
    uvicorn.run("ppx.web.app:app", host=host, port=port, reload=reload)
