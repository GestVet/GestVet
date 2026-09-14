"""Adaptador de entrada HTTP para reclamos.

Solo el dueño de la mascota afectada presenta un reclamo, y solo sobre una
cita propia: el veterinario reclamado lo fija la cita, no quien reclama.
Verlos es cosa de quien lo presentó (para hacer seguimiento) o del personal
(para atenderlo); no hay un flujo de cierre todavía, solo quedar registrado
con su evidencia.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status

from gestvet.core.activity_log import ActivityRecorderDep
from gestvet.core.auth import require_permission
from gestvet.core.identity import Principal
from gestvet.core.pagination import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from gestvet.core.permissions import Permission
from gestvet.modules.complaints.adapters.api.dependencies import (
    AppointmentDirectoryDep,
    ComplaintRepositoryDep,
    EvidenceRepositoryDep,
    EvidenceStorageDep,
)
from gestvet.modules.complaints.adapters.api.schemas import (
    ComplaintPageResponse,
    ComplaintResponse,
    EvidenceResponse,
    FileComplaintRequest,
)
from gestvet.modules.complaints.domain.exceptions import (
    AppointmentNotFound,
    ComplaintNotFound,
    InvalidEvidence,
)
from gestvet.modules.complaints.ports.complaint_repository import ComplaintQuery
from gestvet.modules.complaints.use_cases.file_complaint import FileComplaint, FileComplaintCommand
from gestvet.modules.complaints.use_cases.list_complaints import ListComplaints, scope_to
from gestvet.modules.complaints.use_cases.upload_evidence import (
    UploadEvidence,
    UploadEvidenceCommand,
)

router = APIRouter()

ComplainantDep = Annotated[Principal, Depends(require_permission(Permission.COMPLAINTS_FILE))]
ComplaintsReaderDep = Annotated[Principal, Depends(require_permission(Permission.COMPLAINTS_READ))]


@router.post(
    "",
    response_model=ComplaintResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Presentar un reclamo sobre una cita propia",
)
async def file_complaint(
    payload: FileComplaintRequest,
    client: ComplainantDep,
    complaints: ComplaintRepositoryDep,
    appointments: AppointmentDirectoryDep,
    activity: ActivityRecorderDep,
) -> ComplaintResponse:
    try:
        complaint = await FileComplaint(complaints, appointments, activity)(
            FileComplaintCommand(
                appointment_id=payload.appointment_id,
                client_id=client.user_id,
                description=payload.description,
            )
        )
    except AppointmentNotFound as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    return ComplaintResponse.from_entity(complaint)


@router.get("", response_model=ComplaintPageResponse, summary="Listar reclamos")
async def list_complaints(
    principal: ComplaintsReaderDep,
    complaints: ComplaintRepositoryDep,
    evidence: EvidenceRepositoryDep,
    veterinarian_id: Annotated[int | None, Query(ge=1)] = None,
    limit: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ComplaintPageResponse:
    query = scope_to(
        principal,
        ComplaintQuery(veterinarian_id=veterinarian_id, limit=limit, offset=offset),
    )
    page = await ListComplaints(complaints)(query)
    return ComplaintPageResponse(
        items=[
            ComplaintResponse.from_entity(item, await evidence.list_for_complaint(item.id or 0))
            for item in page.items
        ],
        total=page.total,
    )


@router.post(
    "/{complaint_id}/evidence",
    response_model=EvidenceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Adjuntar evidencia a un reclamo propio",
)
async def upload_evidence(
    complaint_id: int,
    client: ComplainantDep,
    evidence: EvidenceRepositoryDep,
    storage: EvidenceStorageDep,
    complaints: ComplaintRepositoryDep,
    file: Annotated[UploadFile, File()],
) -> EvidenceResponse:
    content = await file.read()
    try:
        guardada = await UploadEvidence(evidence, storage, complaints)(
            UploadEvidenceCommand(
                complaint_id=complaint_id,
                requester_id=client.user_id,
                filename=file.filename or "evidencia",
                content_type=file.content_type or "application/octet-stream",
                content=content,
            )
        )
    except ComplaintNotFound as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    except InvalidEvidence as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error
    return EvidenceResponse.from_entity(guardada)
