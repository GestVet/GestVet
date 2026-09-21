"""Infraestructura compartida de las pruebas.

Cada prueba recibe una base SQLite en memoria propia, así que el orden en que
corren no puede influir en el resultado. `StaticPool` es imprescindible: sin él
cada conexión abriría su propia base en memoria y las tablas creadas por una no
existirían para la siguiente.
"""

from __future__ import annotations

import importlib.util
from collections.abc import AsyncIterator
from datetime import date
from decimal import Decimal
from pathlib import Path
from types import ModuleType

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from gestvet.core.activity import ActivityKind
from gestvet.core.activity_log import ActivityRow
from gestvet.core.auth import get_token_service
from gestvet.core.database import Base, get_session, get_session_factory
from gestvet.core.dni_reniec import get_identity_registry
from gestvet.core.identity import Role
from gestvet.core.identity_registry import IdentityRegistryUnavailable, PersonName
from gestvet.core.llm import JsonCompletion, JsonCompletionRequest, LlmUnavailable
from gestvet.core.llm_openrouter import get_llm_client
from gestvet.core.permissions import SYSTEM_ROLE_NAMES, SYSTEM_ROLE_PERMISSIONS
from gestvet.core.realtime_broker import LocalBroker, get_broker
from gestvet.core.security import BcryptPasswordHasher
from gestvet.core.tokens import JwtTokenService
from gestvet.main import create_app
from gestvet.modules.access.adapters.persistence import models as access_models
from gestvet.modules.access.adapters.persistence.models import (
    AccessRolePermissionRow,
    AccessRoleRow,
)
from gestvet.modules.accounts.adapters.api.dependencies import (
    get_email_sender,
    get_password_hasher,
)
from gestvet.modules.accounts.adapters.persistence import models as accounts_models
from gestvet.modules.accounts.adapters.persistence.models import SpecialtyRow
from gestvet.modules.accounts.adapters.persistence.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from gestvet.modules.accounts.domain.entities import User
from gestvet.modules.appointments.adapters.persistence import models as appointments_models
from gestvet.modules.appointments.adapters.persistence.models import AppointmentTypeRow
from gestvet.modules.availability.adapters.persistence import (
    models as availability_models,
)
from gestvet.modules.billing.adapters.persistence import models as billing_models
from gestvet.modules.complaints.adapters.api.dependencies import get_evidence_storage
from gestvet.modules.complaints.adapters.persistence import models as complaints_models
from gestvet.modules.hospitalizations.adapters.persistence import (
    models as hospitalizations_models,
)
from gestvet.modules.medical_records.adapters.api.dependencies import get_attachment_storage
from gestvet.modules.medical_records.adapters.persistence import (
    models as medical_records_models,
)
from gestvet.modules.pets.adapters.persistence import models as pets_models
from gestvet.modules.pets.adapters.persistence.models import PetBreedRow, PetSpeciesRow
from gestvet.modules.pets.domain.entities import Pet
from gestvet.modules.reviews.adapters.persistence import models as reviews_models

# Cuatro rondas en vez de doce. El algoritmo es el mismo que en producción, que
# es lo que interesa probar; el costo deliberado no aporta nada a una prueba.
TEST_HASHER = BcryptPasswordHasher(rounds=4)
TEST_TOKEN_SERVICE = JwtTokenService(
    secret_key="secreto-de-prueba-con-largo-suficiente",
    algorithm="HS256",
    ttl_seconds=3600,
)
# Los modelos se importan para que sus tablas queden registradas en
# `Base.metadata` antes de crearlas. La tupla hace explicita esa intencion.
REGISTERED_MODELS = (
    ActivityRow,
    access_models,
    accounts_models,
    appointments_models,
    availability_models,
    billing_models,
    complaints_models,
    hospitalizations_models,
    medical_records_models,
    pets_models,
    reviews_models,
)

VALID_PASSWORD = "contrasena-larga"

# Copia de lo que siembra la migracion 0004.
REFERENCE_TYPES = [
    {
        "name": "Consulta general",
        "duration_minutes": 30,
        "price": Decimal("60.00"),
        "is_emergency": False,
        "is_active": True,
    },
    {
        "name": "Cirugia menor",
        "duration_minutes": 90,
        "price": Decimal("350.00"),
        "is_emergency": False,
        "is_active": True,
    },
    {
        "name": "Emergencia",
        "duration_minutes": 60,
        "price": Decimal("150.00"),
        "is_emergency": True,
        "is_active": True,
    },
]
GENERAL_TYPE_ID = 1
SURGERY_TYPE_ID = 2
EMERGENCY_TYPE_ID = 3

