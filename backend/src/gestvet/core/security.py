from __future__ import annotations

import bcrypt


class BcryptPasswordHasher:
    """Adaptador del puerto `PasswordHasher`.

    Se declara en el núcleo porque lo comparten varios módulos, y satisface el
    protocolo por estructura: no hereda de él, así que el dominio nunca es
    importado desde aquí.
    """

    def __init__(self, rounds: int = 12) -> None:
        self._rounds = rounds

    def hash(self, plain_password: str) -> str:
        salt = bcrypt.gensalt(rounds=self._rounds)
        return bcrypt.hashpw(plain_password.encode(), salt).decode()

    def verify(self, plain_password: str, password_hash: str) -> bool:
        try:
            return bcrypt.checkpw(plain_password.encode(), password_hash.encode())
        except ValueError:
            return False
