"""Contrato HTTP del módulo de cuentas.

Estos esquemas son del adaptador, no del dominio. El registro no acepta un
campo `role`: el servidor lo fija, que es lo que evita el hallazgo P0 de la
auditoría.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field

from gestvet.modules.accounts.domain.entities import Role, User

MIN_PASSWORD_LENGTH = 10
MAX_PASSWORD_LENGTH = 128
DOCUMENT_ID_PATTERN = r"^\d{8}$"


class RegisterClientRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=MIN_PASSWORD_LENGTH, max_length=MAX_PASSWORD_LENGTH)
    first_name: str = Field(min_length=1, max_length=80)
    last_name: str = Field(min_length=1, max_length=120)
    document_id: str = Field(pattern=DOCUMENT_ID_PATTERN)
    phone: str = Field(default="", max_length=32)


class RegisterStaffRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=MIN_PASSWORD_LENGTH, max_length=MAX_PASSWORD_LENGTH)
    first_name: str = Field(min_length=1, max_length=80)
    last_name: str = Field(min_length=1, max_length=120)
    # El rol viaja en el cuerpo pero el dominio lo acota: la lista de roles
    # asignables no incluye ADMIN, así que esta pantalla no fabrica
    # administradores por más que se le pida.
    role: Role
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


class ToggleEmergencyCoverageRequest(BaseModel):
    can_cover_emergencies: bool


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


class UserResponse(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    phone: str
    document_id: str
    role: Role
    is_active: bool
    can_cover_emergencies: bool
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
            can_cover_emergencies=user.can_cover_emergencies,
            created_at=user.created_at,
        )


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


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

    @classmethod
    def from_entity(
        cls,
        user: User,
        average_rating: Decimal | None = None,
        review_count: int = 0,
    ) -> VeterinarianResponse:
        return cls(
            id=user.id or 0,
            full_name=user.full_name,
            role=user.role,
            average_rating=average_rating,
            review_count=review_count,
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
