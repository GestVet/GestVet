from __future__ import annotations

from datetime import datetime

from gestvet.core.clinic_time import CLINIC_UTC_OFFSET


class AvailabilityError(Exception):
    """Raíz de los errores del módulo de agenda."""


class InvalidSlot(AvailabilityError):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class OverlappingSlot(AvailabilityError):
    def __init__(self, starts_at: datetime | None = None) -> None:
        detalle = ""
        if starts_at is not None:
            local = starts_at + CLINIC_UTC_OFFSET
            detalle = f" el {local:%d/%m/%Y} a las {local:%H:%M}"
        super().__init__(f"El turno se cruza con otro del mismo veterinario{detalle}.")
        self.starts_at = starts_at


class SlotNotFound(AvailabilityError):
    def __init__(self, slot_id: int) -> None:
        super().__init__(f"No existe el turno {slot_id}.")
        self.slot_id = slot_id


class VeterinarianNotFound(AvailabilityError):
    def __init__(self, veterinarian_id: int) -> None:
        super().__init__("Los turnos solo se asignan a un veterinario con la cuenta activa.")
        self.veterinarian_id = veterinarian_id


class ShiftHasAppointments(AvailabilityError):
    def __init__(self, slot_id: int) -> None:
        super().__init__(
            "Ese turno tiene citas reservadas. Reprográmalas o cancélalas antes de quitarlo."
        )
        self.slot_id = slot_id


class InvalidChangeRequest(AvailabilityError):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class ChangeRequestNotFound(AvailabilityError):
    def __init__(self, request_id: int) -> None:
        super().__init__(f"No existe el pedido de cambio {request_id}.")
        self.request_id = request_id


class ChangeRequestAlreadyResolved(AvailabilityError):
    def __init__(self) -> None:
        super().__init__("Ese pedido ya tiene respuesta.")
