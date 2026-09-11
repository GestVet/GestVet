"""Adaptador de entrada HTTP para el acceso.

Traduce credenciales a un token y errores de dominio a códigos de estado. No
decide nada: la regla de quién puede entrar vive en el caso de uso.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from gestvet.accounts.adapters.api.dependencies import (
    PasswordHasherDep,
    UserRepositoryDep,
)
from gestvet.accounts.adapters.api.schemas import (
    AccessTokenResponse,
    LoginRequest,
    RegisterClientRequest,
    UserResponse,
)
from gestvet.accounts.domain.exceptions import (
    EmailAlreadyRegistered,
    InactiveAccount,
    InvalidCredentials,
    InvalidEmail,
)
from gestvet.accounts.use_cases.authenticate_user import (
    AuthenticateUser,
    AuthenticateUserCommand,
)
from gestvet.accounts.use_cases.register_client import RegisterClient, RegisterClientCommand
from gestvet.core.auth import UNAUTHENTICATED_HEADERS, PrincipalDep, TokenServiceDep

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Autorregistro de un cliente",
)
async def register_client(
    payload: RegisterClientRequest,
    users: UserRepositoryDep,
    hasher: PasswordHasherDep,
) -> UserResponse:
    use_case = RegisterClient(users, hasher)
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
    return UserResponse.from_entity(user)


@router.post("/login", response_model=AccessTokenResponse, summary="Obtener un token de acceso")
async def login(
    payload: LoginRequest,
    users: UserRepositoryDep,
    hasher: PasswordHasherDep,
    tokens: TokenServiceDep,
) -> AccessTokenResponse:
    use_case = AuthenticateUser(users, hasher, tokens)
    try:
        session = await use_case(
            AuthenticateUserCommand(email=str(payload.email), password=payload.password)
        )
    except InvalidCredentials as error:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, str(error), headers=UNAUTHENTICATED_HEADERS
        ) from error
    except InactiveAccount as error:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(error)) from error

    return AccessTokenResponse(
        access_token=session.token.value,
        expires_in=session.token.expires_in_seconds,
        user=UserResponse.from_entity(session.user),
    )


@router.get("/me", response_model=UserResponse, summary="Cuenta que emitió la petición")
async def read_current_user(principal: PrincipalDep, users: UserRepositoryDep) -> UserResponse:
    # El principal solo trae identificador y rol. El perfil completo lo posee
    # este módulo, así que acá sí se lee la entidad entera.
    user = await users.get(principal.user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "La cuenta ya no existe.")
    return UserResponse.from_entity(user)
