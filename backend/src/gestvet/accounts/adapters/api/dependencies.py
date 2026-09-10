"""Cableado del adaptador HTTP.

Las dependencias se declaran como proveedores en lugar de instanciarse dentro
de cada endpoint. Eso es lo que permite que una prueba sustituya el repositorio
o el emisor de tokens sin levantar una base de datos.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from gestvet.accounts.adapters.persistence.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from gestvet.accounts.adapters.security.jwt_token_service import JwtTokenService
from gestvet.accounts.domain.entities import Role, User, ensure_role_is_allowed
from gestvet.accounts.domain.exceptions import InvalidToken, PermissionDenied
from gestvet.accounts.ports.token_service import TokenService
from gestvet.accounts.ports.user_repository import PasswordHasher, UserRepository
from gestvet.core.config import get_settings
from gestvet.core.database import get_session
from gestvet.core.security import BcryptPasswordHasher

# `auto_error=False` para responder con el mensaje del proyecto en vez del
# texto que trae Starlette cuando falta la cabecera.
bearer_scheme = HTTPBearer(auto_error=False, description="Token emitido por /api/v1/auth/login")

UNAUTHENTICATED_HEADERS = {"WWW-Authenticate": "Bearer"}

SessionDep = Annotated[AsyncSession, Depends(get_session)]
CredentialsDep = Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)]


def get_user_repository(session: SessionDep) -> UserRepository:
    return SqlAlchemyUserRepository(session)


def get_password_hasher() -> PasswordHasher:
    return BcryptPasswordHasher()


def get_token_service() -> TokenService:
    settings = get_settings()
    return JwtTokenService(
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        ttl_seconds=settings.access_token_ttl_seconds,
    )


UserRepositoryDep = Annotated[UserRepository, Depends(get_user_repository)]
PasswordHasherDep = Annotated[PasswordHasher, Depends(get_password_hasher)]
TokenServiceDep = Annotated[TokenService, Depends(get_token_service)]


def _unauthenticated(detail: str) -> HTTPException:
    return HTTPException(status.HTTP_401_UNAUTHORIZED, detail, headers=UNAUTHENTICATED_HEADERS)


async def get_current_user(
    credentials: CredentialsDep,
    users: UserRepositoryDep,
    tokens: TokenServiceDep,
) -> User:
    if credentials is None:
        raise _unauthenticated("Falta la credencial de acceso.")

    try:
        claims = tokens.decode(credentials.credentials)
    except InvalidToken as error:
        raise _unauthenticated(str(error)) from error

    # El rol se relee de la base y no se toma del token: así una cuenta
    # degradada o desactivada pierde el acceso sin esperar a que expire.
    user = await users.get(claims.user_id)
    if user is None or not user.is_active:
        raise _unauthenticated("La cuenta ya no está disponible.")
    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]


def require_roles(*allowed: Role) -> Callable[[User], Awaitable[User]]:
    """Construye una dependencia que exige uno de estos roles."""
    permitted = frozenset(allowed)

    async def dependency(current_user: CurrentUserDep) -> User:
        try:
            ensure_role_is_allowed(current_user.role, permitted)
        except PermissionDenied as error:
            raise HTTPException(status.HTTP_403_FORBIDDEN, str(error)) from error
        return current_user

    return dependency
