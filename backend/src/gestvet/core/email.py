"""Adaptador de correo.

Vive en el núcleo porque no habla ningún tipo de negocio: recibe un
destinatario y una URL, y no le importa de qué caso de uso vino ninguno de
los dos. Satisface el puerto `EmailSender` de `accounts` por estructura.

`ConsoleEmailSender` es el único adaptador hoy: registra el correo en el log
en vez de mandarlo. Sirve para desarrollar y para probar sin depender de un
proveedor real, y se reemplaza por uno que sí entregue correo (SMTP, o una
API transaccional) sin tocar ningún caso de uso: el puerto no cambia.
"""

from __future__ import annotations

from gestvet.core.logs import get_logger

logger = get_logger("gestvet.email")


class ConsoleEmailSender:
    async def send_password_reset(self, *, to: str, reset_url: str) -> None:
        # El enlace va entero a propósito: es la única forma de recuperar una
        # contraseña mientras no haya un proveedor de correo. Por eso este
        # adaptador no puede quedar activo en un despliegue real.
        logger.warning("email.password_reset_not_sent", to=to, reset_url=reset_url)
