"""crear el catálogo de especies y razas.

Revision ID: 0020
Revises: 0019
Create Date: 2026-09-14

El catálogo vivía en el código y cambiarlo exigía un despliegue. Pasa a la base
para que la administración agregue una raza el día que llega un animal que no
está. La siembra reproduce la lista que tenía el código, escrita acá y no
importada: una migración tiene que seguir haciendo lo mismo aunque el código
cambie después. Las pruebas siembran su base con estas mismas funciones.

También le da a la administración el permiso nuevo de administrar el catálogo.
"""

from __future__ import annotations

import unicodedata
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0020"
down_revision: str | None = "0019"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PERMISO = "pets.manage_catalog"
SIN_ESPECIFICAR = "Sin especificar"
MESTIZO = "Mestizo"
OTRA_RAZA = "Otra raza"
ORDEN_DE_OTRO = 1000

_PERROS = (
    "Akita inu",
    "Alaskan malamute",
    "American bully",
    "American staffordshire terrier",
    "Basenji",
    "Basset hound",
    "Beagle",
    "Bichón frisé",
    "Bloodhound",
    "Border collie",
    "Boston terrier",
    "Boxer",
    "Bull terrier",
    "Bulldog americano",
    "Bulldog francés",
    "Bulldog inglés",
    "Bullmastiff",
    "Cane corso",
    "Cavalier King Charles spaniel",
    "Chihuahua",
    "Chow chow",
    "Cocker spaniel",
    "Collie",
    "Corgi galés",
    "Dachshund (salchicha)",
    "Dálmata",
    "Dóberman",
    "Dogo alemán (gran danés)",
    "Dogo argentino",
    "Dogo de Burdeos",
    "Fox terrier",
    "Galgo",
    "Golden retriever",
    "Husky siberiano",
    "Jack Russell terrier",
    "Labrador retriever",
    "Lhasa apso",
    "Maltés",
    "Mastín napolitano",
    "Pastor alemán",
    "Pastor australiano",
    "Pastor belga malinois",
    "Pequinés",
    "Perro sin pelo del Perú",
    "Pinscher miniatura",
    "Pitbull",
    "Pomerania",
    "Poodle",
    "Poodle toy",
    "Presa canario",
    "Pug",
    "Rottweiler",
    "Samoyedo",
    "San bernardo",
    "Schnauzer",
    "Schnauzer gigante",
    "Schnauzer miniatura",
    "Setter irlandés",
    "Shar pei",
    "Shiba inu",
    "Shih tzu",
    "Staffordshire bull terrier",
    "Terranova",
    "Weimaraner",
    "West Highland white terrier",
    "Whippet",
    "Yorkshire terrier",
)

_GATOS = (
    "Abisinio",
    "Angora",
    "Azul ruso",
    "Balinés",
    "Bengalí",
    "Birmano",
    "Bombay",
    "British shorthair",
    "Burmés",
    "Cornish rex",
    "Devon rex",
    "Exótico de pelo corto",
    "Himalayo",
    "Maine coon",
    "Manx",
    "Mau egipcio",
    "Oriental",
    "Persa",
    "Ragdoll",
    "Savannah",
    "Scottish fold",
    "Siamés",
    "Siberiano",
    "Sphynx",
    "Van turco",
)

