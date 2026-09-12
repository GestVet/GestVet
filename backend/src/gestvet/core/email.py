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


class ConsoleEmailSender:
    async def send_password_reset(self, *, to: str, reset_url: str) -> None:
        # `print` y no `logging`: uvicorn no propaga loggers propios de la
        # aplicación a la consola salvo que alguien configure `dictConfig`, y
        # este adaptador es justamente el que se reemplaza antes de que eso
        # importe.
        print(f"Correo de recuperación para {to}: {reset_url}")
