"""Adaptador de entrada HTTP de servicios más consumidos.

Router aparte del resto de indicadores: usa `payments.report`, no
`insights.read` — es el mismo permiso que ya exige el reporte de pagos por
medio, exclusivo de administración. No expone nombres de clientes: cuenta
citas por tipo de servicio, nada más.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, Response

from gestvet.core.auth import require_permission
from gestvet.core.permissions import Permission
from gestvet.modules.insights.adapters.api.dependencies import (
    ServiceConsumptionDirectoryDep,
    ServiceConsumptionRendererDep,
)
from gestvet.modules.insights.adapters.api.schemas import (
    ServiceConsumptionListResponse,
    ServiceConsumptionResponse,
)
from gestvet.modules.insights.ports.service_consumption_report import ServiceConsumptionDocument
from gestvet.modules.insights.use_cases.list_service_consumption import ListServiceConsumption

router = APIRouter(dependencies=[Depends(require_permission(Permission.PAYMENTS_REPORT))])

StatusFilter = Literal["pending", "confirmed", "completed", "cancelled", "no_show"]

_STATUS_LABELS: dict[str | None, str] = {
    None: "Todos",
    "pending": "Pendiente",
    "confirmed": "Confirmada",
    "completed": "Completada",
    "cancelled": "Cancelada",
    "no_show": "No asistió",
}

StartsAfterQuery = Annotated[datetime | None, Query(description="Desde")]
EndsBeforeQuery = Annotated[datetime | None, Query(description="Hasta")]
StatusQuery = Annotated[StatusFilter | None, Query(description="Filtra por estado de la cita")]


@router.get(
    "/service-consumption",
    response_model=ServiceConsumptionListResponse,
    summary="Cuántas citas tuvo cada servicio, sin datos de clientes",
)
async def list_service_consumption(
    directory: ServiceConsumptionDirectoryDep,
    starts_after: StartsAfterQuery = None,
    ends_before: EndsBeforeQuery = None,
    status: StatusQuery = None,
) -> ServiceConsumptionListResponse:
    items = await ListServiceConsumption(directory)(starts_after, ends_before, status)
    return ServiceConsumptionListResponse(
        items=[ServiceConsumptionResponse.from_entity(item) for item in items]
    )


@router.get(
    "/service-consumption.pdf",
    summary="Descargar en PDF los servicios más consumidos",
)
async def download_service_consumption_pdf(
    directory: ServiceConsumptionDirectoryDep,
    renderer: ServiceConsumptionRendererDep,
    starts_after: StartsAfterQuery = None,
    ends_before: EndsBeforeQuery = None,
    status: StatusQuery = None,
) -> Response:
    items = await ListServiceConsumption(directory)(starts_after, ends_before, status)
    pdf = renderer.render(
        ServiceConsumptionDocument(
            items=items,
            starts_on=starts_after.date() if starts_after is not None else None,
            # `ends_before` es exclusivo: el frontend manda el inicio del día
            # siguiente al elegido. Un instante antes cae en el día que la
            # persona eligió, que es el que tiene que decir el PDF.
            ends_on=(
                (ends_before - ends_before.resolution).date() if ends_before is not None else None
            ),
            status_label=_STATUS_LABELS[status],
            generated_at=datetime.now(UTC).date(),
        )
    )
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="servicios-mas-consumidos.pdf"'},
    )
