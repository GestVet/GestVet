"""Pruebas de la configuración y validadores del entorno."""

from __future__ import annotations

import pytest

from gestvet.core.config import INSECURE_DEFAULT_SECRET, Settings


def test_produccion_rechaza_sqlite() -> None:
    with pytest.raises(ValueError, match="DATABASE_URL apunta a SQLite en producción"):
        Settings(
            _env_file=None,
            debug=False,
            jwt_secret_key="una-clave-secreta-suficientemente-larga-de-32-caracteres",
            database_url="sqlite+aiosqlite:///./gestvet.db",
        )


def test_produccion_rechaza_jwt_secret_de_desarrollo() -> None:
    with pytest.raises(ValueError, match="JWT_SECRET_KEY conserva el valor de desarrollo"):
        Settings(
            _env_file=None,
            debug=False,
            jwt_secret_key=INSECURE_DEFAULT_SECRET,
            database_url="postgresql+asyncpg://usuario:clave@host:5432/gestvet",
        )


def test_produccion_acepta_postgres_y_secret_propio() -> None:
    settings = Settings(
        _env_file=None,
        debug=False,
        jwt_secret_key="una-clave-secreta-suficientemente-larga-de-32-caracteres",
        database_url="postgresql+asyncpg://usuario:clave@host:5432/gestvet",
    )
    assert not settings.debug
    assert settings.database_url.startswith("postgresql")


def test_desarrollo_permite_sqlite_y_secret_por_defecto() -> None:
    settings = Settings(_env_file=None, debug=True)
    assert settings.debug
    assert settings.database_url.startswith("sqlite")
    assert settings.jwt_secret_key == INSECURE_DEFAULT_SECRET


def test_la_simulacion_del_qr_sigue_a_debug_si_no_se_define() -> None:
    assert Settings(_env_file=None, debug=True).qr_simulation_enabled is True
    produccion = Settings(
        _env_file=None,
        debug=False,
        jwt_secret_key="x" * 40,
        database_url="postgresql+asyncpg://u:p@h/db",
    )
    assert produccion.qr_simulation_enabled is False


def test_la_simulacion_del_qr_se_puede_fijar_a_mano() -> None:
    assert (
        Settings(_env_file=None, debug=True, qr_simulation_enabled=False).qr_simulation_enabled
        is False
    )
