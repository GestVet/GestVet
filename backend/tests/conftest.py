"""Infraestructura compartida de las pruebas.

Cada prueba recibe una base SQLite en memoria propia, así que el orden en que
corren no puede influir en el resultado. `StaticPool` es imprescindible: sin él
cada conexión abriría su propia base en memoria y las tablas creadas por una no
existirían para la siguiente.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import date

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from gestvet.accounts.adapters.api.dependencies import get_password_hasher
from gestvet.accounts.adapters.persistence import models as accounts_models  # noqa: F401
from gestvet.accounts.adapters.persistence.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from gestvet.accounts.domain.entities import User
from gestvet.core.auth import get_token_service
from gestvet.core.database import Base, get_session
from gestvet.core.identity import Role
from gestvet.core.security import BcryptPasswordHasher
from gestvet.core.tokens import JwtTokenService
from gestvet.main import create_app
from gestvet.pets.adapters.persistence import models as pets_models  # noqa: F401
from gestvet.pets.domain.entities import Pet

# Cuatro rondas en vez de doce. El algoritmo es el mismo que en producción, que
# es lo que interesa probar; el costo deliberado no aporta nada a una prueba.
TEST_HASHER = BcryptPasswordHasher(rounds=4)
TEST_TOKEN_SERVICE = JwtTokenService(
    secret_key="secreto-de-prueba-con-largo-suficiente",
    algorithm="HS256",
    ttl_seconds=3600,
)
VALID_PASSWORD = "contrasena-larga"


@pytest.fixture
async def session() -> AsyncIterator[AsyncSession]:
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with factory() as open_session:
        yield open_session

    await engine.dispose()


@pytest.fixture
def users(session: AsyncSession) -> SqlAlchemyUserRepository:
    return SqlAlchemyUserRepository(session)


@pytest.fixture
async def client(session: AsyncSession) -> AsyncIterator[AsyncClient]:
    app = create_app()

    async def override_session() -> AsyncIterator[AsyncSession]:
        # Se replica el ciclo de `get_session`, confirmar al terminar y
        # deshacer ante un error, para que las pruebas ejerciten la misma
        # transacción que sirve una petición real.
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_password_hasher] = lambda: TEST_HASHER
    app.dependency_overrides[get_token_service] = lambda: TEST_TOKEN_SERVICE

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client


def build_user(
    email: str,
    role: Role = Role.CLIENT,
    first_name: str = "Ana",
    last_name: str = "Quispe",
    phone: str = "",
    is_active: bool = True,
) -> User:
    return User(
        email=email,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        role=role,
        password_hash=TEST_HASHER.hash(VALID_PASSWORD),
        is_active=is_active,
    )


def authorization_for(user: User) -> dict[str, str]:
    """Cabecera de acceso para un usuario ya persistido."""
    if user.id is None:
        raise ValueError("El usuario debe estar persistido para emitirle un token.")
    token = TEST_TOKEN_SERVICE.issue(user.id, user.role)
    return {"Authorization": f"Bearer {token.value}"}


def build_pet(
    owner_id: int,
    name: str = "Rocco",
    species: str = "Perro",
    breed: str = "Mestizo",
    birth_date: date | None = None,
    is_active: bool = True,
) -> Pet:
    return Pet(
        name=name,
        species=species,
        breed=breed,
        birth_date=birth_date or date(2020, 5, 17),
        owner_id=owner_id,
        is_active=is_active,
    )
