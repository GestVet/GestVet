"""agregar las especialidades veterinarias.

Revision ID: 0025
Revises: 0024
Create Date: 2026-09-21

Cada veterinario declara con qué se preparó para atender: una disciplina
(cardiología, cirugía...), un tipo de animal (exóticos, equinos...) o un cargo
fuera de la clínica (salud pública, investigación...). La siembra reproduce
un catálogo inicial razonable, escrito acá y no importado: una migración
tiene que seguir haciendo lo mismo aunque el catálogo cambie después. Las
pruebas siembran su base con estas mismas funciones.

También le da a la administración el permiso nuevo de administrar el
catálogo de especialidades.
"""

from __future__ import annotations

import unicodedata
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0025"
down_revision: str | None = "0024"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PERMISO = "specialties.manage_catalog"

DISCIPLINA = "discipline"
TIPO_DE_ANIMAL = "animal_type"
INDUSTRIA = "industry"

# (nombre, categoría, descripción). El orden es el que ve quien administra:
# primero las disciplinas clínicas, después el tipo de animal y al final los
# cargos que no son de consultorio.
CATALOGO_INICIAL: tuple[tuple[str, str, str], ...] = (
    (
        "Cardiología veterinaria",
        DISCIPLINA,
        "Diagnóstico y tratamiento de enfermedades del corazón.",
    ),
    ("Oncología veterinaria", DISCIPLINA, "Tratamiento del cáncer en animales."),
    (
        "Dermatología veterinaria",
        DISCIPLINA,
        "Problemas de la piel, el pelo y las alergias.",
    ),
    ("Oftalmología veterinaria", DISCIPLINA, "Enfermedades y cirugías oculares."),
    (
        "Neurología y neurocirugía veterinaria",
        DISCIPLINA,
        "Trastornos del sistema nervioso y de la columna.",
    ),
    (
        "Traumatología y ortopedia veterinaria",
        DISCIPLINA,
        "Cirugías óseas, de articulaciones y corrección de fracturas.",
    ),
    (
        "Odontología veterinaria",
        DISCIPLINA,
        "Cuidado dental, limpiezas y cirugías maxilofaciales.",
    ),
    (
        "Fisioterapia y rehabilitación animal",
        DISCIPLINA,
        "Recuperación física postoperatoria o de lesiones crónicas.",
    ),
    (
        "Medicina interna veterinaria",
        DISCIPLINA,
        "Diagnóstico y manejo de enfermedades complejas o crónicas.",
    ),
    (
        "Cirugía general veterinaria",
        DISCIPLINA,
        "Procedimientos quirúrgicos que no requieren una subespecialidad.",
    ),
    (
        "Anestesiología y analgesia veterinaria",
        DISCIPLINA,
        "Manejo del dolor y la anestesia antes, durante y después de una cirugía.",
    ),
    (
        "Medicina de urgencias y cuidados intensivos",
        DISCIPLINA,
        "Atención crítica y estabilización de casos graves.",
    ),
    (
        "Etología y comportamiento animal",
        DISCIPLINA,
        "Diagnóstico y corrección de problemas de conducta.",
    ),
    ("Toxicología veterinaria", DISCIPLINA, "Diagnóstico y tratamiento de intoxicaciones."),
    (
        "Animales de compañía (perros y gatos)",
        TIPO_DE_ANIMAL,
        "Clínica de pequeños animales.",
    ),
    (
        "Animales exóticos",
        TIPO_DE_ANIMAL,
        "Aves, reptiles, roedores, hurones y mascotas no convencionales.",
    ),
    ("Equinos", TIPO_DE_ANIMAL, "Atención dedicada a caballos, de deporte, cría o trabajo."),
    (
        "Animales de granja (producción animal)",
        TIPO_DE_ANIMAL,
        "Bovinos, porcinos, ovinos, caprinos y aves de corral.",
    ),
    (
        "Fauna silvestre y zoológicos",
        TIPO_DE_ANIMAL,
        "Manejo de animales en cautiverio, conservación y reservas naturales.",
    ),
    (
        "Seguridad e higiene alimentaria",
        INDUSTRIA,
        "Inspección de mataderos, plantas procesadoras y control de calidad de "
        "productos de origen animal.",
    ),
    (
        "Epidemiología veterinaria",
        INDUSTRIA,
        "Control, prevención y rastreo de enfermedades zoonóticas.",
    ),
    (
        "Patología veterinaria",
        INDUSTRIA,
        "Diagnóstico mediante el análisis de tejidos y necropsias en laboratorio.",
    ),
    (
        "Veterinaria de laboratorio e investigación",
        INDUSTRIA,
        "Desarrollo de vacunas, medicamentos y estudios científicos.",
    ),
    (
        "Nutrición animal",
        INDUSTRIA,
        "Formulación de dietas balanceadas para mascotas o ganado.",
    ),
    (
        "Bienestar animal",
        INDUSTRIA,
        "Evaluación y promoción de condiciones de vida adecuadas para los animales.",
    ),
    (
        "Genética y reproducción animal",
        INDUSTRIA,
        "Mejoramiento genético, inseminación y manejo reproductivo.",
    ),
)


def clave(nombre: str) -> str:
    sin_tildes = unicodedata.normalize("NFD", nombre).encode("ascii", "ignore").decode()
    return " ".join(sin_tildes.casefold().split())


def filas_de_especialidades() -> list[dict[str, object]]:
    return [
        {
            "name": nombre,
            "name_key": clave(nombre),
            "category": categoria,
            "description": descripcion,
            "is_active": True,
        }
        for nombre, categoria, descripcion in CATALOGO_INICIAL
    ]


def upgrade() -> None:
    especialidades = op.create_table(
        "specialties",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("name_key", sa.String(length=80), nullable=False),
        sa.Column("category", sa.String(length=20), nullable=False),
        sa.Column("description", sa.String(length=240), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_specialties_name_key", "specialties", ["name_key"], unique=True)
    op.create_index("ix_specialties_category", "specialties", ["category"], unique=False)

    op.create_table(
        "veterinarian_specialties",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("specialty_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_veterinarian_specialties_user",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["specialty_id"],
            ["specialties.id"],
            name="fk_veterinarian_specialties_specialty",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("user_id", "specialty_id"),
    )

    op.bulk_insert(especialidades, filas_de_especialidades())

    conexion = op.get_bind()
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
    op.drop_table("veterinarian_specialties")
    op.drop_index("ix_specialties_category", table_name="specialties")
    op.drop_index("ix_specialties_name_key", table_name="specialties")
    op.drop_table("specialties")
