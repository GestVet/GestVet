from __future__ import annotations

from dataclasses import dataclass

from gestvet.core.activity import ActivityKind, ActivityRecorder
from gestvet.modules.accounts.domain.entities import Role, User, ensure_role_is_self_assignable
from gestvet.modules.accounts.domain.exceptions import DocumentIdRequired, EmailAlreadyRegistered
from gestvet.modules.accounts.ports.user_repository import PasswordHasher, UserRepository


@dataclass(frozen=True, slots=True)
class RegisterClientCommand:
    email: str
    password: str
    first_name: str
    last_name: str
    document_id: str
    phone: str = ""


class RegisterClient:
    def __init__(
        self,
        users: UserRepository,
        hasher: PasswordHasher,
        activity: ActivityRecorder,
    ) -> None:
        self._users = users
        self._hasher = hasher
        self._activity = activity

    async def __call__(self, command: RegisterClientCommand) -> User:
        # El rol se fija aquí, en el servidor. Nunca llega desde el cliente.
        role = Role.CLIENT
        ensure_role_is_self_assignable(role)

        if not command.document_id.strip():
            raise DocumentIdRequired()

        candidate = User(
            email=command.email,
            first_name=command.first_name.strip(),
            last_name=command.last_name.strip(),
            phone=command.phone.strip(),
            document_id=command.document_id.strip(),
            role=role,
            password_hash=self._hasher.hash(command.password),
        )

        if await self._users.exists_with_email(candidate.email):
            raise EmailAlreadyRegistered(candidate.email)

        creado = await self._users.add(candidate)
        await self._activity.record(creado.id or 0, ActivityKind.CLIENT_REGISTERED)
        return creado
