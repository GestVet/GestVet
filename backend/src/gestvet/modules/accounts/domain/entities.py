"""Entidades de dominio de cuentas.

Python puro. Sin FastAPI, sin SQLAlchemy, sin Pydantic. Este archivo debe
poder ejecutarse sin que exista una base de datos ni un servidor web, y los
contratos de Import Linter lo verifican.
"""

from __future__ import annotations

import hashlib
import re
import secrets
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

# El rol vive en el núcleo compartido, no acá: lo necesitan todos los módulos
# para autorizar, y si lo poseyera `accounts` todos tendrían que importarlo.
from gestvet.core.identity import Role
from gestvet.modules.accounts.domain.exceptions import (
    DuplicateLayoutIdentifier,
    InvalidDocumentId,
    InvalidEmail,
    InvalidLayoutIdentifier,
    InvalidLayoutPreferences,
    LayoutLimitExceeded,
    RoleNotAssignable,
    RoleNotSelfAssignable,
)

_DOCUMENT_ID_PATTERN = re.compile(r"\d{8}")

# El hallazgo P0 de la auditoría de CitasVet fue que un visitante podía pedir
# rol de administrador al registrarse. La regla vive aquí, en el dominio, para
# que ningún adaptador pueda saltársela aceptando un rol del cuerpo HTTP.
SELF_ASSIGNABLE_ROLES: frozenset[Role] = frozenset({Role.CLIENT})

# Roles que la administración puede dar de alta. No incluye ADMIN: una cuenta
# de administración se siembra, no se crea desde una pantalla.
STAFF_ASSIGNABLE_ROLES: frozenset[Role] = frozenset({Role.VETERINARIAN})


@dataclass(slots=True)
class User:
    email: str
    first_name: str
    last_name: str
    role: Role
    password_hash: str
    phone: str = ""
    # Vacío es válido a nivel de entidad: una cuenta de personal no lo
    # necesita, y una cuenta de cliente sembrada antes de que este campo
    # existiera tampoco lo trae. Que sea obligatorio para un cliente nuevo es
    # una regla del caso de uso de registro, no de la entidad.
    document_id: str = ""
    is_active: bool = True
    id: int | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        self.email = normalize_email(self.email)
        self.document_id = validate_document_id(self.document_id)

    @property
    def full_name(self) -> str:
        full = f"{self.first_name} {self.last_name}".strip()
        return full or self.email

    def deactivate(self) -> None:
        self.is_active = False

    def activate(self) -> None:
        self.is_active = True


# Una hora es suficiente para que quien pidió el enlace lo use, y corto para
# que uno olvidado en una bandeja de entrada no quede utilizable indefinidamente.
RESET_TOKEN_TTL = timedelta(hours=1)


@dataclass(slots=True)
class PasswordResetToken:
    """Un enlace de recuperación, de un solo uso.

    Se guarda el hash del token y nunca el valor en claro, igual que una
    contraseña: quien lea la base no puede reconstruir el enlace.
    """

    user_id: int
    token_hash: str
    expires_at: datetime
    used_at: datetime | None = None
    id: int | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def is_valid(self, now: datetime) -> bool:
        return self.used_at is None and now < self.expires_at

    def mark_used(self, now: datetime) -> None:
        self.used_at = now


def generate_reset_token() -> str:
    """Valor en claro que se manda por correo. Nunca se guarda tal cual."""
    return secrets.token_urlsafe(32)


def hash_reset_token(token: str) -> str:
    """Huella del token para buscarlo y compararlo sin guardar el valor real.

    No hace falta el costo de `bcrypt`: el token ya es de alta entropía, así
    que no hay nada que una función lenta proteja contra fuerza bruta que
    SHA-256 no proteja igual.
    """
    return hashlib.sha256(token.encode()).hexdigest()


def validate_document_id(raw: str) -> str:
    value = raw.strip()
    if value and not _DOCUMENT_ID_PATTERN.fullmatch(value):
        raise InvalidDocumentId(value)
    return value


def normalize_email(raw: str) -> str:
    email = raw.strip().lower()
    local, separator, domain = email.partition("@")
    if not separator or not local or "." not in domain:
        raise InvalidEmail(raw)
    return email


def ensure_role_is_self_assignable(role: Role) -> None:
    if role not in SELF_ASSIGNABLE_ROLES:
        raise RoleNotSelfAssignable(role.value)


def ensure_role_is_staff_assignable(role: Role) -> None:
    if role not in STAFF_ASSIGNABLE_ROLES:
        raise RoleNotAssignable(role.value)


LAYOUT_ID_PATTERN = re.compile(r"^[a-z0-9/_-]{1,64}$")
MAX_LAYOUT_ITEMS = 50


@dataclass(frozen=True, slots=True)
class DashboardBlockPreference:
    """Preferencia de visualización de un bloque del panel principal.

    El identificador representa la ruta o tarjeta del bloque, y `visible`
    indica si el usuario desea mostrarlo u ocultarlo.
    """

    id: str
    visible: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not LAYOUT_ID_PATTERN.fullmatch(self.id):
            raise InvalidLayoutIdentifier(str(self.id))
        if not isinstance(self.visible, bool):
            raise InvalidLayoutPreferences("El campo 'visible' debe ser un valor booleano.")


@dataclass(frozen=True, slots=True)
class LayoutPreferences:
    """Disposición personalizada del sidebar y el panel principal.

    Value object inmutable con validación estricta: hasta 50 elementos por lista,
    identificadores con formato de ruta segura y sin elementos repetidos.
    """

    sidebar_order: tuple[str, ...] = ()
    dashboard_blocks: tuple[DashboardBlockPreference, ...] = ()
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        validate_layout_preferences(self.sidebar_order, self.dashboard_blocks)

    @classmethod
    def empty(cls) -> LayoutPreferences:
        return cls(sidebar_order=(), dashboard_blocks=(), updated_at=None)


def validate_layout_preferences(
    sidebar_order: Sequence[str],
    dashboard_blocks: Sequence[DashboardBlockPreference],
) -> None:
    if len(sidebar_order) > MAX_LAYOUT_ITEMS:
        raise LayoutLimitExceeded(MAX_LAYOUT_ITEMS)

    seen_sidebar: set[str] = set()
    for item in sidebar_order:
        if not isinstance(item, str) or not LAYOUT_ID_PATTERN.fullmatch(item):
            raise InvalidLayoutIdentifier(str(item))
        if item in seen_sidebar:
            raise DuplicateLayoutIdentifier(item)
        seen_sidebar.add(item)

    if len(dashboard_blocks) > MAX_LAYOUT_ITEMS:
        raise LayoutLimitExceeded(MAX_LAYOUT_ITEMS)

    seen_blocks: set[str] = set()
    for block in dashboard_blocks:
        if not isinstance(block, DashboardBlockPreference):
            raise InvalidLayoutPreferences("Cada bloque debe ser una preferencia válida.")
        if block.id in seen_blocks:
            raise DuplicateLayoutIdentifier(block.id)
        seen_blocks.add(block.id)


@dataclass(slots=True)
class UserLayoutPreference:
    """Entidad que vincula a un usuario con sus preferencias de interfaz."""

    user_id: int
    preferences: LayoutPreferences

    @property
    def sidebar_order(self) -> tuple[str, ...]:
        return self.preferences.sidebar_order

    @property
    def dashboard_blocks(self) -> tuple[DashboardBlockPreference, ...]:
        return self.preferences.dashboard_blocks

    @property
    def updated_at(self) -> datetime | None:
        return self.preferences.updated_at
