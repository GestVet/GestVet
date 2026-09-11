"""Pruebas del adaptador de persistencia.

El repositorio en memoria de las pruebas de casos de uso no ejecuta SQL, así
que la búsqueda, los filtros, el ordenamiento y la restricción única solo
quedan cubiertos aquí, contra una base real.
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from gestvet.core.identity import Role
from gestvet.modules.accounts.adapters.persistence.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from gestvet.modules.accounts.domain.exceptions import EmailAlreadyRegistered
from gestvet.modules.accounts.ports.user_repository import UserQuery
from tests.conftest import build_user


async def _seed(session: AsyncSession, users: SqlAlchemyUserRepository) -> None:
    await users.add(build_user("carla@example.com", first_name="Carla", last_name="Blanco"))
    await users.add(
        build_user("beto@example.com", first_name="Beto", last_name="Alvarez", phone="987654321")
    )
    await users.add(
        build_user("ada@example.com", first_name="Ada", last_name="Zamora", is_active=False)
    )
    await users.add(build_user("jefa@example.com", role=Role.ADMIN, last_name="Aguirre"))
    await session.commit()


async def test_guardar_devuelve_la_entidad_con_identificador(
    users: SqlAlchemyUserRepository,
) -> None:
    created = await users.add(build_user("ana@example.com"))

    assert created.id is not None
    assert created.email == "ana@example.com"
    assert created.role is Role.CLIENT


async def test_el_correo_repetido_choca_contra_la_restriccion_unica(
    session: AsyncSession,
    users: SqlAlchemyUserRepository,
) -> None:
    await users.add(build_user("ana@example.com"))
    await session.commit()

    # Se salta a propósito la comprobación previa del caso de uso: esto es lo
    # que pasa cuando dos registros simultáneos la superan los dos.
    with pytest.raises(EmailAlreadyRegistered):
        await users.add(build_user("ana@example.com"))


async def test_buscar_por_rol_ignora_a_quien_no_es_cliente(
    session: AsyncSession,
    users: SqlAlchemyUserRepository,
) -> None:
    await _seed(session, users)

    page = await users.search(UserQuery(roles=frozenset({Role.CLIENT})))

    assert page.total == 3
    assert all(user.role is Role.CLIENT for user in page.items)


async def test_la_busqueda_alcanza_nombre_correo_y_telefono(
    session: AsyncSession,
    users: SqlAlchemyUserRepository,
) -> None:
    await _seed(session, users)

    por_nombre = await users.search(UserQuery(roles=frozenset({Role.CLIENT}), search="Carla"))
    por_correo = await users.search(UserQuery(roles=frozenset({Role.CLIENT}), search="beto@"))
    por_telefono = await users.search(UserQuery(roles=frozenset({Role.CLIENT}), search="98765"))

    assert [user.email for user in por_nombre.items] == ["carla@example.com"]
    assert [user.email for user in por_correo.items] == ["beto@example.com"]
    assert [user.email for user in por_telefono.items] == ["beto@example.com"]


async def test_el_filtro_de_estado_separa_activos_de_inactivos(
    session: AsyncSession,
    users: SqlAlchemyUserRepository,
) -> None:
    await _seed(session, users)

    activos = await users.search(UserQuery(roles=frozenset({Role.CLIENT}), is_active=True))
    inactivos = await users.search(UserQuery(roles=frozenset({Role.CLIENT}), is_active=False))

    assert activos.total == 2
    assert [user.email for user in inactivos.items] == ["ada@example.com"]


@pytest.mark.parametrize(
    ("ordering", "esperado"),
    [
        (None, ["beto@example.com", "carla@example.com", "ada@example.com"]),
        ("email", ["ada@example.com", "beto@example.com", "carla@example.com"]),
        ("-email", ["carla@example.com", "beto@example.com", "ada@example.com"]),
        ("last_name", ["beto@example.com", "carla@example.com", "ada@example.com"]),
    ],
)
async def test_el_ordenamiento_traduce_a_la_columna_correcta(
    session: AsyncSession,
    users: SqlAlchemyUserRepository,
    ordering: str | None,
    esperado: list[str],
) -> None:
    await _seed(session, users)

    page = await users.search(UserQuery(roles=frozenset({Role.CLIENT}), ordering=ordering))

    assert [user.email for user in page.items] == esperado


async def test_una_columna_desconocida_cae_al_orden_predeterminado(
    session: AsyncSession,
    users: SqlAlchemyUserRepository,
) -> None:
    await _seed(session, users)

    page = await users.search(UserQuery(roles=frozenset({Role.CLIENT}), ordering="password_hash"))

    assert [user.email for user in page.items] == [
        "beto@example.com",
        "carla@example.com",
        "ada@example.com",
    ]


async def test_la_paginacion_recorta_sin_perder_el_total(
    session: AsyncSession,
    users: SqlAlchemyUserRepository,
) -> None:
    await _seed(session, users)

    page = await users.search(
        UserQuery(roles=frozenset({Role.CLIENT}), ordering="email", limit=2, offset=1)
    )

    assert page.total == 3
    assert [user.email for user in page.items] == ["beto@example.com", "carla@example.com"]


async def test_buscar_por_correo_normaliza_y_encuentra(
    session: AsyncSession,
    users: SqlAlchemyUserRepository,
) -> None:
    await users.add(build_user("Ana.Quispe@Example.com"))
    await session.commit()

    encontrado = await users.get_by_email("ana.quispe@example.com")

    assert encontrado is not None
    assert encontrado.full_name == "Ana Quispe"


async def test_la_fecha_vuelve_de_la_base_con_su_zona_horaria(
    session: AsyncSession,
    users: SqlAlchemyUserRepository,
) -> None:
    """SQLite no guarda la zona; el adaptador la repone al leer.

    Sin esto el API serializa una marca sin desplazamiento, el navegador la
    toma como hora local y la fecha se corre. Solo ocurre contra SQLite, asi
    que el error viaja hasta produccion sin que nadie lo vea.
    """
    creado = await users.add(build_user("ana@example.com"))
    await session.commit()

    recuperado = await users.get_by_email("ana@example.com")

    assert creado.created_at.tzinfo is not None
    assert recuperado is not None
    assert recuperado.created_at.tzinfo is not None
    assert recuperado.created_at.utcoffset() == timedelta(0)