# La primera especialidad sembrada, para las pruebas que solo necesitan una
# válida y no les importa cuál.
DEFAULT_SPECIALTY_ID = 1

# Un rol de sistema por tipo de cuenta, con identificador fijo para que las
# pruebas puedan referirse a ellos.
SYSTEM_ROLE_IDS: dict[Role, int] = {kind: index for index, kind in enumerate(Role, start=1)}
SYSTEM_ROLES = [
    {
        "id": SYSTEM_ROLE_IDS[kind],
        "name": SYSTEM_ROLE_NAMES[kind],
        "description": "",
        "account_kind": kind.value,
        "is_system": True,
    }
    for kind in Role
]
SYSTEM_ROLE_PERMISSION_ROWS = [
    {"role_id": SYSTEM_ROLE_IDS[kind], "permission": permission.value}
    for kind, permissions in SYSTEM_ROLE_PERMISSIONS.items()
    for permission in sorted(permissions)
]

CATALOG_MIGRATION = (
    Path(__file__).resolve().parents[1]
    / "alembic"
    / "versions"
    / "0020_crear_el_catalogo_de_especies_y_razas.py"
)


def load_catalog_migration() -> ModuleType:
    """La migración que siembra el catálogo: se lee de ahí para no copiar la lista."""
    spec = importlib.util.spec_from_file_location("catalog_migration", CATALOG_MIGRATION)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"No se pudo cargar {CATALOG_MIGRATION}.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_catalog_migration = load_catalog_migration()
CATALOG_SPECIES_ROWS = [
    {"id": index, **row}
    for index, row in enumerate(_catalog_migration.filas_de_especies(), start=1)
]
CATALOG_BREED_ROWS = _catalog_migration.filas_de_razas(
    {row["name"]: row["id"] for row in CATALOG_SPECIES_ROWS}
)

SPECIALTIES_MIGRATION = (
    Path(__file__).resolve().parents[1]
    / "alembic"
    / "versions"
    / "0025_agregar_las_especialidades_veterinarias.py"
)


def load_specialties_migration() -> ModuleType:
    """La migración que siembra las especialidades: se lee de ahí para no copiar la lista."""
    spec = importlib.util.spec_from_file_location("specialties_migration", SPECIALTIES_MIGRATION)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"No se pudo cargar {SPECIALTIES_MIGRATION}.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_specialties_migration = load_specialties_migration()
CATALOG_SPECIALTY_ROWS = [
    {"id": index, **row}
    for index, row in enumerate(_specialties_migration.filas_de_especialidades(), start=1)
]


@pytest.fixture
async def session() -> AsyncIterator[AsyncSession]:
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
        # Los motivos de consulta son datos de referencia que en produccion
        # siembra la migracion. Sin ellos no se puede reservar nada.
        await connection.execute(insert(AppointmentTypeRow), REFERENCE_TYPES)
        # Los roles de sistema también los siembra una migración. Sin ellos
        # ninguna cuenta tendría permisos y todo respondería 403.
        await connection.execute(insert(AccessRoleRow), SYSTEM_ROLES)
        await connection.execute(insert(AccessRolePermissionRow), SYSTEM_ROLE_PERMISSION_ROWS)
        # El catálogo de especies y razas también: sin él no se registra ninguna mascota.
        await connection.execute(insert(PetSpeciesRow), CATALOG_SPECIES_ROWS)
        await connection.execute(insert(PetBreedRow), CATALOG_BREED_ROWS)
        # Y el de especialidades: sin él no se puede dar de alta a un veterinario.
        await connection.execute(insert(SpecialtyRow), CATALOG_SPECIALTY_ROWS)

    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with factory() as open_session:
        yield open_session

    await engine.dispose()


@pytest.fixture
def users(session: AsyncSession) -> SqlAlchemyUserRepository:
    return SqlAlchemyUserRepository(session)


@pytest.fixture
def sent_emails() -> list[tuple[str, str]]:
    """Correos que un caso de uso pidió mandar durante la prueba.

    Cada elemento es (destinatario, URL). Ninguna prueba manda correo de
    verdad: `client` reemplaza el remitente real por uno que solo anota acá.
    """
    return []


