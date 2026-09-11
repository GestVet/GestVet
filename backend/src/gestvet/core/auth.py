"""Autenticación y autorización para el borde HTTP de cualquier módulo.

Es la única pieza del núcleo que lee la tabla de usuarios, y lee solo tres
columnas: identificador, rol y estado. Esa proyección mínima es el contrato
compartido entre módulos. El resto del perfil lo posee `accounts` y nadie más
lo toca.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from gestvet.core.config import get_settings
from gestvet.core.database import get_session
from gestvet.core.identity import (
    InvalidToken,
    PermissionDenied,
    Principal,
    Role,
    TokenService,
    ensure_role_is_allowed,
)
from gestvet.core.tokens import JwtTokenService

# `auto_error=False` para responder con el mensaje del proyecto en vez del
# texto que trae Starlette cuando falta la cabecera.
bearer_scheme = HTTPBearer(auto_error=False, description="Token emitido por /api/v1/auth/login")

UNAUTHENTICATED_HEADERS = {"WWW-Authenticate": "Bearer"}

# Proyección de identidad. Deliberadamente no usa el modelo ORM de `accounts`:
# importarlo convertiria al nucleo en dependiente de un modulo de dominio.
_PRINCIPAL_QUERY = text("SELECT id, role, is_active FROM users WHERE id = :user_id")

SessionDep = Annotated[AsyncSession, Depends(get_session)]
CredentialsDep = Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)]


def get_token_service() -> TokenService:
    settings = get_settings()
    return JwtTokenService(
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        ttl_seconds=settings.access_token_ttl_seconds,
    )


TokenServiceDep = Annotated[TokenService, Depends(get_token_service)]


def unauthenticated(detail: str) -> HTTPException:
    return HTTPException(status.HTTP_401_UNAUTHORIZED, detail, headers=UNAUTHENTICATED_HEADERS)


async def get_principal(
    credentials: CredentialsDep,
    session: SessionDep,
    tokens: TokenServiceDep,
) -> Principal:
    if credentials is None:
        raise unauthenticated("Falta la credencial de acceso.")

    try:
        claims = tokens.decode(credentials.credentials)
    except InvalidToken as error:
        raise unauthenticated(str(error)) from error

    # El rol se relee de la base y no se toma del token: así una cuenta
    # degradada o desactivada pierde el acceso sin esperar a que expire.
    row = (await session.execute(_PRINCIPAL_QUERY, {"user_id": claims.user_id})).first()
    if row is None or not row.is_active:
        raise unauthenticated("La cuenta ya no está disponible.")

    return Principal(user_id=int(row.id), role=Role(row.role), is_active=bool(row.is_active))


PrincipalDep = Annotated[Principal, Depends(get_principal)]


def require_roles(*allowed: Role) -> Callable[[Principal], Awaitable[Principal]]:
    """Construye una dependencia que exige uno de estos roles."""
    permitted = frozenset(allowed)

    async def dependency(principal: PrincipalDep) -> Principal:
        try:
            ensure_role_is_allowed(principal.role, permitted)
        except PermissionDenied as error:
            raise HTTPException(status.HTTP_403_FORBIDDEN, str(error)) from error
        return principal

    return dependency
