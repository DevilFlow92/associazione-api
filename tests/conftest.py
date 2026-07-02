from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.api.deps import get_current_user
from app.core.database import Base, get_db
from app.models.utente import TipoUtente, Utente
from main import app

engine_test = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
AsyncSessionTest = async_sessionmaker(bind=engine_test, expire_on_commit=False)


@pytest.fixture(autouse=True)
async def setup_db():
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session() -> AsyncSession:
    async with AsyncSessionTest() as session:
        yield session


@pytest.fixture
async def client(
    db_session: AsyncSession, request: pytest.FixtureRequest
) -> AsyncClient:
    async def override_get_db():
        yield db_session

    async def override_get_current_user():
        return Utente(
            id=1, tipo=TipoUtente.UMANO, email="test@example.com", superuser=True
        )

    app.dependency_overrides[get_db] = override_get_db
    # I router delle entità sono protetti da ``get_current_user``. Per i test
    # funzionali sostituiamo il principal con un superuser, così da esercitare
    # gli endpoint senza autenticazione reale. Il modulo ``test_auth`` verifica
    # il meccanismo di autenticazione stesso e quindi mantiene la dipendenza
    # originale.
    if not request.module.__name__.endswith("test_auth"):
        app.dependency_overrides[get_current_user] = override_get_current_user
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="https://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()
