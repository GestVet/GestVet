"""La administración amplía y corrige el catálogo de especies y razas."""

from __future__ import annotations

from typing import Any

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from gestvet.core.identity import Role
from gestvet.modules.accounts.adapters.persistence.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from gestvet.modules.accounts.domain.entities import User
from gestvet.modules.pets.adapters.persistence.sqlalchemy_pet_repository import (
    SqlAlchemyPetRepository,
)
from tests.conftest import authorization_for, build_pet, build_user

CATALOG_URL = "/api/v1/pets/catalog"
MANAGE_URL = f"{CATALOG_URL}/manage"
SPECIES_URL = f"{CATALOG_URL}/species"
PETS_URL = "/api/v1/pets"


async def _account(session: AsyncSession, email: str, role: Role) -> User:
    user = await SqlAlchemyUserRepository(session).add(build_user(email, role=role))
    await session.commit()
    return user


async def _admin(session: AsyncSession) -> dict[str, str]:
    return authorization_for(await _account(session, "admin@example.com", Role.ADMIN))


async def _species(client: AsyncClient, headers: dict[str, str], name: str) -> dict[str, Any]:
    manage = (await client.get(MANAGE_URL, headers=headers)).json()
    return next(item for item in manage["species"] if item["name"] == name)


async def _offered(client: AsyncClient, headers: dict[str, str]) -> dict[str, list[str]]:
    catalog = (await client.get(CATALOG_URL, headers=headers)).json()
    return {item["name"]: item["breeds"] for item in catalog["species"]}


async def test_la_especie_nueva_se_formatea_y_trae_sin_especificar(
    client: AsyncClient, session: AsyncSession
) -> None:
    admin = await _admin(session)

    response = await client.post(
        SPECIES_URL, json={"name": "  PETAURO  del azúcar "}, headers=admin
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Petauro del azúcar"
    assert [raza["name"] for raza in body["breeds"]] == ["Sin especificar"]
    assert (await _offered(client, admin))["Petauro del azúcar"] == ["Sin especificar"]


async def test_no_entra_una_especie_que_solo_cambia_tildes_o_mayusculas(
    client: AsyncClient, session: AsyncSession
) -> None:
    admin = await _admin(session)

    response = await client.post(SPECIES_URL, json={"name": "huron"}, headers=admin)

    assert response.status_code == 409


async def test_un_cliente_no_administra_el_catalogo(
    client: AsyncClient, session: AsyncSession
) -> None:
    cliente = authorization_for(await _account(session, "ana@example.com", Role.CLIENT))

    assert (await client.get(MANAGE_URL, headers=cliente)).status_code == 403
    assert (
        await client.post(SPECIES_URL, json={"name": "Petauro"}, headers=cliente)
    ).status_code == 403


async def test_la_raza_nueva_aparece_en_su_especie_y_no_se_duplica(
    client: AsyncClient, session: AsyncSession
) -> None:
    admin = await _admin(session)
    perro = await _species(client, admin, "Perro")
    url = f"{SPECIES_URL}/{perro['id']}/breeds"

    creada = await client.post(url, json={"name": "BORDER TERRIER"}, headers=admin)
    repetida = await client.post(url, json={"name": "border  terrier"}, headers=admin)

    assert creada.status_code == 201
    assert creada.json()["name"] == "Border terrier"
    assert repetida.status_code == 409
    assert "Border terrier" in (await _offered(client, admin))["Perro"]


async def test_corregir_una_raza_la_corrige_en_las_fichas(
    client: AsyncClient, session: AsyncSession
) -> None:
    admin = await _admin(session)
    dueno = await _account(session, "ana@example.com", Role.CLIENT)
    mascota = await SqlAlchemyPetRepository(session).add(
        build_pet(owner_id=dueno.id or 0, species="Perro", breed="Pitbull")
    )
    await session.commit()
    perro = await _species(client, admin, "Perro")
    pitbull = next(raza for raza in perro["breeds"] if raza["name"] == "Pitbull")

    response = await client.patch(
        f"{CATALOG_URL}/breeds/{pitbull['id']}",
        json={"name": "pitbull terrier americano", "is_active": True},
        headers=admin,
    )

    assert response.status_code == 200
    session.expire_all()
    guardada = await SqlAlchemyPetRepository(session).get(mascota.id or 0)
    assert guardada is not None
    assert guardada.breed == "Pitbull terrier americano"


async def test_corregir_una_especie_la_corrige_en_las_fichas(
    client: AsyncClient, session: AsyncSession
) -> None:
    admin = await _admin(session)
    dueno = await _account(session, "ana@example.com", Role.CLIENT)
    mascota = await SqlAlchemyPetRepository(session).add(
        build_pet(owner_id=dueno.id or 0, species="Hurón", breed="Sin especificar")
    )
    await session.commit()
    huron = await _species(client, admin, "Hurón")

    response = await client.patch(
        f"{SPECIES_URL}/{huron['id']}",
        json={"name": "Hurón doméstico", "is_active": True},
        headers=admin,
    )

    assert response.status_code == 200
    session.expire_all()
    guardada = await SqlAlchemyPetRepository(session).get(mascota.id or 0)
    assert guardada is not None
    assert guardada.species == "Hurón doméstico"


async def test_una_raza_desactivada_no_se_ofrece_pero_no_bloquea_la_ficha(
    client: AsyncClient, session: AsyncSession
) -> None:
    admin = await _admin(session)
    dueno = await _account(session, "ana@example.com", Role.CLIENT)
    cabeceras = authorization_for(dueno)
    mascota = await SqlAlchemyPetRepository(session).add(
        build_pet(owner_id=dueno.id or 0, species="Perro", breed="Pug")
    )
    await session.commit()
    perro = await _species(client, admin, "Perro")
    pug = next(raza for raza in perro["breeds"] if raza["name"] == "Pug")

    await client.patch(
        f"{CATALOG_URL}/breeds/{pug['id']}", json={"name": "Pug", "is_active": False}, headers=admin
    )
    nueva = await client.post(
        PETS_URL,
        json={"name": "Toby", "species": "Perro", "breed": "Pug", "birth_date": "2021-03-01"},
        headers=cabeceras,
    )
    ficha = await client.patch(
        f"{PETS_URL}/{mascota.id}/owner-profile",
        json={"species": "Perro", "breed": "Pug", "color": "Negro"},
        headers=cabeceras,
    )

    assert "Pug" not in (await _offered(client, admin))["Perro"]
    assert nueva.status_code == 422
    assert ficha.status_code == 200


async def test_sin_especificar_no_se_desactiva(client: AsyncClient, session: AsyncSession) -> None:
    admin = await _admin(session)
    gato = await _species(client, admin, "Gato")
    desconocida = next(raza for raza in gato["breeds"] if raza["is_locked"])

    response = await client.patch(
        f"{CATALOG_URL}/breeds/{desconocida['id']}",
        json={"name": "Sin especificar", "is_active": False},
        headers=admin,
    )

    assert response.status_code == 409


async def test_un_nombre_con_numeros_se_rechaza(client: AsyncClient, session: AsyncSession) -> None:
    admin = await _admin(session)

    response = await client.post(SPECIES_URL, json={"name": "Especie 2"}, headers=admin)

    assert response.status_code == 422
