"""Ensamblado de la aplicación.

Este es el único lugar donde los módulos de dominio se conocen entre sí, y solo
para montar sus routers. Ningún módulo importa a otro.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from gestvet.accounts.adapters.api.router import router as clients_router
from gestvet.core.config import get_settings
from gestvet.core.database import engine

API_PREFIX = "/api/v1"

settings = get_settings()


class HealthResponse(BaseModel):
    """Respuesta del sondeo de vida.

    Está tipada, y no devuelta como diccionario suelto, para que el esquema
    OpenAPI describa los campos y quien consuma el API derive el tipo exacto.
    """

    status: str
    service: str
    version: str


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    # El esquema lo crean las migraciones de Alembic, también en desarrollo.
    # Crearlo al arrancar dejaba que la base local se apartara del historial de
    # migraciones sin que nadie se enterara hasta el despliegue.
    yield
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title="GestVet API",
        version=settings.app_version,
        description="API modular para la gestión veterinaria.",
        lifespan=lifespan,
        # Todo cuelga del prefijo versionado para que un proxy que solo reenvíe
        # `/api` alcance también el esquema y la documentación.
        openapi_url=f"{API_PREFIX}/openapi.json",
        docs_url=f"{API_PREFIX}/docs",
        redoc_url=f"{API_PREFIX}/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get(f"{API_PREFIX}/health", tags=["system"], summary="Sondeo de vida")
    async def health() -> HealthResponse:
        return HealthResponse(
            status="ok",
            service=settings.app_name,
            version=settings.app_version,
        )

    app.include_router(clients_router, prefix=f"{API_PREFIX}/clients", tags=["clients"])
    return app


app = create_app()
