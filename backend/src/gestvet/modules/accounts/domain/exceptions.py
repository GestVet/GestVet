"""Errores de dominio.

Los adaptadores los traducen a códigos HTTP. El dominio no conoce HTTP.
"""

from __future__ import annotations


class AccountsError(Exception):
    """Raíz de los errores del módulo de cuentas."""


class InvalidEmail(AccountsError):
    def __init__(self, value: str) -> None:
        super().__init__(f"El correo electrónico no es válido: {value!r}")
        self.value = value


class InvalidDocumentId(AccountsError):
    def __init__(self, value: str) -> None:
        super().__init__(f"El DNI no es válido: {value!r}. Debe tener 8 dígitos.")
        self.value = value


class DocumentIdRequired(AccountsError):
    def __init__(self) -> None:
        super().__init__("El DNI es obligatorio para registrarte.")


class RoleNotSelfAssignable(AccountsError):
    def __init__(self, role: str) -> None:
        super().__init__(f"El rol {role!r} no se puede solicitar al registrarse.")
        self.role = role


class EmailAlreadyRegistered(AccountsError):
    def __init__(self, email: str) -> None:
        super().__init__(f"Ya existe una cuenta con el correo {email!r}.")
        self.email = email


class UserNotFound(AccountsError):
    def __init__(self, user_id: int) -> None:
        super().__init__(f"No existe la cuenta {user_id}.")
        self.user_id = user_id


class InvalidCredentials(AccountsError):
    """No se dice si falló el correo o la contraseña: eso enumera cuentas."""

    def __init__(self) -> None:
        super().__init__("El correo o la contraseña no son correctos.")


class InactiveAccount(AccountsError):
    def __init__(self, email: str) -> None:
        super().__init__(f"La cuenta {email!r} está desactivada.")
        self.email = email


class RoleNotAssignable(AccountsError):
    def __init__(self, role: str) -> None:
        super().__init__(f"El rol {role} no se puede asignar desde el alta de personal.")
        self.role = role


class CannotDeactivateSelf(AccountsError):
    def __init__(self) -> None:
        super().__init__("No puedes desactivar tu propia cuenta.")


class InvalidResetToken(AccountsError):
    def __init__(self) -> None:
        super().__init__("El enlace de recuperación no es válido o ya venció.")
