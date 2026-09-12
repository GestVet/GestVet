"""Lector hacia datos que posee `appointments`.

Registrar un pago necesita saber si la cita existe y de qué cliente es, para
completar el pago y para poder acotar "mis pagos" a quien corresponde. Un
cobro por QR además necesita el monto: lo fija el tipo de cita por defecto,
no quien genera el QR, para que un cliente no pueda cobrarse a sí mismo por
menos de lo que corresponde. El personal sí puede ajustarlo (ver
`CreateQrCharge`), y para eso necesita saber si la cita es de emergencia: en
una cita normal el ajuste tiene un margen acotado sobre el precio de
catálogo, en una de emergencia no, porque el costo real solo se sabe al
terminar la atención. Y necesita saber si la cita ya fue atendida: el precio
solo tiene sentido una vez que se sabe qué se atendió; si el desenlace
amerita cobrar distinto (o no cobrar), eso lo decide el personal a mano.
`appointments` es otro módulo de dominio y este no puede importarlo: la
pregunta se declara acá como puerto y un adaptador la responde leyendo la
tabla ajena, igual que hacen `medical_records` y `accounts`.

Se lee, nunca se escribe.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Protocol


class AppointmentDirectory(Protocol):
    async def find_client_id(self, appointment_id: int) -> int | None: ...

    async def find_amount_due(self, appointment_id: int) -> Decimal | None: ...

    async def is_completed(self, appointment_id: int) -> bool: ...

    async def is_emergency(self, appointment_id: int) -> bool: ...
