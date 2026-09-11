"""Pruebas de los casos de uso sin base de datos ni servidor.

Esto es lo que compra la arquitectura hexagonal: el repositorio en memoria
satisface el puerto por estructura, así que el caso de uso no distingue.
"""

from __future__ import annotations

import pytest

from gestvet.core.identity import Role
from gestvet.core.pagination import Page
from gestvet.modules.accounts.domain.entities import User, normalize_email
from gestvet.modules.accounts.domain.exceptions import (
    EmailAlreadyRegistered,
    InvalidEmail,
    RoleNotSelfAssignable,
)
from gestvet.modules.accounts.ports.user_repository import UserQuery
from gestvet.modules.accounts.use_cases.list_clients import (
    CLIENT_ROLES,
    ListUsers,
    resolve_ordering,
)
from gestvet.modules.accounts.use_cases.register_client import RegisterClient, RegisterClientCommand


class InMemoryUserRepository:
    def __init__(self) -> None:
        self.rows: list[User] = []
        self._next_id = 1

    async def add(self, user: User) -> User:
        user.id = self._next_id
        self._next_id += 1
        self.rows.append(user)
        return user

    async def get(self, user_id: int) -> User | None:
        return next((row for row in self.rows if row.id == user_id), None)

    async def get_by_email(self, email: str) -> User | None:
        return next((row for row in self.rows if row.email == email), None)

    async def exists_with_email(self, email: str) -> bool:
        return any(row.email == email for row in self.rows)

    async def save(self, user: User) -> User:
        self.rows = [user if row.id == user.id else row for row in self.rows]
        return user

    async def search(self, query: UserQuery) -> Page[User]:
        roles = query.roles or set()
        matches = [row for row in self.rows if row.role in roles]
        window = matches[query.offset : query.offset + query.limit]
        return Page(items=window, total=len(matches))


class FakeHasher:
    def hash(self, plain_password: str) -> str:
        return f"fake${plain_password}"

    def verify(self, plain_password: str, password_hash: str) -> bool:
        return password_hash == f"fake${plain_password}"

    def dummy_hash(self) -> str:
        return "fake$ninguna-contrasena-produce-esto"


async def test_registro_crea_un_cliente_y_nunca_otro_rol() -> None:
    users = InMemoryUserRepository()
    register = RegisterClient(users, FakeHasher())

    created = await register(
        RegisterClientCommand(
            email="Ana.Quispe@Example.com",
            password="contrasena-larga",
            first_name="Ana",
            last_name="Quispe",
        )
    )

    assert created.role is Role.CLIENT
    assert created.email == "ana.quispe@example.com"
    assert created.password_hash != "contrasena-larga"


async def test_registro_rechaza_un_correo_repetido() -> None:
    users = InMemoryUserRepository()
    register = RegisterClient(users, FakeHasher())
    command = RegisterClientCommand(
        email="ana@example.com",
        password="contrasena-larga",
        first_name="Ana",
        last_name="Quispe",
    )
    await register(command)

    with pytest.raises(EmailAlreadyRegistered):
        await register(command)


@pytest.mark.parametrize("raw", ["sin-arroba", "@example.com", "ana@sinpunto", ""])
def test_correo_invalido(raw: str) -> None:
    with pytest.raises(InvalidEmail):
        normalize_email(raw)


@pytest.mark.parametrize(
    "role",
    [Role.ADMIN, Role.VETERINARIAN, Role.EMERGENCY_VETERINARIAN],
)
def test_ningun_rol_privilegiado_es_autoasignable(role: Role) -> None:
    """Cierra el hallazgo P0 de la auditoría de CitasVet."""
    from gestvet.modules.accounts.domain.entities import ensure_role_is_self_assignable

    with pytest.raises(RoleNotSelfAssignable):
        ensure_role_is_self_assignable(role)


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [
        (None, "last_name"),
        ("email", "email"),
        ("-created_at", "-created_at"),
        ("password_hash", "last_name"),
        ("-password_hash", "last_name"),
    ],
)
def test_el_ordenamiento_solo_acepta_columnas_de_la_lista_blanca(
    entrada: str | None, esperado: str
) -> None:
    assert resolve_ordering(entrada) == esperado


async def test_listado_solo_devuelve_clientes() -> None:
    users = InMemoryUserRepository()
    await users.add(
        User(
            email="admin@example.com",
            first_name="Admin",
            last_name="Root",
            role=Role.ADMIN,
            password_hash="x",
        )
    )
    await users.add(
        User(
            email="ana@example.com",
            first_name="Ana",
            last_name="Quispe",
            role=Role.CLIENT,
            password_hash="x",
        )
    )

    page = await ListUsers(users, CLIENT_ROLES)(UserQuery())

    assert page.total == 1
    assert page.items[0].email == "ana@example.com"
