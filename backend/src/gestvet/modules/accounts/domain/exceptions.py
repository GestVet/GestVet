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


class IdentityCheckConsentRequired(AccountsError):
    def __init__(self) -> None:
        super().__init__("Necesitamos tu autorización para verificar tu DNI.")


class TermsNotAccepted(AccountsError):
    def __init__(self) -> None:
        super().__init__("Debes aceptar los términos y condiciones para registrarte.")


class DocumentNotFoundInRegistry(AccountsError):
    def __init__(self) -> None:
        super().__init__("No encontramos ese DNI. Revisa el número.")


class IdentityMismatch(AccountsError):
    """No dice qué nombre figura: el formulario es público."""

    def __init__(self) -> None:
        super().__init__(
            "El nombre o el apellido no coinciden con los de tu DNI. "
            "Escríbelos como figuran en el documento."
        )


class InvalidSpecialty(AccountsError):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class SpecialtyNotFound(AccountsError):
    def __init__(self, specialty_id: int) -> None:
        super().__init__(f"No existe la especialidad {specialty_id}.")
        self.specialty_id = specialty_id


class SpecialtyNameTaken(AccountsError):
    def __init__(self, name: str) -> None:
        super().__init__(f"Ya existe «{name}» en el catálogo de especialidades.")
        self.name = name


class SpecialtiesRequired(AccountsError):
    def __init__(self) -> None:
        super().__init__("Elige al menos una especialidad para el veterinario.")


class UnknownSpecialties(AccountsError):
    """Alguno de los identificadores no corresponde a una especialidad que exista."""

    def __init__(self, specialty_ids: frozenset[int]) -> None:
        listado = ", ".join(str(entry_id) for entry_id in sorted(specialty_ids))
        super().__init__(f"Estas especialidades no existen: {listado}.")
        self.specialty_ids = specialty_ids


class InvalidLayoutPreferences(AccountsError):
    """Raíz de errores de validación en las preferencias de interfaz."""


class InvalidLayoutIdentifier(InvalidLayoutPreferences):
    def __init__(self, value: str) -> None:
        super().__init__(
            f"El identificador {value!r} no es válido. "
            "Debe coincidir con el patrón ^[a-z0-9/_-]{1,64}$."
        )
        self.value = value


class DuplicateLayoutIdentifier(InvalidLayoutPreferences):
    def __init__(self, value: str) -> None:
        super().__init__(f"El identificador {value!r} está duplicado.")
        self.value = value


class LayoutLimitExceeded(InvalidLayoutPreferences):
    def __init__(self, limit: int = 50) -> None:
        super().__init__(f"La lista no puede superar el límite de {limit} elementos.")
        self.limit = limit
