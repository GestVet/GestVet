"""Contrato HTTP del módulo de cuentas.

Estos esquemas son del adaptador, no del dominio. El registro no acepta un
campo `role`: el servidor lo fija, que es lo que evita el hallazgo P0 de la
auditoría.
"""

from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator

from gestvet.core.permissions import Permission
from gestvet.modules.accounts.domain.entities import LayoutPreferences, Role, User
from gestvet.modules.accounts.domain.specialties import Specialty, SpecialtyCategory

MIN_PASSWORD_LENGTH = 10
MAX_PASSWORD_LENGTH = 128
DOCUMENT_ID_PATTERN = r"^\d{8}$"
LAYOUT_ID_PATTERN = r"^[a-z0-9/_-]{1,64}$"
MAX_LAYOUT_ITEMS = 50
_KNOWN = frozenset(permission.value for permission in Permission)


class RegisterClientRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=MIN_PASSWORD_LENGTH, max_length=MAX_PASSWORD_LENGTH)
    first_name: str = Field(min_length=1, max_length=80)
    last_name: str = Field(min_length=1, max_length=120)
    document_id: str = Field(pattern=DOCUMENT_ID_PATTERN)
    phone: str = Field(default="", max_length=32)
    # La persona autorizó verificar su DNI. Solo se exige mientras la verificación
    # está en uso; hoy no lo está, falta el convenio con RENIEC.
    accepts_identity_check: bool = False
    # La persona aceptó los términos y condiciones; el formulario no deja enviarlo sin marcarlo.
    accepts_terms: Literal[True]


class RegisterStaffRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=MIN_PASSWORD_LENGTH, max_length=MAX_PASSWORD_LENGTH)
    first_name: str = Field(min_length=1, max_length=80)
    last_name: str = Field(min_length=1, max_length=120)
    # El rol viaja en el cuerpo pero el dominio lo acota: la lista de roles
    # asignables no incluye ADMIN, así que esta pantalla no fabrica
    # administradores por más que se le pida.
    role: Role
    # Con qué atiende: al menos una, para que el veterinario pueda encontrarse
    # desde el filtro de especialidad al reservar.
    specialty_ids: list[int] = Field(min_length=1)
    phone: str = Field(default="", max_length=32)


class RegisterWalkInClientRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=80)
    last_name: str = Field(min_length=1, max_length=120)
    document_id: str = Field(pattern=DOCUMENT_ID_PATTERN)
    phone: str = Field(default="", max_length=32)


class UpdateClientContactRequest(BaseModel):
    email: EmailStr
    phone: str = Field(default="", max_length=32)
    document_id: str = Field(default="", pattern=r"^(\d{8})?$")


class UpdateProfileRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=80)
    last_name: str = Field(min_length=1, max_length=120)
    phone: str = Field(default="", max_length=32)
    document_id: str = Field(default="", pattern=r"^(\d{8})?$")
    new_password: str | None = Field(
        default=None, min_length=MIN_PASSWORD_LENGTH, max_length=MAX_PASSWORD_LENGTH
    )


class ChangeUserStatusRequest(BaseModel):
    is_active: bool


class LoginRequest(BaseModel):
    email: EmailStr
    # Sin longitud mínima: validar aquí diría cuánto mide una contraseña válida
    # y convertiría el formulario de acceso en un oráculo.
    password: str = Field(max_length=MAX_PASSWORD_LENGTH)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=1)
    new_password: str = Field(min_length=MIN_PASSWORD_LENGTH, max_length=MAX_PASSWORD_LENGTH)


class MessageResponse(BaseModel):
    message: str


class IdentityCheckResponse(BaseModel):
    available: bool


