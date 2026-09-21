"""crear los consentimientos informados.

Revision ID: 0026
Revises: 0025
Create Date: 2026-09-21

Hasta ahora el consentimiento era un papel escaneado y subido como adjunto de
la historia clínica. Una emergencia abierta desde la web no dejaba ninguna
constancia de que el dueño supiera que el animal podía morir o que el costo
se conoce al final. Esta migración:

- crea `consent_templates`, los textos versionados. Una versión no se edita:
  se publica otra y se desactiva la anterior, porque cada firma apunta al
  texto que se leyó;
- crea `consents`, cada firma con una copia del texto y su huella SHA-256,
  para que el registro se sostenga aunque la plantilla cambie;
- siembra la versión 1 del texto de riesgo de emergencia;
- agrega `appointments.risk_consent_id`, única, para saber qué firma habilitó
  cada emergencia y que una misma firma no abra dos. Las citas que ya
  existían quedan en nulo.

El tipo y el estado se guardan como texto y no como enumerado de la base:
sumar un tipo de consentimiento no tiene que alterar ninguna columna.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op

revision: str = "0026"
down_revision: str | None = "0025"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TIPO_RIESGO_DE_EMERGENCIA = "emergency_risk"

TITULO_RIESGO_DE_EMERGENCIA = "Consentimiento informado para la atención de emergencia"

# Borrador para que lo revise un médico veterinario o un abogado. Corregirlo
# es sembrar una versión 2 en otra migración y desactivar esta, nunca
# editar este texto: hay firmas que apuntan a él.
CUERPO_RIESGO_DE_EMERGENCIA = """\
Declaro que soy el propietario de la mascota o la persona responsable de ella en este momento, \
y que puedo tomar decisiones sobre su atención.

1. Estado de la mascota. Entiendo que mi mascota llega por una emergencia y que puede estar en \
estado crítico. Aun con una atención adecuada y oportuna, su estado puede empeorar, puede quedar \
con secuelas e incluso puede morir. El equipo veterinario no puede garantizar un resultado.

2. Atención inicial. Autorizo al médico veterinario de turno a estabilizar a mi mascota y a \
realizar las medidas de diagnóstico y de tratamiento que, según su criterio profesional, sean \
urgentes: por ejemplo, el examen clínico, oxígeno, fluidos, medicamentos, control del dolor, \
análisis de laboratorio o imágenes.

3. Costo. Entiendo que el costo de una atención de emergencia no se conoce de antemano: depende \
de lo que mi mascota necesite y se sabe recién cuando termina la atención. Me comprometo a pagar \
los servicios que se le presten.

4. Información y decisiones posteriores. El médico veterinario me informará sobre el estado de \
mi mascota y sobre las opciones de tratamiento en cuanto le sea posible. Antes de cualquier \
procedimiento que no sea urgente, como una cirugía, una internación o la eutanasia, me pedirá un \
consentimiento específico para ese procedimiento.

5. Declaración. Leí este texto, pude hacer las preguntas que necesitaba y lo acepto libremente. \
La información que di sobre mi mascota y sobre mí es verdadera.\
"""

_SEMBRADO_EL = datetime(2026, 9, 21, tzinfo=UTC)


def plantilla_de_riesgo_de_emergencia() -> dict[str, object]:
    """La fila sembrada. Las pruebas la leen de acá para no copiar el texto."""
    return {
        "kind": TIPO_RIESGO_DE_EMERGENCIA,
        "version": 1,
        "title": TITULO_RIESGO_DE_EMERGENCIA,
        "body": CUERPO_RIESGO_DE_EMERGENCIA,
        "is_active": True,
        "created_at": _SEMBRADO_EL,
    }


def upgrade() -> None:
    plantillas = op.create_table(
        "consent_templates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(length=40), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("kind", "version", name="uq_consent_templates_kind_version"),
    )
    op.create_index("ix_consent_templates_kind", "consent_templates", ["kind"], unique=False)

    op.create_table(
        "consents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("template_id", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(length=40), nullable=False),
        sa.Column("pet_id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("channel", sa.String(length=20), nullable=False),
        sa.Column("text_snapshot", sa.Text(), nullable=False),
        sa.Column("text_sha256", sa.String(length=64), nullable=False),
        sa.Column("signer_name", sa.String(length=120), nullable=False),
        sa.Column("signer_user_id", sa.Integer(), nullable=True),
        sa.Column("witness_id", sa.Integer(), nullable=True),
        sa.Column("requested_by", sa.Integer(), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("ip", sa.String(length=45), nullable=False),
        sa.Column("user_agent", sa.String(length=300), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["template_id"],
            ["consent_templates.id"],
            name="fk_consents_template",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["pet_id"], ["pets.id"], name="fk_consents_pet", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["client_id"], ["users.id"], name="fk_consents_client", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["signer_user_id"],
            ["users.id"],
            name="fk_consents_signer_user",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["witness_id"], ["users.id"], name="fk_consents_witness", ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["requested_by"],
            ["users.id"],
            name="fk_consents_requested_by",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_consents_template_id", "consents", ["template_id"], unique=False)
    op.create_index("ix_consents_pet_id", "consents", ["pet_id"], unique=False)
    op.create_index("ix_consents_client_id", "consents", ["client_id"], unique=False)

    op.bulk_insert(plantillas, [plantilla_de_riesgo_de_emergencia()])

    # En lote: SQLite no agrega una clave foránea con un ALTER TABLE simple.
    with op.batch_alter_table("appointments") as batch:
        batch.add_column(sa.Column("risk_consent_id", sa.Integer(), nullable=True))
        batch.create_foreign_key(
            "fk_appointments_risk_consent",
            "consents",
            ["risk_consent_id"],
            ["id"],
            ondelete="RESTRICT",
        )
        batch.create_unique_constraint("uq_appointments_risk_consent_id", ["risk_consent_id"])


def downgrade() -> None:
    with op.batch_alter_table("appointments") as batch:
        batch.drop_constraint("uq_appointments_risk_consent_id", type_="unique")
        batch.drop_constraint("fk_appointments_risk_consent", type_="foreignkey")
        batch.drop_column("risk_consent_id")
    op.drop_index("ix_consents_client_id", table_name="consents")
    op.drop_index("ix_consents_pet_id", table_name="consents")
    op.drop_index("ix_consents_template_id", table_name="consents")
    op.drop_table("consents")
    op.drop_index("ix_consent_templates_kind", table_name="consent_templates")
    op.drop_table("consent_templates")
