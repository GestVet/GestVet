"""Contrato HTTP del módulo de cuentas.

Estos esquemas son del adaptador, no del dominio. El registro no acepta un
campo `role`: el servidor lo fija, que es lo que evita el hallazgo P0 de la
auditoría.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from gestvet.accounts.domain.entities import Role


class RegisterClientRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    first_name: str = Field(min_length=1, max_length=80)
    last_name: str = Field(min_length=1, max_length=120)
    phone: str = Field(default="", max_length=32)


class UserResponse(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    phone: str
    role: Role
    is_active: bool
    created_at: datetime


class ClientPageResponse(BaseModel):
    items: list[UserResponse]
    total: int
