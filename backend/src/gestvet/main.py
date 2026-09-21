"""Ensamblado de la aplicación.

Este es el único lugar donde los módulos de dominio se conocen entre sí, y solo
para montar sus routers. Ningún módulo importa a otro.
"""

from __future__ import annotations

import asyncio
import contextlib
import secrets
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated, Any

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from gestvet.core.config import get_settings
from gestvet.core.database import SessionFactory, engine, get_session_factory
from gestvet.core.events_router import router as events_router
from gestvet.core.logs import configure_logging, get_logger
from gestvet.core.realtime_broker import get_broker
from gestvet.core.request_logging import REQUEST_ID_HEADER, RequestLoggingMiddleware
from gestvet.core.whatsapp_console import ConsoleWhatsAppSender
from gestvet.modules.access.adapters.api.router import router as access_router
from gestvet.modules.accounts.adapters.api.admin_router import router as admin_router
from gestvet.modules.accounts.adapters.api.auth_router import router as auth_router
from gestvet.modules.accounts.adapters.api.router import router as clients_router
from gestvet.modules.accounts.adapters.api.veterinarians_router import (
    router as veterinarians_router,
)
from gestvet.modules.appointments.adapters.api.router import router as appointments_router
from gestvet.modules.appointments.adapters.persistence.directories import (
    SqlClientDirectory as SqlAppointmentClientDirectory,
)
from gestvet.modules.appointments.adapters.persistence.directories import (
    SqlPetDirectory as SqlAppointmentPetDirectory,
)
from gestvet.modules.appointments.adapters.persistence.repositories import (
    SqlAlchemyAppointmentRepository,
)
from gestvet.modules.appointments.use_cases.send_upcoming_reminders import SendUpcomingReminders
from gestvet.modules.availability.adapters.api.router import router as availability_router
from gestvet.modules.billing.adapters.api.router import router as billing_router
from gestvet.modules.complaints.adapters.api.router import router as complaints_router
from gestvet.modules.hospitalizations.adapters.api.router import (
    router as hospitalizations_router,
)
from gestvet.modules.insights.adapters.api.pets_overview_router import (
    router as pets_overview_router,
)
from gestvet.modules.insights.adapters.api.router import router as insights_router
from gestvet.modules.insights.adapters.api.service_consumption_router import (
    router as service_consumption_router,
)
from gestvet.modules.medical_records.adapters.api.assistant_router import (
    router as clinical_assistant_router,
)
from gestvet.modules.medical_records.adapters.api.public_card_router import (
    router as public_card_router,
)
from gestvet.modules.medical_records.adapters.api.router import router as medical_records_router
from gestvet.modules.medical_records.adapters.api.vaccinations_router import (
    router as vaccinations_router,
)
from gestvet.modules.medical_records.adapters.persistence.directories import (
    SqlOwnerContactDirectory,
)
from gestvet.modules.medical_records.adapters.persistence.repositories import (
    SqlAlchemyVaccinationRepository,
)
from gestvet.modules.medical_records.use_cases.send_vaccine_reminders import SendVaccineReminders
from gestvet.modules.pets.adapters.api.catalog_router import router as pet_catalog_router
from gestvet.modules.pets.adapters.api.router import router as pets_router
from gestvet.modules.reviews.adapters.api.router import router as reviews_router

API_PREFIX = "/api/v1"

settings = get_settings()
logger = get_logger("gestvet.app")

# Cada cuánto se despiertan los recordatorios de WhatsApp a revisar qué citas
# entran a su ventana de 24h y qué vacunas vencen en la semana. Es un
# `asyncio.Task` en el propio proceso y no un servicio aparte: alcanza para un
# solo proceso de API, que es como corre esto hoy, y no agrega ninguna
# dependencia nueva al proyecto.
REMINDER_POLL_INTERVAL_SECONDS = 30 * 60


class HealthResponse(BaseModel):
    """Respuesta del sondeo de vida.

    Está tipada, y no devuelta como diccionario suelto, para que el esquema
    OpenAPI describa los campos y el frontend derive el tipo exacto.
    """

    status: str
    service: str
    version: str


async def _send_due_reminders(factory: async_sessionmaker[AsyncSession]) -> None:
    async with factory() as session:
        use_case = SendUpcomingReminders(
            SqlAlchemyAppointmentRepository(session),
            SqlAppointmentClientDirectory(session),
            SqlAppointmentPetDirectory(session),
            ConsoleWhatsAppSender(),
        )
        await use_case()
        await session.commit()


async def _send_due_vaccine_reminders(factory: async_sessionmaker[AsyncSession]) -> None:
    async with factory() as session:
        use_case = SendVaccineReminders(
            SqlAlchemyVaccinationRepository(session),
            SqlOwnerContactDirectory(session),
            ConsoleWhatsAppSender(),
        )
        await use_case()
        await session.commit()


async def run_reminder_round(
    factory: async_sessionmaker[AsyncSession] | None = None,
) -> dict[str, str]:
    """Ejecuta una ronda de comprobación y envío de recordatorios pendientes."""
    session_factory = factory or SessionFactory
    results: dict[str, str] = {}
    for job in (_send_due_reminders, _send_due_vaccine_reminders):
        try:
            await job(session_factory)
            results[job.__name__] = "ok"
        except Exception:
            # Un fallo en una vuelta (por ejemplo, la base momentáneamente
            # inalcanzable) no debe tumbar el proceso: se reintenta en la
            # siguiente, con lo pendiente todavía sin `reminder_sent_at`.
            logger.exception("whatsapp.reminders_failed", job=job.__name__)
            results[job.__name__] = "error"
    return results


