"""Enlaces firmados para compartir algo sin iniciar sesión.

Un enlace lleva un identificador y una fecha de vencimiento, firmados con
HMAC-SHA256: quien lo tiene puede abrirlo, pero nadie puede fabricar uno ni
cambiarle el identificador. La clave se deriva del secreto de la aplicación con
un propósito distinto para cada uso, así un enlace de un carnet nunca sirve
como credencial ni para otra cosa.

Python puro, sin dependencias: lo usan los casos de uso.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import UTC, datetime


def _encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _decode(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


@dataclass(frozen=True, slots=True)
class SignedReference:
    subject_id: int
    expires_at: datetime


class SignedLinks:
    def __init__(self, secret: str, *, purpose: str) -> None:
        self._key = hashlib.sha256(f"{purpose}:{secret}".encode()).digest()

    def sign(self, subject_id: int, expires_at: datetime) -> str:
        body = {"s": subject_id, "e": int(expires_at.timestamp())}
        payload = _encode(json.dumps(body, separators=(",", ":")).encode())
        return f"{payload}.{self._signature(payload)}"

    def read(self, token: str, now: datetime) -> SignedReference | None:
        """El identificador del enlace, o `None` si fue alterado o ya venció."""
        payload, _, signature = token.partition(".")
        expected = self._signature(payload)
        if not payload or not hmac.compare_digest(signature.encode(), expected.encode()):
            return None
        try:
            data = json.loads(_decode(payload))
            reference = SignedReference(
                subject_id=int(data["s"]),
                expires_at=datetime.fromtimestamp(int(data["e"]), tz=UTC),
            )
        except (ValueError, KeyError, TypeError):
            return None
        return reference if reference.expires_at > now else None

    def _signature(self, payload: str) -> str:
        return _encode(hmac.new(self._key, payload.encode(), hashlib.sha256).digest())
