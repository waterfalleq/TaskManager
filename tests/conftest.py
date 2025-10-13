import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.db.database import Base, get_db

DATABASE_URL = "postgresql+asyncpg://test_user:test_password@localhost:5433/test_db"

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncTestingSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

@pytest.fixture(scope="session")
async def prepare_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def async_client(prepare_database):
    # override зависимости
    async def override_get_db():
        async with AsyncTestingSessionLocal() as session:
            yield session
    from app.main import app
    app.dependency_overrides[get_async_db] = override_get_db

    from httpx import AsyncClient
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
