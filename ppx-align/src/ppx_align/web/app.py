from __future__ import annotations

import asyncio
import os
import random
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from pydantic import BaseModel

from ppx_align.web.state import configure, get_data_root
from ppx_align.web.routes import documents


@asynccontextmanager
async def lifespan(app: FastAPI):
    root = get_data_root()
    if not root.is_dir():
        raise RuntimeError(f"Data root is not a directory: {root}")
    yield


class HealthResponse(BaseModel):
    status: str


app = FastAPI(lifespan=lifespan)
app.include_router(documents.router, prefix="/api/v1/ppx")


@app.middleware("http")
async def random_delay_middleware(request: Request, call_next):
    delay_ms = int(os.environ.get("PPX_DELAY_MS", "0"))
    if delay_ms > 0:
        ms = random.uniform(delay_ms // 2, delay_ms)
        await asyncio.sleep(ms / 1000)
    return await call_next(request)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")
