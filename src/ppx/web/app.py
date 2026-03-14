from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel

from ppx.web.state import configure, get_data_root
from ppx.web.routes import documents


@asynccontextmanager
async def lifespan(app: FastAPI):
    root = get_data_root()
    if not root.is_dir():
        raise RuntimeError(f"Data root is not a directory: {root}")
    yield


class HealthResponse(BaseModel):
    status: str


app = FastAPI(lifespan=lifespan)
app.include_router(documents.router, prefix="/v1/ppx")


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")
