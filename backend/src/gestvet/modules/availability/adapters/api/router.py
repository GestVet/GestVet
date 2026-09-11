"""Adaptador de entrada HTTP para la disponibilidad.

Un veterinario publica y retira su propia agenda. Cualquier cuenta autenticada
puede consultarla, porque un cliente necesita verla para poder reservar.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from gestvet.core.auth import PrincipalDep, require_roles
from gestvet.core.identity import VETERINARIAN_ROLES, Principal
from gestvet.modules.availability.adapters.api.dependencies import AvailabilityRepositoryDep
from gestvet.modules.availability.adapters.api.schemas import (
    PublishSlotRequest,
    SlotListResponse,
    SlotResponse,
)
from gestvet.modules.availability.domain.exceptions import (
    InvalidSlot,
    OverlappingSlot,
    SlotNotFound,
)
from gestvet.modules.availability.ports.availability_repository import SlotQuery
from gestvet.modules.availability.use_cases.list_slots import ListSlots
from gestvet.modules.availability.use_cases.publish_slot import PublishSlot, PublishSlotCommand
from gestvet.modules.availability.use_cases.withdraw_slot import WithdrawSlot, WithdrawSlotCommand

router = APIRouter()

VeterinarianDep = Annotated[Principal, Depends(require_roles(*VETERINARIAN_ROLES))]


def _to_list(slots: list) -> SlotListResponse:
    items = [SlotResponse.from_entity(slot) for slot in slots]
    return SlotListResponse(items=items, total=len(items))


@router.post(
    "",
    response_model=SlotResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Publicar un tramo de disponibilidad propio",
)
async def publish_slot(
    payload: PublishSlotRequest,
    veterinarian: VeterinarianDep,
    slots: AvailabilityRepositoryDep,
) -> SlotResponse:
    try:
        slot = await PublishSlot(slots)(
            PublishSlotCommand(
                veterinarian_id=veterinarian.user_id,
                starts_at=payload.starts_at,
                ends_at=payload.ends_at,
            )
        )
    except InvalidSlot as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error
    except OverlappingSlot as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    return SlotResponse.from_entity(slot)


@router.get("/mine", response_model=SlotListResponse, summary="Mi agenda publicada")
async def list_my_slots(
    veterinarian: VeterinarianDep,
    slots: AvailabilityRepositoryDep,
    starts_after: Annotated[datetime | None, Query(description="Desde")] = None,
    ends_before: Annotated[datetime | None, Query(description="Hasta")] = None,
) -> SlotListResponse:
    return _to_list(
        await ListSlots(slots)(
            SlotQuery(
                veterinarian_id=veterinarian.user_id,
                starts_after=starts_after,
                ends_before=ends_before,
            )
        )
    )


@router.get("", response_model=SlotListResponse, summary="Agenda de un veterinario")
async def list_slots_of_veterinarian(
    principal: PrincipalDep,
    slots: AvailabilityRepositoryDep,
    veterinarian_id: Annotated[int, Query(ge=1, description="Veterinario consultado")],
    starts_after: Annotated[datetime | None, Query(description="Desde")] = None,
    ends_before: Annotated[datetime | None, Query(description="Hasta")] = None,
) -> SlotListResponse:
    return _to_list(
        await ListSlots(slots)(
            SlotQuery(
                veterinarian_id=veterinarian_id,
                starts_after=starts_after,
                ends_before=ends_before,
            )
        )
    )


@router.delete(
    "/{slot_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Retirar un tramo propio",
)
async def withdraw_slot(
    slot_id: int,
    veterinarian: VeterinarianDep,
    slots: AvailabilityRepositoryDep,
) -> None:
    try:
        await WithdrawSlot(slots)(
            WithdrawSlotCommand(slot_id=slot_id, veterinarian_id=veterinarian.user_id)
        )
    except SlotNotFound as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
