"""Pruebas de los casos de uso de recuperación de contraseña, sin base ni servidor."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from gestvet.core.identity import Role
from gestvet.modules.accounts.domain.entities import (
    PasswordResetToken,
    User,
    generate_reset_token,
    hash_reset_token,
)
from gestvet.modules.accounts.domain.exceptions import InvalidResetToken
from gestvet.modules.accounts.use_cases.request_password_reset import (
    RequestPasswordReset,
    RequestPasswordResetCommand,
)
from gestvet.modules.accounts.use_cases.reset_password import ResetPassword, ResetPasswordCommand
from tests.test_register_client import FakeHasher, InMemoryUserRepository

PASSWORD = "contrasena-larga"
FRONTEND_URL = "http://localhost:5173"


class InMemoryPasswordResetRepository:
    def __init__(self) -> None:
        self.rows: list[PasswordResetToken] = []
        self._next_id = 1

    async def add(self, token: PasswordResetToken) -> PasswordResetToken:
        token.id = self._next_id
        self._next_id += 1
        self.rows.append(token)
        return token

    async def get_by_hash(self, token_hash: str) -> PasswordResetToken | None:
        return next((row for row in self.rows if row.token_hash == token_hash), None)

    async def save(self, token: PasswordResetToken) -> PasswordResetToken:
        self.rows = [token if row.id == token.id else row for row in self.rows]
        return token


class FakeEmailSender:
    def __init__(self) -> None:
        self.sent: list[tuple[str, str]] = []

    async def send_password_reset(self, *, to: str, reset_url: str) -> None:
        self.sent.append((to, reset_url))


def _account(email: str = "ana@example.com", is_active: bool = True) -> User:
    return User(
        email=email,
        first_name="Ana",
        last_name="Quispe",
        role=Role.CLIENT,
        password_hash=FakeHasher().hash(PASSWORD),
        is_active=is_active,
    )


async def test_pedir_recuperacion_manda_un_correo_con_el_token() -> None:
    users = InMemoryUserRepository()
    await users.add(_account())
    tokens = InMemoryPasswordResetRepository()
    email_sender = FakeEmailSender()

    await RequestPasswordReset(users, tokens, email_sender, FRONTEND_URL)(
        RequestPasswordResetCommand(email="Ana@Example.com")
    )

    assert len(tokens.rows) == 1
    assert len(email_sender.sent) == 1
    destinatario, url = email_sender.sent[0]
    assert destinatario == "ana@example.com"
    assert url.startswith(f"{FRONTEND_URL}/restablecer-contrasena?token=")


@pytest.mark.parametrize("email", ["nadie@example.com", "no-es-un-correo"])
async def test_pedir_recuperacion_no_manda_nada_si_no_hay_cuenta(email: str) -> None:
    """Ni un correo inexistente ni uno mal formado dejan rastro distinguible."""
    users = InMemoryUserRepository()
    await users.add(_account())
    tokens = InMemoryPasswordResetRepository()
    email_sender = FakeEmailSender()

    await RequestPasswordReset(users, tokens, email_sender, FRONTEND_URL)(
        RequestPasswordResetCommand(email=email)
    )

    assert tokens.rows == []
    assert email_sender.sent == []


async def test_pedir_recuperacion_no_manda_nada_a_una_cuenta_desactivada() -> None:
    users = InMemoryUserRepository()
    await users.add(_account(is_active=False))
    tokens = InMemoryPasswordResetRepository()
    email_sender = FakeEmailSender()

    await RequestPasswordReset(users, tokens, email_sender, FRONTEND_URL)(
        RequestPasswordResetCommand(email="ana@example.com")
    )

    assert tokens.rows == []
    assert email_sender.sent == []


async def test_restablecer_con_el_token_correcto_cambia_la_contrasena() -> None:
    users = InMemoryUserRepository()
    cuenta = await users.add(_account())
    tokens = InMemoryPasswordResetRepository()
    plano = generate_reset_token()
    await tokens.add(
        PasswordResetToken(
            user_id=cuenta.id or 0,
            token_hash=hash_reset_token(plano),
            expires_at=datetime.now(UTC) + timedelta(hours=1),
        )
    )

    await ResetPassword(users, tokens, FakeHasher())(
        ResetPasswordCommand(token=plano, new_password="otra-contrasena-larga")
    )

    actualizada = await users.get_by_email("ana@example.com")
    assert actualizada is not None
    assert FakeHasher().verify("otra-contrasena-larga", actualizada.password_hash)


async def test_el_token_no_sirve_una_segunda_vez() -> None:
    users = InMemoryUserRepository()
    cuenta = await users.add(_account())
    tokens = InMemoryPasswordResetRepository()
    plano = generate_reset_token()
    await tokens.add(
        PasswordResetToken(
            user_id=cuenta.id or 0,
            token_hash=hash_reset_token(plano),
            expires_at=datetime.now(UTC) + timedelta(hours=1),
        )
    )
    reset = ResetPassword(users, tokens, FakeHasher())
    await reset(ResetPasswordCommand(token=plano, new_password="otra-contrasena-larga"))

    with pytest.raises(InvalidResetToken):
        await reset(ResetPasswordCommand(token=plano, new_password="una-tercera-contrasena"))


async def test_un_token_vencido_no_sirve() -> None:
    users = InMemoryUserRepository()
    cuenta = await users.add(_account())
    tokens = InMemoryPasswordResetRepository()
    plano = generate_reset_token()
    await tokens.add(
        PasswordResetToken(
            user_id=cuenta.id or 0,
            token_hash=hash_reset_token(plano),
            expires_at=datetime.now(UTC) - timedelta(minutes=1),
        )
    )

    with pytest.raises(InvalidResetToken):
        await ResetPassword(users, tokens, FakeHasher())(
            ResetPasswordCommand(token=plano, new_password="otra-contrasena-larga")
        )


async def test_un_token_inventado_no_sirve() -> None:
    users = InMemoryUserRepository()
    await users.add(_account())
    tokens = InMemoryPasswordResetRepository()

    with pytest.raises(InvalidResetToken):
        await ResetPassword(users, tokens, FakeHasher())(
            ResetPasswordCommand(token="token-que-nunca-se-emitio", new_password=PASSWORD)
        )
