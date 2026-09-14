"""Errores de dominio de la historia clínica.

Los adaptadores los traducen a códigos HTTP. El dominio no conoce HTTP.
"""

from __future__ import annotations


class MedicalRecordsError(Exception):
    """Raíz de los errores del módulo de historia clínica."""


class InvalidClinicalEntry(MedicalRecordsError):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class ClinicalEntryNotFound(MedicalRecordsError):
    def __init__(self, entry_id: int) -> None:
        super().__init__(f"No existe la entrada clínica {entry_id}.")
        self.entry_id = entry_id


class PetNotFound(MedicalRecordsError):
    def __init__(self, pet_id: int) -> None:
        super().__init__(f"No existe la mascota {pet_id}.")
        self.pet_id = pet_id


class InvalidAttachment(MedicalRecordsError):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class AttachmentNotFound(MedicalRecordsError):
    def __init__(self, attachment_id: int) -> None:
        super().__init__(f"No existe el adjunto {attachment_id}.")
        self.attachment_id = attachment_id


class InvalidVaccination(MedicalRecordsError):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class InvalidCardLink(MedicalRecordsError):
    """Alterado, vencido o de una mascota que ya no existe: se responde igual."""

    def __init__(self) -> None:
        super().__init__("Este carnet no es válido o ya venció. Pide uno nuevo a la clínica.")
