"""pedir consentimientos específicos.

Revision ID: 0027
Revises: 0026
Create Date: 2026-09-21

Hasta ahora el único consentimiento era el riesgo de una emergencia, firmado
al abrirla. Esta migración deja que el veterinario pida uno específico sobre
una cita después de evaluar a la mascota:

- agrega `consents.appointment_id`, la cita del pedido. Sin clave foránea:
  `appointments.risk_consent_id` ya apunta hacia `consents` y el ciclo
  obligaría a crear y borrar las tablas con restricciones diferidas;
- agrega `consents.decision_reason`, el motivo de un rechazo o la
  justificación de una atención sin consentimiento por urgencia vital;
- deja en nulo el canal, el nombre de quien firma y la fecha de la decisión:
  un pedido pendiente todavía no tiene ninguno de los tres;
- siembra la versión 1 de cinco textos: pronóstico reservado, cirugía o
  procedimiento invasivo, anestesia o sedación, internación y eutanasia.

Los textos son borradores para que los revise un médico veterinario o un
abogado. Corregirlos es sembrar una versión 2 en otra migración y desactivar
la 1, nunca editarlos acá: hay firmas que apuntan a ellos.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op

revision: str = "0027"
down_revision: str | None = "0026"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SEMBRADO_EL = datetime(2026, 9, 21, tzinfo=UTC)

DECLARACION_INICIAL = """\
Declaro que soy el propietario de la mascota o la persona responsable de ella, y que puedo \
tomar decisiones sobre su atención.
"""

DECLARACION_FINAL = """\
Leí este texto, pude hacer las preguntas que necesitaba y lo acepto libremente. La información \
que di sobre mi mascota y sobre mí es verdadera.\
"""

CUERPO_PRONOSTICO_RESERVADO = f"""\
{DECLARACION_INICIAL}
1. Estado de la mascota. El médico veterinario me explicó que mi mascota tiene un pronóstico \
reservado: su estado es grave y hay un riesgo alto de que empeore o muera, aun con el \
tratamiento indicado.

2. Tratamiento y alternativas. Me explicó el tratamiento que propone, lo que se espera de él y \
sus límites, y las alternativas, incluidas la de limitar el tratamiento al alivio del dolor y \
del malestar y la de no tratar.

3. Sin garantía de resultado. Entiendo que el equipo veterinario no puede garantizar la \
recuperación de mi mascota.

4. Costo. Entiendo que el costo estimado que se me indica es aproximado y que puede cambiar \
según la evolución. El médico veterinario me avisará si va a superar de forma importante lo \
estimado.

5. Información y decisiones. Me mantendrán informado sobre la evolución. Puedo retirar este \
consentimiento en cualquier momento, sabiendo que interrumpir el tratamiento puede afectar la \
salud o la vida de mi mascota.

6. Declaración. {DECLARACION_FINAL}"""

CUERPO_PROCEDIMIENTO = f"""\
{DECLARACION_INICIAL}
1. Procedimiento. Autorizo al médico veterinario a realizar en mi mascota el procedimiento que \
se indica al pie de este texto. Me explicó en qué consiste, por qué lo recomienda y qué \
alternativas hay.

2. Riesgos. Entiendo que todo procedimiento invasivo tiene riesgos, entre ellos sangrado, \
infección, reacciones a los medicamentos, problemas de cicatrización y, en casos poco \
frecuentes, la muerte. Algunos riesgos dependen del estado de salud de mi mascota.

3. Imprevistos. Si durante el procedimiento aparece una situación que pone en riesgo la vida \
de mi mascota, autorizo al médico veterinario a hacer lo necesario para estabilizarla. \
Cualquier cambio que no sea urgente me lo consultará antes.

4. Anestesia. Si el procedimiento requiere anestesia o sedación, el médico veterinario me \
pedirá además el consentimiento específico para ella.

5. Cuidados posteriores. Me comprometo a seguir las indicaciones de cuidado y a asistir a los \
controles. Entiendo que no seguirlas puede afectar el resultado.

6. Costo. El costo estimado que figura abajo es aproximado: puede cambiar si surgen \
complicaciones o hace falta un tratamiento adicional.

7. Declaración. {DECLARACION_FINAL}"""

CUERPO_ANESTESIA = f"""\
{DECLARACION_INICIAL}
1. Autorización. Autorizo al médico veterinario a administrar a mi mascota la anestesia o la \
sedación necesaria para el procedimiento que se indica al pie de este texto.

2. Evaluación previa. Me explicaron que antes se evalúa a mi mascota y que pueden indicarse \
análisis para reducir el riesgo. Informé con verdad sobre su salud, los medicamentos que recibe \
y si comió en las horas previas.

3. Riesgos. Entiendo que toda anestesia o sedación tiene riesgos, aun en un animal sano y con \
un control adecuado: vómitos, reacciones alérgicas, alteraciones del ritmo del corazón o de la \
respiración, baja de temperatura y, en casos poco frecuentes, paro cardiorrespiratorio y muerte. \
El riesgo es mayor en animales de edad avanzada, con enfermedades previas o en estado crítico.

4. Control y medidas de emergencia. Durante la anestesia se controlarán sus signos vitales. Si \
se presenta una complicación, autorizo las maniobras de reanimación y los medicamentos de \
emergencia que hagan falta.

5. Recuperación. Entiendo que la recuperación puede tomar horas y que mi mascota puede necesitar \
quedarse en observación.

6. Declaración. {DECLARACION_FINAL}"""

CUERPO_INTERNACION = f"""\
{DECLARACION_INICIAL}
1. Autorización. Autorizo la internación de mi mascota en la clínica para su tratamiento y \
observación, por el motivo que se indica al pie de este texto.

