"""Errores de dominio de accesos.

Los adaptadores los traducen a códigos HTTP. El dominio no conoce HTTP.
"""

from __future__ import annotations


class AccessError(Exception):
    """Raíz de los errores del módulo de accesos."""


class InvalidAccessRole(AccessError):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class AccessRoleNotFound(AccessError):
    def __init__(self, role_id: int) -> None:
        super().__init__(f"No existe el rol {role_id}.")
        self.role_id = role_id


class AccountNotFound(AccessError):
    def __init__(self, user_id: int) -> None:
        super().__init__(f"No existe la cuenta {user_id}.")
        self.user_id = user_id


class RoleNameTaken(AccessError):
    def __init__(self, name: str) -> None:
        super().__init__(f"Ya existe un rol llamado {name!r}.")
        self.name = name


class RoleInUse(AccessError):
    def __init__(self, assigned: int) -> None:
        super().__init__(
            f"El rol está asignado a {assigned} cuenta(s). Reasígnalas antes de borrarlo."
        )
        self.assigned = assigned


class AccessRoleLocked(AccessError):
    """Un cambio que dejaría a la clínica sin poder administrar roles."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class RoleKindMismatch(AccessError):
    def __init__(self, role_kind: str, account_kind: str) -> None:
        super().__init__(
            f"Ese rol es para cuentas de tipo {role_kind!r} y la cuenta es de tipo "
            f"{account_kind!r}."
        )
        self.role_kind = role_kind
        self.account_kind = account_kind
