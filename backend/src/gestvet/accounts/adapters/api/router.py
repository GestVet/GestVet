"""Adaptador de entrada HTTP.

Traduce peticiones a comandos, y errores de dominio a códigos de estado. No
contiene reglas de negocio ni consultas.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from gestvet.accounts.adapters.api.schemas import (
    ClientPageResponse,
    RegisterClientRequest,
    UserResponse,
)
from gestvet.accounts.adapters.persistence.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from gestvet.accounts.domain.entities import User
from gestvet.accounts.domain.exceptions import EmailAlreadyRegistered, InvalidEmail
from gestvet.accounts.ports.user_repository import ClientQuery
from gestvet.accounts.use_cases.list_clients import ListClients
from gestvet.accounts.use_cases.register_client import RegisterClient, RegisterClientCommand
from gestvet.core.database import get_session
from gestvet.core.security import BcryptPasswordHasher

router = APIRouter()

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def _to_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id or 0,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        phone=user.phone,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
    )


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Autorregistro de un cliente",
)
async def register_client(payload: RegisterClientRequest, session: SessionDep) -> UserResponse:
    use_case = RegisterClient(SqlAlchemyUserRepository(session), BcryptPasswordHasher())
    try:
        user = await use_case(
            RegisterClientCommand(
                email=str(payload.email),
                password=payload.password,
                first_name=payload.first_name,
                last_name=payload.last_name,
                phone=payload.phone,
            )
        )
    except EmailAlreadyRegistered as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    except InvalidEmail as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(error)) from error
    return _to_response(user)


@router.get("", response_model=ClientPageResponse, summary="Listar clientes")
async def list_clients(
    session: SessionDep,
    search: Annotated[str | None, Query(description="Busca en nombre, correo y teléfono")] = None,
    ordering: Annotated[str | None, Query(description="Columna, '-' invierte")] = None,
    is_active: Annotated[bool | None, Query(description="Filtra por estado")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ClientPageResponse:
    use_case = ListClients(SqlAlchemyUserRepository(session))
    page = await use_case(
        ClientQuery(
            search=search,
            is_active=is_active,
            ordering=ordering,
            limit=limit,
            offset=offset,
        )
    )
    return ClientPageResponse(
        items=[_to_response(user) for user in page.items],
        total=page.total,
    )
