import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.config import settings
from app.database import get_db
from app.main import app
from app.models import Base, User

TEST_DATABASE_URL = (
    f"postgresql+asyncpg://{settings.postgres_user}:{settings.postgres_password}"
    f"@{settings.postgres_host}:{settings.postgres_port}/flashcart_test"
)

test_engine = create_async_engine(TEST_DATABASE_URL)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _setup_test_schema():
    """Rebuild the test database schema once per test run.

    Using Base.metadata directly (not Alembic) is fine here because the goal is a
    schema matching the current models, not exercising migrations themselves.
    """
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    await test_engine.dispose()


@pytest_asyncio.fixture
async def db_session():
    """One isolated transaction per test.

    join_transaction_mode="create_savepoint" means the app code's own
    `await db.commit()` calls only release a SAVEPOINT, not the outer transaction.
    Rolling back the outer transaction after the test undoes everything the test
    (and the route code it exercised) did, regardless of how many commits happened.
    """
    async with test_engine.connect() as connection:
        trans = await connection.begin()
        session = AsyncSession(
            bind=connection,
            join_transaction_mode="create_savepoint",
            expire_on_commit=False,
        )
        try:
            yield session
        finally:
            await session.close()
            await trans.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


async def register_and_login(client: AsyncClient, email: str, password: str, name: str = "Test User") -> str:
    """Register a user and log in, returning a bearer token for use in Authorization headers."""
    await client.post("/register", json={"name": name, "email": email, "password": password})
    response = await client.post("/auth/login", json={"email": email, "password": password})
    return response.json()["access_token"]


async def make_admin(db_session: AsyncSession, email: str) -> None:
    """Promote a user to admin, using the SAME session/transaction as the test.

    Goes through the ORM (not a raw UPDATE) so SQLAlchemy's identity map stays
    consistent -- a raw SQL update wouldn't refresh any User object already loaded
    into this session, leaving stale cached data visible to later queries.
    """
    result = await db_session.execute(select(User).where(User.email == email))
    user = result.scalar_one()
    user.role = "admin"
    await db_session.flush()


