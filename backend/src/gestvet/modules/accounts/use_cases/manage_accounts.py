"""Casos de uso de administración de cuentas.

Alta de personal, activación y turno de guardia. Todo lo que en el original
vivía repartido entre cuatro endpoints que aceptaban cualquier rol destino.
"""

from __future__ import annotations

from dataclasses import dataclass

from gestvet.core.activity import ActivityKind, ActivityRecorder
from gestvet.core.identity import Role
from gestvet.modules.accounts.domain.entities import (
    User,
    ensure_role_is_staff_assignable,
    swapped_guard_role,
)
from gestvet.modules.accounts.domain.exceptions import (
    CannotDeactivateSelf,
    EmailAlreadyRegistered,
    UserNotFound,
)
from gestvet.modules.accounts.ports.user_repository import PasswordHasher, UserRepository


@dataclass(frozen=True, slots=True)
class RegisterStaffCommand:
    actor_id: int
    email: str
    password: str
    first_name: str
    last_name: str
    role: Role
    phone: str = ""


class RegisterStaff:
    """Alta de un veterinario. Solo la administración llega hasta acá."""

    def __init__(
        self,
        users: UserRepository,
        hasher: PasswordHasher,
        activity: ActivityRecorder,
    ) -> None:
        self._users = users
        self._hasher = hasher
        self._activity = activity

    async def __call__(self, command: RegisterStaffCommand) -> User:
        # El rol llega del cuerpo, pero acotado: la lista no incluye ADMIN, así
        # que esta pantalla no puede fabricar administradores.
        ensure_role_is_staff_assignable(command.role)

        candidate = User(
            email=command.email,
            first_name=command.first_name.strip(),
            last_name=command.last_name.strip(),
            phone=command.phone.strip(),
            role=command.role,
            password_hash=self._hasher.hash(command.password),
        )

        if await self._users.exists_with_email(candidate.email):
            raise EmailAlreadyRegistered(candidate.email)

        creado = await self._users.add(candidate)
        # El asiento lo firma quien da el alta, no la cuenta recien creada.
        await self._activity.record(command.actor_id, ActivityKind.STAFF_REGISTERED, creado.email)
        return creado


@dataclass(frozen=True, slots=True)
class ChangeUserStatusCommand:
    user_id: int
    actor_id: int
    is_active: bool


class ChangeUserStatus:
    def __init__(self, users: UserRepository, activity: ActivityRecorder) -> None:
        self._users = users
        self._activity = activity

    async def __call__(self, command: ChangeUserStatusCommand) -> User:
        # Desactivarse a uno mismo deja la clínica sin quien reactive la
        # cuenta. El original lo permitía.
        if command.user_id == command.actor_id and not command.is_active:
            raise CannotDeactivateSelf()

        user = await self._users.get(command.user_id)
        if user is None:
            raise UserNotFound(command.user_id)

        if command.is_active:
            user.activate()
        else:
            user.deactivate()

        guardado = await self._users.save(user)
        estado = "activada" if command.is_active else "desactivada"
        await self._activity.record(
            command.actor_id,
            ActivityKind.USER_STATUS_CHANGED,
            f"{guardado.email}: cuenta {estado}",
        )
        return guardado


@dataclass(frozen=True, slots=True)
class ToggleGuardDutyCommand:
    user_id: int
    actor_id: int


class ToggleGuardDuty:
    """Pone o saca a un veterinario del turno de guardia.

    Es un intercambio entre dos roles y nada más. El original tenía un endpoint
    que aceptaba el rol destino en el cuerpo, así que servía igual para
    convertir a un cliente en administrador.
    """

    def __init__(self, users: UserRepository, activity: ActivityRecorder) -> None:
        self._users = users
        self._activity = activity

    async def __call__(self, command: ToggleGuardDutyCommand) -> User:
        user = await self._users.get(command.user_id)
        if user is None:
            raise UserNotFound(command.user_id)

        user.role = swapped_guard_role(user.role)
        guardado = await self._users.save(user)
        await self._activity.record(
            command.actor_id,
            ActivityKind.GUARD_DUTY_TOGGLED,
            f"{guardado.email}: {guardado.role.label}",
        )
        return guardado


@dataclass(frozen=True, slots=True)
class UpdateProfileCommand:
    user_id: int
    first_name: str
    last_name: str
    phone: str = ""
    new_password: str | None = None


class UpdateProfile:
    """Cada cuenta edita lo suyo.

    No entran ni el correo ni el rol: el correo es la identidad con la que se
    accede y el rol lo fija el servidor.
    """

    def __init__(
        self,
        users: UserRepository,
        hasher: PasswordHasher,
        activity: ActivityRecorder,
    ) -> None:
        self._users = users
        self._hasher = hasher
        self._activity = activity

    async def __call__(self, command: UpdateProfileCommand) -> User:
        user = await self._users.get(command.user_id)
        if user is None:
            raise UserNotFound(command.user_id)

        user.first_name = command.first_name.strip()
        user.last_name = command.last_name.strip()
        user.phone = command.phone.strip()
        cambio_clave = bool(command.new_password)
        if cambio_clave:
            user.password_hash = self._hasher.hash(command.new_password or "")

        guardado = await self._users.save(user)
        await self._activity.record(
            command.user_id,
            ActivityKind.PROFILE_UPDATED,
            "con cambio de contraseña" if cambio_clave else "",
        )
        return guardado
