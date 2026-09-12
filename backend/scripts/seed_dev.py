"""Siembra cuentas de prueba en la base de desarrollo.

Existe para poder abrir las pantallas privadas de cada rol sin registrar a mano
un cliente y sin tocar la base para crear personal, que el registro público no
permite. Todas las cuentas comparten la contraseña `DEMO_PASSWORD` y usan el
dominio reservado example.com, así que ninguna puede confundirse con una
persona real.

Es idempotente: una cuenta que ya existe se deja como está. Se niega a correr
contra una base que no sea local.

Uso:
    uv run --directory backend python scripts/seed_dev.py
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import date

from sqlalchemy.engine import make_url

from gestvet.core.config import get_settings
from gestvet.core.database import SessionFactory, engine
from gestvet.core.identity import Role
from gestvet.core.security import BcryptPasswordHasher
from gestvet.modules.accounts.adapters.persistence.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from gestvet.modules.accounts.domain.entities import User
from gestvet.modules.pets.adapters.persistence.sqlalchemy_pet_repository import (
    SqlAlchemyPetRepository,
)
from gestvet.modules.pets.domain.entities import Pet, PetSex

DEMO_PASSWORD = "gestvet-demo-2026"

# SQLite no tiene host; Postgres local se escribe de cualquiera de estas formas.
LOCAL_HOSTS = {None, "localhost", "127.0.0.1", "::1"}


@dataclass(frozen=True, slots=True)
class DemoAccount:
    email: str
    first_name: str
    role: Role
    document_id: str = ""


ACCOUNTS = (
    DemoAccount("admin.demo@example.com", "Admin", Role.ADMIN),
    DemoAccount("cliente.demo@example.com", "Cliente", Role.CLIENT, document_id="10000001"),
    DemoAccount("veterinario.demo@example.com", "Veterinario", Role.VETERINARIAN),
    DemoAccount("guardia.demo@example.com", "Guardia", Role.EMERGENCY_VETERINARIAN),
)


def _is_local_database(database_url: str) -> bool:
    return make_url(database_url).host in LOCAL_HOSTS


async def seed() -> list[str]:
    password_hash = BcryptPasswordHasher().hash(DEMO_PASSWORD)
    report: list[str] = []
    async with SessionFactory() as session:
        users = SqlAlchemyUserRepository(session)
        pets = SqlAlchemyPetRepository(session)
        for account in ACCOUNTS:
            if await users.get_by_email(account.email) is not None:
                report.append(f"ya existía  {account.email}")
                continue
            user = await users.add(
                User(
                    email=account.email,
                    first_name=account.first_name,
                    last_name="Demo",
                    role=account.role,
                    password_hash=password_hash,
                    document_id=account.document_id,
                )
            )
            # Un cliente sin mascotas deja vacías la reserva y la historia
            # clínica, que son justo las pantallas que se quieren revisar.
            if user.role is Role.CLIENT and user.id is not None:
                await pets.add(
                    Pet(
                        name="Firulais",
                        species="Perro",
                        breed="Mestizo",
                        birth_date=date(2021, 3, 14),
                        owner_id=user.id,
                        sex=PetSex.MALE,
                    )
                )
            report.append(f"creada      {account.email} ({account.role.label})")
        await session.commit()
    await engine.dispose()
    return report


def main() -> int:
    database_url = get_settings().database_url
    if not _is_local_database(database_url):
        print("La base configurada no es local. Las cuentas de prueba no se siembran ahí.")
        return 1
    for line in asyncio.run(seed()):
        print(line)
    print(f"Contraseña de todas las cuentas: {DEMO_PASSWORD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
