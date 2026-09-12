"""Puerto de envío de correo.

El caso de uso arma la URL completa y le pide al adaptador que la mande: así
el negocio no sabe si el correo sale por SMTP, por una API transaccional o,
en desarrollo, por la consola.
"""

from __future__ import annotations

from typing import Protocol


class EmailSender(Protocol):
    async def send_password_reset(self, *, to: str, reset_url: str) -> None: ...