async def _reminder_loop() -> None:
    while True:
        await asyncio.sleep(REMINDER_POLL_INTERVAL_SECONDS)
        await run_reminder_round(SessionFactory)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    # El esquema lo crean las migraciones de Alembic, también en desarrollo.
    # Crearlo al arrancar dejaba que la base local se apartara del historial de
    # migraciones sin que nadie se enterara hasta el despliegue.
    broker = get_broker()
    await broker.start()
    reminder_task = asyncio.create_task(_reminder_loop())
    logger.info("app.started", version=settings.app_version, debug=settings.debug)
    yield
    reminder_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await reminder_task
    await broker.stop()
    await engine.dispose()
    logger.info("app.stopped")


def create_app() -> FastAPI:
    # Se configura acá y no al importar el módulo: uvicorn instala sus propios
    # handlers antes de cargar la aplicación, y esta llamada los reemplaza.
    configure_logging(level=settings.log_level, json=settings.log_json)

    app = FastAPI(
        title="GestVet API",
        version=settings.app_version,
        description="API modular para la gestión veterinaria.",
        lifespan=lifespan,
        # El esquema y la documentación cuelgan del prefijo versionado para
        # que el proxy del frontend, que solo reenvía `/api`, los alcance.
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
        # Sin exponerla, el navegador no deja leer la cabecera desde otro
        # origen y el frontend no podría anotar el identificador de un error.
        expose_headers=[REQUEST_ID_HEADER],
    )
    # Se agrega al final para quedar por fuera de CORS: así también se
    # registran las respuestas que CORS corta antes de llegar a un router.
    app.add_middleware(RequestLoggingMiddleware)

    @app.get(f"{API_PREFIX}/health", tags=["system"], summary="Sondeo de vida")
    async def health() -> HealthResponse:
        return HealthResponse(
            status="ok",
            service=settings.app_name,
            version=settings.app_version,
        )

    @app.post(
        f"{API_PREFIX}/internal/reminders/run",
        tags=["system"],
        summary="Disparador del cron de recordatorios",
        # Solo lo llama el cron de GitHub Actions: no es parte del contrato del frontend.
        include_in_schema=False,
    )
    async def trigger_reminders(
        session_factory: Annotated[async_sessionmaker[AsyncSession], Depends(get_session_factory)],
        x_reminders_token: Annotated[str | None, Header(alias="X-Reminders-Token")] = None,
        authorization: Annotated[str | None, Header()] = None,
    ) -> dict[str, Any]:
        cron_token = get_settings().reminders_cron_token.strip()
        if not cron_token:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Endpoint no habilitado.",
            )

        token = x_reminders_token
        if not token and authorization and authorization.startswith("Bearer "):
            token = authorization[7:].strip()

        if not token or not secrets.compare_digest(token, cron_token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token de recordatorios inválido.",
            )

        jobs = await run_reminder_round(session_factory)
        return {"status": "ok", "jobs": jobs}

    app.include_router(events_router, prefix=f"{API_PREFIX}/events", tags=["system"])
    app.include_router(access_router, prefix=f"{API_PREFIX}/access", tags=["access"])
    app.include_router(auth_router, prefix=f"{API_PREFIX}/auth", tags=["auth"])
    app.include_router(clients_router, prefix=f"{API_PREFIX}/clients", tags=["clients"])
    app.include_router(admin_router, prefix=API_PREFIX, tags=["admin"])
    app.include_router(
        veterinarians_router, prefix=f"{API_PREFIX}/veterinarians", tags=["veterinarians"]
    )
    # Antes que el de mascotas: "/pets/catalog" no es una mascota.
    app.include_router(pet_catalog_router, prefix=f"{API_PREFIX}/pets/catalog", tags=["pets"])
    app.include_router(pets_router, prefix=f"{API_PREFIX}/pets", tags=["pets"])
    app.include_router(
        availability_router, prefix=f"{API_PREFIX}/availability", tags=["availability"]
    )
    app.include_router(
        appointments_router, prefix=f"{API_PREFIX}/appointments", tags=["appointments"]
    )
    # Antes que la historia clínica: "/medical-records/vaccinations" no es una entrada.
    # Sin sesión: la abre quien escanea el QR del carnet.
    app.include_router(
        public_card_router,
        prefix=f"{API_PREFIX}/public/vaccination-cards",
        tags=["public"],
    )
    app.include_router(
        clinical_assistant_router,
        prefix=f"{API_PREFIX}/medical-records/assistant",
        tags=["medical-records"],
    )
    app.include_router(
        vaccinations_router,
        prefix=f"{API_PREFIX}/medical-records/vaccinations",
        tags=["medical-records"],
    )
    app.include_router(
        medical_records_router, prefix=f"{API_PREFIX}/medical-records", tags=["medical-records"]
    )
    app.include_router(billing_router, prefix=f"{API_PREFIX}/payments", tags=["billing"])
    app.include_router(reviews_router, prefix=f"{API_PREFIX}/reviews", tags=["reviews"])
    app.include_router(complaints_router, prefix=f"{API_PREFIX}/complaints", tags=["complaints"])
    app.include_router(
        hospitalizations_router,
        prefix=f"{API_PREFIX}/hospitalizations",
        tags=["hospitalizations"],
    )
    app.include_router(insights_router, prefix=f"{API_PREFIX}/insights", tags=["insights"])
    app.include_router(pets_overview_router, prefix=f"{API_PREFIX}/insights", tags=["insights"])
    app.include_router(
        service_consumption_router, prefix=f"{API_PREFIX}/insights", tags=["insights"]
    )
    return app


app = create_app()
