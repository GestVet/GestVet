"""Casos de uso de administración de cuentas.

Alta de personal, activación y turno de guardia. Todo lo que en el original
vivía repartido entre cuatro endpoints que aceptaban cualquier rol destino.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass

from gestvet.core.activity import ActivityKind, ActivityRecorder
from gestvet.core.identity import Role
from gestvet.modules.accounts.domain.entities import (
    User,
    ensure_role_is_backup_eligible,
    ensure_role_is_staff_assignable,
    normalize_email,
    swapped_guard_role,
    validate_document_id,
)
from gestvet.modules.accounts.domain.exceptions import (
    CannotDeactivateSelf,
    DocumentIdRequired,
    EmailAlreadyRegistered,
    UserNotFound,
    VeterinarianHasUpcomingAppointments,
)
from gestvet.modules.accounts.ports.appointment_directory import AppointmentDirectory
from gestvet.modules.accounts.ports.user_repository import PasswordHasher, UserRepository

# Dominio reservado, nunca resuelve de verdad: nadie puede recibir un correo
# a esta dirección, así que no hay forma de que alguien "reclame" la cuenta
# por accidente antes de que el personal cargue el correo real.
PLACEHOLDER_EMAIL_DOMAIN = "pendiente.gestvet.local"


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

    def __init__(
        self,
        users: UserRepository,
        activity: ActivityRecorder,
        appointments: AppointmentDirectory,
    ) -> None:
        self._users = users
        self._activity = activity
        self._appointments = appointments

    async def __call__(self, command: ToggleGuardDutyCommand) -> User:
        user = await self._users.get(command.user_id)
        if user is None:
            raise UserNotFound(command.user_id)

        if user.role is Role.VETERINARIAN:
            # De guardia solo recibe emergencias. Si ya tiene citas normales
            # asignadas, quedarían sin nadie que las atienda.
            if await self._appointments.has_upcoming_normal_appointments(command.user_id):
                raise VeterinarianHasUpcomingAppointments(command.user_id)

        user.role = swapped_guard_role(user.role)
        guardado = await self._users.save(user)
        await self._activity.record(
            command.actor_id,
            ActivityKind.GUARD_DUTY_TOGGLED,
            f"{guardado.email}: {guardado.role.label}",
        )
        return guardado


@dataclass(frozen=True, slots=True)
class ToggleEmergencyCoverageCommand:
    user_id: int
    actor_id: int
    can_cover_emergencies: bool


class ToggleEmergencyCoverage:
    """Habilita o quita a un veterinario normal como respaldo de emergencias.

    Solo tiene sentido en un veterinario normal: el de guardia ya atiende
    emergencias por su rol, y ni el cliente ni la administración atienden
    ninguna cita.
    """

    def __init__(self, users: UserRepository, activity: ActivityRecorder) -> None:
        self._users = users
        self._activity = activity

    async def __call__(self, command: ToggleEmergencyCoverageCommand) -> User:
        user = await self._users.get(command.user_id)
        if user is None:
            raise UserNotFound(command.user_id)

        ensure_role_is_backup_eligible(user.role)
        user.can_cover_emergencies = command.can_cover_emergencies

        guardado = await self._users.save(user)
        estado = "habilitado" if command.can_cover_emergencies else "deshabilitado"
        await self._activity.record(
            command.actor_id,
            ActivityKind.GUARD_DUTY_TOGGLED,
            f"{guardado.email}: respaldo de emergencias {estado}",
        )
        return guardado


@dataclass(frozen=True, slots=True)
class UpdateProfileCommand:
    user_id: int
    first_name: str
    last_name: str
    phone: str = ""
    document_id: str = ""
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
        user.document_id = validate_document_id(command.document_id)
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


@dataclass(frozen=True, slots=True)
class RegisterWalkInClientCommand:
    actor_id: int
    first_name: str
    last_name: str
    document_id: str
    phone: str = ""


class RegisterWalkInClient:
    """Alta de un cliente sin correo ni contraseña, para una emergencia.

    No hay tiempo de pedirle un correo a alguien que llega sin cita ni cuenta:
    la cuenta nace con un correo de relleno, inutilizable para entrar, y el
    personal la completa con calma después con `UpdateClientContact`. Hasta
    entonces el DNI es el único dato real que la identifica.
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

    async def __call__(self, command: RegisterWalkInClientCommand) -> User:
        if not command.document_id.strip():
            raise DocumentIdRequired()

        placeholder_email = f"pendiente-{secrets.token_hex(8)}@{PLACEHOLDER_EMAIL_DOMAIN}"
        candidate = User(
            email=placeholder_email,
            first_name=command.first_name.strip(),
            last_name=command.last_name.strip(),
            phone=command.phone.strip(),
            document_id=command.document_id.strip(),
            role=Role.CLIENT,
            password_hash=self._hasher.hash(secrets.token_urlsafe(32)),
        )

        creado = await self._users.add(candidate)
        await self._activity.record(
            command.actor_id,
            ActivityKind.CLIENT_REGISTERED,
            f"alta exprés de emergencia: {creado.full_name}",
        )
        return creado


@dataclass(frozen=True, slots=True)
class UpdateClientContactCommand:
    user_id: int
    actor_id: int
    email: str
    phone: str = ""
    document_id: str = ""


class UpdateClientContact:
    """Completa el correo real de un cliente dado de alta por emergencia.

    Lo hace el personal, no el propio cliente: mientras el correo siga siendo
    el de relleno, la cuenta no tiene forma de autenticarse para editarse a
    sí misma.
    """

    def __init__(self, users: UserRepository, activity: ActivityRecorder) -> None:
        self._users = users
        self._activity = activity

    async def __call__(self, command: UpdateClientContactCommand) -> User:
        user = await self._users.get(command.user_id)
        if user is None:
            raise UserNotFound(command.user_id)

        normalized = normalize_email(command.email)
        if normalized != user.email and await self._users.exists_with_email(normalized):
            raise EmailAlreadyRegistered(normalized)

        user.email = normalized
        if command.phone:
            user.phone = command.phone.strip()
        if command.document_id:
            user.document_id = validate_document_id(command.document_id)

        guardado = await self._users.save(user)
        await self._activity.record(
            command.actor_id,
            ActivityKind.PROFILE_UPDATED,
            f"{guardado.email}: contacto completado por el personal",
        )
        return guardado
