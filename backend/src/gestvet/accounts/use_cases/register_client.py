"""Caso de uso: autorregistro de un cliente."""

from __future__ import annotations

from dataclasses import dataclass

from gestvet.accounts.domain.entities import Role, User, ensure_role_is_self_assignable
from gestvet.accounts.domain.exceptions import EmailAlreadyRegistered
from gestvet.accounts.ports.user_repository import PasswordHasher, UserRepository


@dataclass(frozen=True, slots=True)
class RegisterClientCommand:
    email: str
    password: str
    first_name: str
    last_name: str
    phone: str = ""


class RegisterClient:
    def __init__(self, users: UserRepository, hasher: PasswordHasher) -> None:
        self._users = users
        self._hasher = hasher

    async def __call__(self, command: RegisterClientCommand) -> User:
        # El rol se fija aquí, en el servidor. Nunca llega desde el cliente.
        role = Role.CLIENT
        ensure_role_is_self_assignable(role)

        candidate = User(
            email=command.email,
            first_name=command.first_name.strip(),
            last_name=command.last_name.strip(),
            phone=command.phone.strip(),
            role=role,
            password_hash=self._hasher.hash(command.password),
        )

        if await self._users.exists_with_email(candidate.email):
            raise EmailAlreadyRegistered(candidate.email)

        return await self._users.add(candidate)
