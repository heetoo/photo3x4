"""Aplicação FastAPI da interface e da API REST do photo3x4."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from PIL import Image

from .observability import init_sentry
from .processor import process_for_sheet, process_image
from .utils import image_to_jpeg

BASE_DIR = Path(__file__).parent


def git_revision() -> str:
    """Obtém a revisão para versionar os assets do frontend."""
    configured = os.getenv("APP_GIT_SHA")
    if configured:
        return configured[:40]
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=BASE_DIR.parent,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "dev"


init_sentry(release=git_revision())
app = FastAPI(title="photo3x4", version="0.1.0")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def home() -> HTMLResponse:
    """Entrega a aplicação web de uma página."""
    template = (BASE_DIR / "templates" / "index.html").read_text(encoding="utf-8")
    return HTMLResponse(
        content=template.replace("__APP_GIT_SHA__", git_revision()),
        headers={"Cache-Control": "no-store, max-age=0"},
    )


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check simples."""
    return {"status": "ok"}


@app.get("/sw.js")
async def service_worker() -> Response:
    """Entrega o service worker no escopo da aplicação inteira."""
    service_worker_file = (BASE_DIR / "static" / "sw.js").read_bytes()
    return Response(
        content=service_worker_file,
        media_type="application/javascript",
        headers={"Service-Worker-Allowed": "/", "Cache-Control": "no-cache"},
    )


@app.post("/api/process")
async def process(file: UploadFile = File(...)) -> Response:
    """Remove o fundo e retorna a captura completa para edição no navegador."""
    try:
        result = process_image(await file.read(), fit=False)
        return Response(content=image_to_jpeg(result), media_type="image/jpeg")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Não foi possível processar a foto.") from exc


@app.post("/api/sheet")
async def sheet(file: UploadFile = File(...)) -> Response:
    """Recebe uma foto 3x4 e retorna oito cópias em uma folha 10x15."""
    try:
        result = process_for_sheet(await file.read())
        return Response(content=image_to_jpeg(result), media_type="image/jpeg")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Não foi possível gerar a folha.") from exc
