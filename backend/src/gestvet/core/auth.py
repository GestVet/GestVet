"""Autenticación y autorización para el borde HTTP de cualquier módulo.

Es la única pieza del núcleo que lee la tabla de usuarios, y lee solo lo que la
autorización necesita: identificador, tipo de cuenta, estado y los permisos de
su rol. Esa proyección mínima es el contrato compartido entre módulos. El resto
del perfil lo posee `accounts`, y los roles los posee `access`.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from gestvet.core.config import get_settings
from gestvet.core.database import get_session
from gestvet.core.identity import (
    InvalidToken,
    MissingPermission,
    Principal,
    Role,
    TokenService,
    ensure_permission,
)
from gestvet.core.permissions import Permission
from gestvet.core.tokens import JwtTokenService

# `auto_error=False` para responder con el mensaje del proyecto en vez del
# texto que trae Starlette cuando falta la cabecera.
bearer_scheme = HTTPBearer(auto_error=False, description="Token emitido por /api/v1/auth/login")

UNAUTHENTICATED_HEADERS = {"WWW-Authenticate": "Bearer"}

# Proyección de identidad y acceso. Deliberadamente no usa los modelos ORM de
# `accounts` ni de `access`: importarlos convertiría al núcleo en dependiente de
# módulos de dominio.
#
# El rol efectivo es el asignado a la cuenta, si es de su mismo tipo, o el rol
# de sistema de su tipo. Así una cuenta nueva no necesita ninguna fila extra, y
# una asignación que quedó desfasada tras un cambio de tipo no da permisos
# ajenos. Devuelve una fila por permiso.
_ACCESS_QUERY = text(
    "SELECT u.id, u.role, u.is_active, r.id AS role_id, r.name AS role_name, p.permission "
    "FROM users u "
    "LEFT JOIN access_roles r ON r.id = COALESCE("
    "(SELECT a.role_id FROM user_access_roles a "
    "JOIN access_roles ar ON ar.id = a.role_id "
    "WHERE a.user_id = u.id AND ar.account_kind = u.role), "
    "(SELECT s.id FROM access_roles s WHERE s.is_system = :system AND s.account_kind = u.role)"
    ") "
    "LEFT JOIN access_role_permissions p ON p.role_id = r.id "
    "WHERE u.id = :user_id"
)

SessionDep = Annotated[AsyncSession, Depends(get_session)]
CredentialsDep = Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)]


@dataclass(frozen=True, slots=True)
class SessionAccess:
    """El rol efectivo de una cuenta, tal como lo ve la interfaz."""

    role_id: int | None
    role_name: str
    permissions: frozenset[str]


@dataclass(frozen=True, slots=True)
class _LoadedAccount:
    principal: Principal
    access: SessionAccess


async def _load_account(session: AsyncSession, user_id: int) -> _LoadedAccount | None:
    rows = (await session.execute(_ACCESS_QUERY, {"user_id": user_id, "system": True})).all()
    if not rows:
        return None
    first = rows[0]
    permissions = frozenset(str(row.permission) for row in rows if row.permission is not None)
    principal = Principal(
        user_id=int(first.id),
        role=Role(first.role),
        is_active=bool(first.is_active),
        permissions=permissions,
    )
    access = SessionAccess(
        role_id=int(first.role_id) if first.role_id is not None else None,
        role_name=str(first.role_name or ""),
        permissions=permissions,
    )
    return _LoadedAccount(principal=principal, access=access)


async def load_access(session: AsyncSession, user_id: int) -> SessionAccess:
    """Rol efectivo y permisos de una cuenta, para devolvérselos a la interfaz."""
    loaded = await _load_account(session, user_id)
    if loaded is None:
        return SessionAccess(role_id=None, role_name="", permissions=frozenset())
    return loaded.access


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


async def _resolve_principal(
    credentials: HTTPAuthorizationCredentials | None,
    session: AsyncSession,
    tokens: TokenService,
) -> Principal:
    if credentials is None:
        raise unauthenticated("Falta la credencial de acceso.")

    try:
        claims = tokens.decode(credentials.credentials)
    except InvalidToken as error:
        raise unauthenticated(str(error)) from error

    # El tipo de cuenta y los permisos se releen de la base y no se toman del
    # token: una cuenta desactivada, o un rol al que se le quitó un permiso,
    # pierde el acceso en la petición siguiente sin esperar a que expire.
    loaded = await _load_account(session, claims.user_id)
    if loaded is None or not loaded.principal.is_active:
        raise unauthenticated("La cuenta ya no está disponible.")
    return loaded.principal


async def get_principal(
    credentials: CredentialsDep,
    session: SessionDep,
    tokens: TokenServiceDep,
) -> Principal:
    return await _resolve_principal(credentials, session, tokens)


PrincipalDep = Annotated[Principal, Depends(get_principal)]

# Una conexión de avisos queda abierta por horas. Con la sesión de siempre, que
# se cierra al terminar la respuesta, retendría una conexión del pool todo ese
# tiempo; con `scope="function"` la sesión se cierra antes de empezar a
# transmitir.
_ShortSessionDep = Annotated[AsyncSession, Depends(get_session, scope="function")]


async def get_stream_principal(
    credentials: CredentialsDep,
    session: _ShortSessionDep,
    tokens: TokenServiceDep,
) -> Principal:
    return await _resolve_principal(credentials, session, tokens)


StreamPrincipalDep = Annotated[Principal, Depends(get_stream_principal)]


def require_permission(*required: Permission) -> Callable[[Principal], Awaitable[Principal]]:
    """Exige al menos uno de los permisos pedidos.

    Cada endpoint declara la acción que hace, no quién puede hacerla: quién la
    tiene lo decide la administración al armar los roles.
    """

    async def dependency(principal: PrincipalDep) -> Principal:
        try:
            ensure_permission(principal, *required)
        except MissingPermission as error:
            raise HTTPException(status.HTTP_403_FORBIDDEN, str(error)) from error
        return principal

    return dependency