class UserResponse(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    phone: str
    document_id: str
    role: Role
    is_active: bool
    created_at: datetime

    @classmethod
    def from_entity(cls, user: User) -> UserResponse:
        return cls(
            id=user.id or 0,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            phone=user.phone,
            document_id=user.document_id,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
        )


class CurrentUserResponse(UserResponse):
    """La cuenta propia, con lo que su rol le deja hacer.

    La interfaz oculta lo que no está permitido con esta lista; la API igual
    lo rechaza, así que ocultar es comodidad y no seguridad.
    """

    access_role_id: int | None
    access_role_name: str
    permissions: list[Permission]

    @classmethod
    def with_access(
        cls, user: User, role_id: int | None, role_name: str, permissions: frozenset[str]
    ) -> CurrentUserResponse:
        base = UserResponse.from_entity(user)
        return cls(
            **base.model_dump(),
            access_role_id=role_id,
            access_role_name=role_name,
            # Un código que ya no está en el catálogo no le sirve a la interfaz.
            permissions=sorted(Permission(code) for code in permissions if code in _KNOWN),
        )


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: CurrentUserResponse


class SpecialtyResponse(BaseModel):
    id: int
    name: str
    category: SpecialtyCategory
    category_label: str
    description: str
    is_active: bool

    @classmethod
    def from_entity(cls, specialty: Specialty) -> SpecialtyResponse:
        return cls(
            id=specialty.id or 0,
            name=specialty.name,
            category=specialty.category,
            category_label=specialty.category.label,
            description=specialty.description,
            is_active=specialty.is_active,
        )


class SpecialtyListResponse(BaseModel):
    items: list[SpecialtyResponse]


class AddSpecialtyRequest(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    category: SpecialtyCategory
    description: str = Field(default="", max_length=240)


class UpdateSpecialtyRequest(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    category: SpecialtyCategory
    description: str = Field(default="", max_length=240)
    is_active: bool


class AssignVeterinarianSpecialtiesRequest(BaseModel):
    specialty_ids: list[int] = Field(min_length=1)


class VeterinarianSpecialtiesResponse(BaseModel):
    """Especialidades asignadas a un veterinario, para la pantalla de personal."""

    user_id: int
    specialties: list[SpecialtyResponse]


class VeterinarianSpecialtiesListResponse(BaseModel):
    items: list[VeterinarianSpecialtiesResponse]


class VeterinarianResponse(BaseModel):
    """Proyección mínima para elegir veterinario al reservar.

    No trae correo ni teléfono: un cliente necesita el nombre para reservar, no
    los datos de contacto del personal.
    """

    id: int
    full_name: str
    role: Role
    average_rating: Decimal | None
    review_count: int
    specialties: list[SpecialtyResponse]

    @classmethod
    def from_entity(
        cls,
        user: User,
        average_rating: Decimal | None = None,
        review_count: int = 0,
        specialties: list[Specialty] | None = None,
    ) -> VeterinarianResponse:
        return cls(
            id=user.id or 0,
            full_name=user.full_name,
            role=user.role,
            average_rating=average_rating,
            review_count=review_count,
            specialties=[SpecialtyResponse.from_entity(item) for item in specialties or []],
        )


class VeterinarianListResponse(BaseModel):
    items: list[VeterinarianResponse]
    total: int


class ActivityResponse(BaseModel):
    id: int
    kind: str
    kind_label: str
    detail: str
    occurred_at: datetime
    user_id: int
    user_name: str
    user_role: Role


class ActivityPageResponse(BaseModel):
    items: list[ActivityResponse]
    total: int


class ClientPageResponse(BaseModel):
    items: list[UserResponse]
    total: int


class DocumentLookupRequest(BaseModel):
    document_id: str = Field(pattern=DOCUMENT_ID_PATTERN)
    # El cliente autorizó la consulta de su DNI.
    consent: Literal[True]


class DocumentLookupResponse(BaseModel):
    """Solo nombres y apellidos: nada más del DNI sale del servidor."""

    first_names: str
    last_names: str


class DashboardBlockPreferenceSchema(BaseModel):
    id: str = Field(pattern=LAYOUT_ID_PATTERN)
    visible: bool = True


class LayoutPreferencesRequest(BaseModel):
    sidebar_order: list[str] = Field(default_factory=list, max_length=MAX_LAYOUT_ITEMS)
    dashboard_blocks: list[DashboardBlockPreferenceSchema] = Field(
        default_factory=list, max_length=MAX_LAYOUT_ITEMS
    )

    @field_validator("sidebar_order")
    @classmethod
    def validate_sidebar_order(cls, items: list[str]) -> list[str]:
        pattern = re.compile(LAYOUT_ID_PATTERN)
        seen: set[str] = set()
        for item in items:
            if not pattern.fullmatch(item):
                raise ValueError(f"Identificador de ruta inválido: {item!r}")
            if item in seen:
                raise ValueError(f"Identificador duplicado en sidebar_order: {item!r}")
            seen.add(item)
        return items

    @field_validator("dashboard_blocks")
    @classmethod
    def validate_dashboard_blocks(
        cls, blocks: list[DashboardBlockPreferenceSchema]
    ) -> list[DashboardBlockPreferenceSchema]:
        seen: set[str] = set()
        for b in blocks:
            if b.id in seen:
                raise ValueError(f"Identificador de bloque duplicado: {b.id!r}")
            seen.add(b.id)
        return blocks


class LayoutPreferencesResponse(BaseModel):
    sidebar_order: list[str]
    dashboard_blocks: list[DashboardBlockPreferenceSchema]
    updated_at: datetime | None

    @classmethod
    def from_entity(cls, entity: LayoutPreferences) -> LayoutPreferencesResponse:
        return cls(
            sidebar_order=list(entity.sidebar_order),
            dashboard_blocks=[
                DashboardBlockPreferenceSchema(id=b.id, visible=b.visible)
                for b in entity.dashboard_blocks
            ],
            updated_at=entity.updated_at,
        )
