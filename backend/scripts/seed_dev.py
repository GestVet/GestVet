"""Siembra cuentas de prueba en la base de desarrollo.

Existe para poder abrir las pantallas privadas de cada rol sin registrar a mano
un cliente y sin tocar la base para crear personal, que el registro público no
permite. Todas las cuentas comparten la contraseña `DEMO_PASSWORD` y usan el
dominio reservado example.com, así que ninguna puede confundirse con una
persona real.

También les asigna turnos a los dos veterinarios de prueba, para que la reserva
tenga horas que ofrecer y las emergencias alguien de guardia.

Es idempotente: una cuenta que ya existe se deja como está, y un veterinario
que ya tiene turnos por delante no recibe otros. Se niega a correr salvo que se
cumplan dos condiciones a la vez: la base es local y `DEBUG` está activo. Mirar
solo el host no alcanza: un túnel SSH a la base de producción también se ve
como `127.0.0.1`, y sembraría ahí cuentas con una contraseña que está escrita
en este archivo. Un despliegue corre con `DEBUG=false`, así que la segunda
condición lo deja afuera aunque la base parezca local.

Uso:
    uv run --directory backend python scripts/seed_dev.py
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta

from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession

from gestvet.core.clinic_time import clinic_date
from gestvet.core.config import get_settings
from gestvet.core.database import SessionFactory, engine
from gestvet.core.identity import Role
from gestvet.core.security import BcryptPasswordHasher
from gestvet.modules.accounts.adapters.persistence.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from gestvet.modules.accounts.domain.entities import User
from gestvet.modules.availability.adapters.persistence.sqlalchemy_availability_repository import (
    SqlAlchemyAvailabilityRepository,
)
from gestvet.modules.availability.domain.entities import ShiftKind
from gestvet.modules.availability.domain.weekly_plan import WeeklyShift, expand_weekly_plan
from gestvet.modules.availability.ports.availability_repository import SlotQuery
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
    DemoAccount("guardia.demo@example.com", "Guardia", Role.VETERINARIAN),
)

# Un horario como el de una clínica de Trujillo: atención de lunes a sábado y
# guardia nocturna todos los días.
_ATENCION = tuple(WeeklyShift(weekday=dia, starts=time(9), ends=time(18)) for dia in range(6))
_GUARDIA = tuple(
    WeeklyShift(weekday=dia, starts=time(20), ends=time(8), kind=ShiftKind.ON_CALL)
    for dia in range(7)
)
DEMO_SHIFTS = {
    "veterinario.demo@example.com": _ATENCION,
    "guardia.demo@example.com": _GUARDIA,
}
DEMO_WEEKS = 4


def _is_local_database(database_url: str) -> bool:
    return make_url(database_url).host in LOCAL_HOSTS


async def _seed_accounts(session: AsyncSession, report: list[str]) -> None:
    password_hash = BcryptPasswordHasher().hash(DEMO_PASSWORD)
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


async def _seed_shifts(session: AsyncSession, report: list[str]) -> None:
    users = SqlAlchemyUserRepository(session)
    slots = SqlAlchemyAvailabilityRepository(session)
    ahora = datetime.now(UTC)
    # Desde mañana: un turno de hoy que ya empezó confundiría la reserva.
    manana = clinic_date(ahora) + timedelta(days=1)
    for email, plan in DEMO_SHIFTS.items():
        user = await users.get_by_email(email)
        if user is None or user.id is None:
            continue
        if await slots.list(SlotQuery(veterinarian_id=user.id, starts_after=ahora)):
            report.append(f"ya tenía turnos {email}")
            continue
        await slots.add_many(expand_weekly_plan(user.id, manana, DEMO_WEEKS, plan))
        report.append(f"turnos      {email} ({DEMO_WEEKS} semanas)")


async def seed() -> list[str]:
    report: list[str] = []
    async with SessionFactory() as session:
        await _seed_accounts(session, report)
        await session.flush()
        await _seed_shifts(session, report)
        await session.commit()
    await engine.dispose()
    return report


def main() -> int:
    settings = get_settings()
    if not settings.debug:
        print("DEBUG está desactivado. Las cuentas de prueba solo se siembran en desarrollo.")
        return 1
    if not _is_local_database(settings.database_url):
        print("La base configurada no es local. Las cuentas de prueba no se siembran ahí.")
        return 1
    for line in asyncio.run(seed()):
        print(line)
    print(f"Contraseña de todas las cuentas: {DEMO_PASSWORD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