class FakeLlmClient:
    """Asistente de prueba: anota lo que se le pide y responde lo configurado.

    Con `response = None` se comporta como un asistente apagado.
    """

    def __init__(self) -> None:
        self.requests: list[JsonCompletionRequest] = []
        self.response: dict[str, object] | None = {
            "resumen": "Mascota sana, sin novedades.",
            "alertas": [],
            "pendientes": [],
        }

    async def complete_json(self, request: JsonCompletionRequest) -> JsonCompletion:
        self.requests.append(request)
        if self.response is None:
            raise LlmUnavailable("El asistente de IA no está configurado en este servidor.")
        return JsonCompletion(data=self.response, model="modelo-de-prueba")


class FakeIdentityRegistry:
    """Registro de DNI de prueba.

    Con `people = None` se comporta como sin proveedor: el registro no verifica
    y la consulta responde que no está disponible.
    """

    def __init__(self) -> None:
        self.people: dict[str, PersonName] | None = None
        self.lookups: list[str] = []

    @property
    def available(self) -> bool:
        return self.people is not None

    async def lookup(self, document_id: str) -> PersonName | None:
        if self.people is None:
            raise IdentityRegistryUnavailable(
                "La consulta de DNI no está configurada en este servidor."
            )
        self.lookups.append(document_id)
        return self.people.get(document_id)


@pytest.fixture
def identity_registry() -> FakeIdentityRegistry:
    """Ninguna prueba consulta un DNI real, aunque el `.env` tenga una clave."""
    return FakeIdentityRegistry()


@pytest.fixture
def llm() -> FakeLlmClient:
    """Ninguna prueba llama a un modelo real, aunque el `.env` tenga una clave."""
    return FakeLlmClient()


@pytest.fixture
def broker() -> LocalBroker:
    """Reparto de avisos en memoria: ninguna prueba abre `LISTEN` en Postgres."""
    return LocalBroker()


@pytest.fixture
async def client(
    session: AsyncSession,
    sent_emails: list[tuple[str, str]],
    broker: LocalBroker,
    llm: FakeLlmClient,
    identity_registry: FakeIdentityRegistry,
) -> AsyncIterator[AsyncClient]:
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

    class RecordingEmailSender:
        async def send_password_reset(self, *, to: str, reset_url: str) -> None:
            sent_emails.append((to, reset_url))

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_session_factory] = lambda: async_sessionmaker(
        session.bind, expire_on_commit=False, class_=AsyncSession
    )
    app.dependency_overrides[get_password_hasher] = lambda: TEST_HASHER
    app.dependency_overrides[get_token_service] = lambda: TEST_TOKEN_SERVICE
    app.dependency_overrides[get_email_sender] = lambda: RecordingEmailSender()
    # Una sola instancia por prueba: lo que sube una petición lo lee la siguiente.
    storage = InMemoryAttachmentStorage()
    app.dependency_overrides[get_attachment_storage] = lambda: storage
    app.dependency_overrides[get_evidence_storage] = lambda: storage
    app.dependency_overrides[get_broker] = lambda: broker
    app.dependency_overrides[get_llm_client] = lambda: llm
    app.dependency_overrides[get_identity_registry] = lambda: identity_registry

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client


def build_user(
    email: str,
    role: Role = Role.CLIENT,
    first_name: str = "Ana",
    last_name: str = "Quispe",
    phone: str = "",
    document_id: str = "",
    is_active: bool = True,
) -> User:
    return User(
        email=email,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        document_id=document_id,
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


class InMemoryAttachmentStorage:
    """Guarda los bytes en un diccionario en vez de en disco.

    Ninguna prueba necesita que el archivo sobreviva al proceso; le alcanza
    con que `save`, `read` y `delete` se comporten como el adaptador real.
    """

    def __init__(self) -> None:
        self.saved: dict[str, bytes] = {}

    async def save(self, key: str, content: bytes, content_type: str) -> None:
        del content_type
        self.saved[key] = content

    async def read(self, key: str) -> bytes:
        if key not in self.saved:
            raise FileNotFoundError(key)
        return self.saved[key]

    async def delete(self, key: str) -> None:
        self.saved.pop(key, None)


class RecordingActivity:
    """Bitácora en memoria, para afirmar qué asientos dejó un caso de uso."""

    def __init__(self) -> None:
        self.entries: list[tuple[int, ActivityKind, str]] = []

    async def record(self, user_id: int, kind: ActivityKind, detail: str = "") -> None:
        self.entries.append((user_id, kind, detail))

    def kinds(self) -> list[ActivityKind]:
        return [kind for _, kind, _ in self.entries]
