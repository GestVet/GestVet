"""Las migraciones tienen que reproducir el modelo, no parecerse a él.

Sin esta prueba la deriva es silenciosa: alguien agrega una columna al modelo,
las pruebas pasan porque crean las tablas desde el metadata, y el despliegue
falla contra una base migrada que no tiene esa columna.

Es una prueba síncrona a propósito: `alembic` abre su propio bucle de eventos y
no puede anidarse dentro del que abriría pytest-asyncio.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine

from gestvet.accounts.adapters.persistence import models as accounts_models  # noqa: F401
from gestvet.core.config import get_settings
from gestvet.core.database import Base

BACKEND_ROOT = Path(__file__).resolve().parents[1]


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