# (especie, si admite mestizo, razas). El orden es el que ve el dueño: primero
# las mascotas más comunes, después la granja y al final "Otro".
CATALOGO_INICIAL: tuple[tuple[str, bool, tuple[str, ...]], ...] = (
    ("Perro", True, _PERROS),
    ("Gato", True, _GATOS),
    (
        "Conejo",
        True,
        (
            "Angora",
            "Belier",
            "Cabeza de león",
            "Californiano",
            "Enano holandés",
            "Gigante de Flandes",
            "Mini lop",
            "Neozelandés",
            "Rex",
        ),
    ),
    (
        "Roedor",
        False,
        (
            "Chinchilla",
            "Cuy",
            "Cuy abisinio",
            "Cuy andino",
            "Cuy peruano (pelo largo)",
            "Degú",
            "Hámster",
            "Hámster enano ruso",
            "Hámster roborovski",
            "Hámster sirio",
            "Jerbo",
            "Rata",
            "Ratón",
        ),
    ),
    ("Hurón", False, ()),
    ("Erizo", False, ("Erizo africano pigmeo",)),
    (
        "Ave",
        False,
        (
            "Agapornis",
            "Cacatúa",
            "Canario",
            "Cotorra argentina",
            "Diamante mandarín",
            "Guacamayo",
            "Jilguero",
            "Loro",
            "Loro gris africano",
            "Ninfa (carolina)",
            "Paloma",
            "Periquito australiano",
        ),
    ),
    (
        "Reptil",
        False,
        (
            "Boa constrictor",
            "Camaleón",
            "Dragón barbudo",
            "Gecko crestado",
            "Gecko leopardo",
            "Iguana",
            "Pitón bola",
            "Serpiente",
            "Serpiente del maíz",
            "Tortuga acuática",
            "Tortuga de orejas rojas",
            "Tortuga sulcata",
            "Tortuga terrestre",
        ),
    ),
    ("Anfibio", False, ("Ajolote", "Rana arborícola", "Rana cornuda", "Sapo", "Tritón")),
    (
        "Pez",
        False,
        (
            "Betta",
            "Carpa koi",
            "Disco",
            "Escalar",
            "Goldfish",
            "Guppy",
            "Molly",
            "Neón",
            "Oscar",
            "Platy",
        ),
    ),
    ("Ave de corral", False, ("Codorniz", "Gallina", "Gallo", "Ganso", "Pato", "Pavo")),
    (
        "Caballo",
        True,
        (
            "Andaluz",
            "Appaloosa",
            "Árabe",
            "Caballo peruano de paso",
            "Criollo",
            "Cuarto de milla",
            "Frisón",
            "Percherón",
            "Pony",
            "Pura sangre inglés",
        ),
    ),
    ("Burro o mula", False, ("Burro", "Mula")),
    ("Alpaca o llama", False, ("Alpaca huacaya", "Alpaca suri", "Llama")),
    (
        "Vaca",
        True,
        ("Angus", "Brahman", "Brown swiss", "Criolla", "Gyr", "Hereford", "Holstein", "Jersey"),
    ),
    ("Cerdo", True, ("Duroc", "Landrace", "Mini pig", "Pietrain", "Vietnamita", "Yorkshire")),
    ("Oveja", True, ("Black belly", "Corriedale", "Criolla", "Dorper", "Hampshire", "Merino")),
    ("Cabra", True, ("Alpina", "Anglo nubian", "Boer", "Criolla", "Saanen")),
    ("Otro", False, ()),
)


def clave(nombre: str) -> str:
    sin_tildes = unicodedata.normalize("NFD", nombre).encode("ascii", "ignore").decode()
    return " ".join(sin_tildes.casefold().split())


def filas_de_especies() -> list[dict[str, object]]:
    return [
        {
            "name": especie,
            "name_key": clave(especie),
            "sort_order": ORDEN_DE_OTRO if especie == "Otro" else (posicion + 1) * 10,
            "is_active": True,
        }
        for posicion, (especie, _, _) in enumerate(CATALOGO_INICIAL)
    ]


def filas_de_razas(ids_por_especie: dict[str, int]) -> list[dict[str, object]]:
    filas: list[dict[str, object]] = []
    for especie, admite_mestizo, razas in CATALOGO_INICIAL:
        nombres = (
            SIN_ESPECIFICAR,
            *((MESTIZO,) if admite_mestizo else ()),
            *razas,
            *((OTRA_RAZA,) if razas else ()),
        )
        filas.extend(
            {
                "species_id": ids_por_especie[especie],
                "name": nombre,
                "name_key": clave(nombre),
                "is_active": True,
            }
            for nombre in nombres
        )
    return filas


def upgrade() -> None:
    especies = op.create_table(
        "pet_species",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=40), nullable=False),
        sa.Column("name_key", sa.String(length=40), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_pet_species_name_key", "pet_species", ["name_key"], unique=True)

    razas = op.create_table(
        "pet_breeds",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("species_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=60), nullable=False),
        sa.Column("name_key", sa.String(length=60), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["species_id"], ["pet_species.id"], name="fk_pet_breeds_species", ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("species_id", "name_key", name="uq_pet_breeds_species_name_key"),
    )
    op.create_index("ix_pet_breeds_species_id", "pet_breeds", ["species_id"], unique=False)

    op.bulk_insert(especies, filas_de_especies())
    conexion = op.get_bind()
    ids = dict(conexion.execute(sa.text("SELECT name, id FROM pet_species")).all())
    op.bulk_insert(razas, filas_de_razas(ids))

    rol_admin = conexion.execute(
        sa.text("SELECT id FROM access_roles WHERE account_kind = 'admin' AND is_system = :si"),
        {"si": True},
    ).scalar_one_or_none()
    if rol_admin is not None:
        conexion.execute(
            sa.text(
                "INSERT INTO access_role_permissions (role_id, permission) VALUES (:rol, :permiso)"
            ),
            {"rol": rol_admin, "permiso": PERMISO},
        )


def downgrade() -> None:
    op.execute(sa.text(f"DELETE FROM access_role_permissions WHERE permission = '{PERMISO}'"))
    op.drop_index("ix_pet_breeds_species_id", table_name="pet_breeds")
    op.drop_table("pet_breeds")
    op.drop_index("ix_pet_species_name_key", table_name="pet_species")
    op.drop_table("pet_species")