2. Atención durante la internación. Autorizo al equipo veterinario a administrarle los \
medicamentos, fluidos, curaciones, análisis y demás cuidados que requiera su evolución. Una \
cirugía, una anestesia o cualquier otro procedimiento invasivo necesitará un consentimiento \
específico, salvo que su vida corra peligro inmediato y no sea posible ubicarme.

3. Riesgos. Entiendo que mi mascota puede empeorar o morir durante la internación a pesar de la \
atención, y que la internación puede causarle estrés.

4. Contacto. Me comprometo a mantener un teléfono disponible. La clínica me informará sobre la \
evolución y me avisará de cualquier cambio importante. Las visitas se coordinan con el equipo.

5. Costo. Entiendo que el costo depende de los días de internación y de los tratamientos que \
reciba; el monto estimado que figura abajo es aproximado.

6. Alta. El alta la decide el médico veterinario. Si decido retirar a mi mascota antes, lo haré \
bajo mi responsabilidad y dejaré constancia de ello.

7. Declaración. {DECLARACION_FINAL}"""

CUERPO_EUTANASIA = f"""\
Declaro que soy el propietario de la mascota o la persona responsable de ella, que soy mayor \
de edad y que puedo tomar esta decisión.

1. Solicitud voluntaria. Solicito de manera voluntaria, libre y sin presiones que se practique \
la eutanasia a mi mascota, por el motivo que se indica al pie de este texto.

2. Información recibida. El médico veterinario me explicó el estado de mi mascota, su \
pronóstico y las alternativas, incluidos los cuidados para aliviar su dolor y su malestar. Tuve \
tiempo para pensarlo y para hacer las preguntas que necesitaba.

3. Decisión irreversible. Entiendo que la eutanasia causa la muerte de mi mascota, que es \
definitiva y que no se puede revertir una vez realizada.

4. Procedimiento. Se realizará con sedación previa y con medicamentos destinados a que no \
sienta dolor ni angustia, según las buenas prácticas de la profesión. Puedo pedir estar \
presente o no.

5. Restos. Indicaré al equipo el destino de los restos de mi mascota, que se coordina por \
separado.

6. Declaración. Declaro que, hasta donde sé, mi mascota no mordió a ninguna persona en los \
últimos diez días. {DECLARACION_FINAL}"""

_TEXTOS: tuple[tuple[str, str, str], ...] = (
    (
        "high_risk",
        "Consentimiento informado ante un pronóstico reservado",
        CUERPO_PRONOSTICO_RESERVADO,
    ),
    (
        "procedure",
        "Consentimiento informado para cirugía o procedimiento invasivo",
        CUERPO_PROCEDIMIENTO,
    ),
    ("anesthesia", "Consentimiento informado para anestesia o sedación", CUERPO_ANESTESIA),
    ("hospitalization", "Consentimiento informado para internación", CUERPO_INTERNACION),
    ("euthanasia", "Consentimiento informado para eutanasia", CUERPO_EUTANASIA),
)


def plantillas_especificas() -> list[dict[str, object]]:
    """Las filas sembradas. Las pruebas las leen de acá para no copiar los textos."""
    return [
        {
            "kind": tipo,
            "version": 1,
            "title": titulo,
            "body": cuerpo,
            "is_active": True,
            "created_at": _SEMBRADO_EL,
        }
        for tipo, titulo, cuerpo in _TEXTOS
    ]


_PLANTILLAS = sa.table(
    "consent_templates",
    sa.column("kind", sa.String),
    sa.column("version", sa.Integer),
    sa.column("title", sa.String),
    sa.column("body", sa.Text),
    sa.column("is_active", sa.Boolean),
    sa.column("created_at", sa.DateTime(timezone=True)),
)


def upgrade() -> None:
    # En lote: SQLite no cambia la nulabilidad de una columna con un ALTER simple.
    with op.batch_alter_table("consents") as batch:
        batch.add_column(sa.Column("appointment_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("decision_reason", sa.Text(), nullable=True))
        batch.alter_column("channel", existing_type=sa.String(length=20), nullable=True)
        batch.alter_column("signer_name", existing_type=sa.String(length=120), nullable=True)
        batch.alter_column("decided_at", existing_type=sa.DateTime(timezone=True), nullable=True)
    op.create_index("ix_consents_appointment_id", "consents", ["appointment_id"], unique=False)
    op.bulk_insert(_PLANTILLAS, plantillas_especificas())


def downgrade() -> None:
    tipos = tuple(tipo for tipo, _, _ in _TEXTOS)
    conexion = op.get_bind()
    conexion.execute(
        sa.text("DELETE FROM consents WHERE kind IN :tipos").bindparams(
            sa.bindparam("tipos", expanding=True)
        ),
        {"tipos": list(tipos)},
    )
    conexion.execute(
        sa.text("DELETE FROM consent_templates WHERE kind IN :tipos").bindparams(
            sa.bindparam("tipos", expanding=True)
        ),
        {"tipos": list(tipos)},
    )
    op.drop_index("ix_consents_appointment_id", table_name="consents")
    with op.batch_alter_table("consents") as batch:
        batch.alter_column("decided_at", existing_type=sa.DateTime(timezone=True), nullable=False)
        batch.alter_column("signer_name", existing_type=sa.String(length=120), nullable=False)
        batch.alter_column("channel", existing_type=sa.String(length=20), nullable=False)
        batch.drop_column("decision_reason")
        batch.drop_column("appointment_id")
