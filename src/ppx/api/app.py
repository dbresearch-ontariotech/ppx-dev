from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from ppx.api.routes import documents

app = FastAPI(title="OCR Utilities API")
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])


@app.get("/api/health")
def health():
    return {"status": "ok"}


class SPAMiddleware(BaseHTTPMiddleware):
    """Serve static files for non-API requests, falling back to index.html."""

    def __init__(self, app, static_dir: Path):
        super().__init__(app)
        self.static_dir = static_dir

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        # If the API returned 404 and it's a GET for a non-API path, serve SPA
        if (
            response.status_code == 404
            and request.method == "GET"
            and not request.url.path.startswith("/api/")
        ):
            path = request.url.path.lstrip("/")
            # Try exact static file
            candidate = self.static_dir / path
            if candidate.is_file():
                return FileResponse(candidate)
            # SPA fallback
            return FileResponse(self.static_dir / "index.html")

        return response


def configure(data_dir: Path, static_dir: Optional[Path] = None) -> None:
    """Set the data directory for the documents router."""
    documents.data_dir = data_dir

    if static_dir and static_dir.is_dir():
        # Serve _next static assets directly
        app.mount(
            "/_next",
            StaticFiles(directory=static_dir / "_next"),
            name="next-assets",
        )
        # SPA fallback for everything else
        app.add_middleware(SPAMiddleware, static_dir=static_dir)
