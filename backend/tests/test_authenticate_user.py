"""Pruebas del caso de uso de acceso, sin base de datos ni servidor."""

from __future__ import annotations

import pytest

from gestvet.accounts.domain.entities import Role, User
from gestvet.accounts.domain.exceptions import InactiveAccount, InvalidCredentials
from gestvet.accounts.ports.token_service import AccessToken, TokenClaims
from gestvet.accounts.use_cases.authenticate_user import (
    AuthenticateUser,
    AuthenticateUserCommand,
)
from tests.test_register_client import FakeHasher, InMemoryUserRepository

PASSWORD = "contrasena-larga"


class FakeTokenService:
    def __init__(self) -> None:
        self.issued: list[TokenClaims] = []

    def issue(self, user_id: int, role: Role) -> AccessToken:
        self.issued.append(TokenClaims(user_id=user_id, role=role))
        return AccessToken(value=f"token-{user_id}", expires_in_seconds=3600)

    def decode(self, token: str) -> TokenClaims:
        return self.issued[-1]


class CountingHasher(FakeHasher):
    """Registra cada verificación para poder afirmar que siempre ocurre."""

    def __init__(self) -> None:
        self.verifications = 0

    def verify(self, plain_password: str, password_hash: str) -> bool:
        self.verifications += 1
        return super().verify(plain_password, password_hash)


async def _repository_with(user: User) -> InMemoryUserRepository:
    users = InMemoryUserRepository()
    await users.add(user)
    return users


def _account(email: str = "ana@example.com", is_active: bool = True) -> User:
    return User(
        email=email,
        first_name="Ana",
        last_name="Quispe",
        role=Role.CLIENT,
        password_hash=FakeHasher().hash(PASSWORD),
        is_active=is_active,
    )


async def test_las_credenciales_correctas_emiten_un_token() -> None:
    users = await _repository_with(_account())
    tokens = FakeTokenService()

    session = await AuthenticateUser(users, FakeHasher(), tokens)(
        AuthenticateUserCommand(email="Ana@Example.com", password=PASSWORD)
    )

    assert session.token.value == "token-1"
    assert session.user.role is Role.CLIENT


@pytest.mark.parametrize(
    ("email", "password"),
    [
        ("ana@example.com", "otra-contrasena"),
        ("nadie@example.com", PASSWORD),
        ("no-es-un-correo", PASSWORD),
    ],
)
async def test_toda_credencial_fallida_da_el_mismo_error(email: str, password: str) -> None:
    users = await _repository_with(_account())

    with pytest.raises(InvalidCredentials):
        await AuthenticateUser(users, FakeHasher(), FakeTokenService())(
            AuthenticateUserCommand(email=email, password=password)
        )


@pytest.mark.parametrize("email", ["ana@example.com", "nadie@example.com", "no-es-un-correo"])
async def test_la_verificacion_corre_aunque_el_correo_no_exista(email: str) -> None:
    """Sin esto, un correo desconocido responde antes y delata qué cuentas hay."""
    users = await _repository_with(_account())
    hasher = CountingHasher()

    with pytest.raises(InvalidCredentials):
        await AuthenticateUser(users, hasher, FakeTokenService())(
            AuthenticateUserCommand(email=email, password="otra-contrasena")
        )

    assert hasher.verifications == 1


async def test_una_cuenta_desactivada_no_accede() -> None:
    users = await _repository_with(_account(is_active=False))

    with pytest.raises(InactiveAccount):
        await AuthenticateUser(users, FakeHasher(), FakeTokenService())(
            AuthenticateUserCommand(email="ana@example.com", password=PASSWORD)
        )
