"""Lectores hacia datos que posee otro módulo.

Una cita necesita dos cosas que no son suyas: saber si la mascota es del
cliente y si el veterinario publicó esa hora. `pets` y `availability` son
módulos de dominio independientes y este no puede importarlos.

La salida es la misma que usa `gestvet.core.auth` para la identidad: una
proyección de solo lectura, escrita a mano contra la tabla del otro módulo y
declarada como puerto para que el negocio no sepa de dónde sale la respuesta.
El acoplamiento es al nombre de la tabla, está acotado a estas consultas y lo
cubren las pruebas.

La regla es estricta: se lee, nunca se escribe. Modificar una mascota o un
tramo de agenda sigue siendo competencia exclusiva de su módulo.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, bindparam, text
from sqlalchemy.ext.asyncio import AsyncSession

from gestvet.core.identity import Role

# Una consulta escrita a mano no pasa por el sistema de tipos de SQLAlchemy,
# así que un `datetime` llegaría crudo al driver: en SQLite eso cae en el
# adaptador obsoleto que Python marcó para borrar. Declarar el tipo del
# parámetro devuelve la conversión a SQLAlchemy, que la hace igual en todos
# los motores.
_MOMENT = DateTime(timezone=True)

_PET_IS_OWNED = text(
    "SELECT 1 FROM pets WHERE id = :pet_id AND owner_id = :owner_id AND is_active = :active"
)

_SCHEDULE_COVERS = text(
    "SELECT 1 FROM availability_slots "
    "WHERE veterinarian_id = :veterinarian_id "
    "AND starts_at <= :starts_at AND ends_at >= :ends_at "
    "LIMIT 1"
).bindparams(
    bindparam("starts_at", type_=_MOMENT),
    bindparam("ends_at", type_=_MOMENT),
)

_ON_DUTY = text(
    "SELECT DISTINCT s.veterinarian_id FROM availability_slots s "
    "JOIN users u ON u.id = s.veterinarian_id "
    "WHERE u.role = :role AND u.is_active = :active "
    "AND s.starts_at <= :moment AND s.ends_at > :moment"
).bindparams(bindparam("moment", type_=_MOMENT))


class SqlPetDirectory:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def is_owned_by(self, pet_id: int, owner_id: int) -> bool:
        # Una mascota dada de baja no puede recibir citas nuevas.
        row = (
            await self._session.execute(
                _PET_IS_OWNED, {"pet_id": pet_id, "owner_id": owner_id, "active": True}
            )
        ).first()
        return row is not None


class SqlScheduleDirectory:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def covers(self, veterinarian_id: int, starts_at: datetime, ends_at: datetime) -> bool:
        """La cita entera tiene que caber dentro de un único tramo publicado.

        Repartirla entre dos tramos contiguos seria defendible, pero el
        original tampoco lo hacia y abre la puerta a agendar sobre el hueco
        entre dos jornadas.
        """
        row = (
            await self._session.execute(
                _SCHEDULE_COVERS,
                {
                    "veterinarian_id": veterinarian_id,
                    "starts_at": starts_at,
                    "ends_at": ends_at,
                },
            )
        ).first()
        return row is not None

    async def veterinarians_on_duty(self, moment: datetime) -> list[int]:
        rows = await self._session.execute(
            _ON_DUTY,
            {
                "role": Role.EMERGENCY_VETERINARIAN.value,
                "active": True,
                "moment": moment,
            },
        )
        return [int(row.veterinarian_id) for row in rows]
