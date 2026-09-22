"""Las migraciones tienen que reproducir el modelo, no parecerse a él.

Sin esta prueba la deriva es silenciosa: alguien agrega una columna al modelo,
las pruebas pasan porque crean las tablas desde el metadata, y el despliegue
falla contra una base migrada que no tiene esa columna.

Es una prueba síncrona a propósito: `alembic` abre su propio bucle de eventos y
no puede anidarse dentro del que abriría pytest-asyncio.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, text

from gestvet.core.config import get_settings
from gestvet.core.database import Base
from gestvet.core.permissions import SYSTEM_ROLE_PERMISSIONS
from gestvet.modules.consents.domain.entities import ConsentKind
from tests.conftest import REGISTERED_MODELS

BACKEND_ROOT = Path(__file__).resolve().parents[1]

# El metadata tiene que estar completo antes de comparar: sin los modelos
# registrados, la comparacion no veria ninguna tabla y pasaria siempre.
assert REGISTERED_MODELS


@pytest.fixture
def migrated_database(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    database = tmp_path / "migrada.db"

    # `env.py` toma la URL de la configuración de la aplicación, así que hay que
    # apuntarla al archivo temporal y limpiar la caché que la memoriza.
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{database.as_posix()}")
    get_settings.cache_clear()

    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    command.upgrade(config, "head")

    yield database

    get_settings.cache_clear()


def test_las_migraciones_reproducen_el_modelo(migrated_database: Path) -> None:
    engine = create_engine(f"sqlite:///{migrated_database.as_posix()}")
    try:
        with engine.connect() as connection:
            context = MigrationContext.configure(connection)
            diferencias = compare_metadata(context, Base.metadata)
    finally:
        engine.dispose()

    assert diferencias == [], (
        "El modelo y las migraciones divergieron. Generá la migración que falta con "
        "`uv run --directory backend alembic revision --autogenerate -m '...'`."
    )


def test_la_migracion_siembra_los_roles_de_sistema_del_codigo(migrated_database: Path) -> None:
    """La semilla de la migración está escrita a mano; no puede apartarse del código."""
    engine = create_engine(f"sqlite:///{migrated_database.as_posix()}")
    try:
        with engine.connect() as connection:
            filas = connection.execute(
                text(
                    "SELECT r.account_kind, p.permission FROM access_roles r "
                    "JOIN access_role_permissions p ON p.role_id = r.id WHERE r.is_system = 1"
                )
            ).all()
    finally:
        engine.dispose()

    sembrado: dict[str, set[str]] = defaultdict(set)
    for tipo, permiso in filas:
        sembrado[tipo].add(permiso)
    esperado = {
        kind.value: {permission.value for permission in permissions}
        for kind, permissions in SYSTEM_ROLE_PERMISSIONS.items()
    }
    assert dict(sembrado) == esperado


def test_la_migracion_siembra_el_texto_de_riesgo_de_emergencia(migrated_database: Path) -> None:
    engine = create_engine(f"sqlite:///{migrated_database.as_posix()}")
    try:
        with engine.connect() as connection:
            filas = connection.execute(
                text(
                    "SELECT kind, version, is_active, body FROM consent_templates "
                    "WHERE kind = 'emergency_risk'"
                )
            ).all()
    finally:
        engine.dispose()

    assert [(kind, version, bool(activa)) for kind, version, activa, _ in filas] == [
        ("emergency_risk", 1, True)
    ]
    cuerpo = filas[0][3]
    for idea in ("morir", "estabilizar", "costo", "consentimiento específico", "responsable"):
        assert idea in cuerpo


def test_la_migracion_siembra_los_textos_especificos(migrated_database: Path) -> None:
    engine = create_engine(f"sqlite:///{migrated_database.as_posix()}")
    try:
        with engine.connect() as connection:
            filas = dict(
                connection.execute(
                    text(
                        "SELECT kind, body FROM consent_templates "
                        "WHERE version = 1 AND is_active = 1 AND kind != 'emergency_risk'"
                    )
                ).all()
            )
    finally:
        engine.dispose()

    assert set(filas) == {
        kind.value for kind in ConsentKind if kind is not ConsentKind.EMERGENCY_RISK
    }
    for cuerpo in filas.values():
        assert "responsable" in cuerpo
        assert "Declaración." in cuerpo
    assert "irreversible" in filas["euthanasia"] or "revertir" in filas["euthanasia"]
    assert "voluntaria" in filas["euthanasia"]
    assert "muera" in filas["high_risk"]
