import os

import asyncio
import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from httpx import ASGITransport

from db.base import Base
from main import app
from utils.session import get_session_id, get_db
from db.packages import PackageTypeTable

# Set testing mode
os.environ['TESTING'] = 'True'
os.environ['TEST_DATABASE_NAME'] = 'test_delivery_service'


# Test database settings
TEST_DB_URL = (f'mysql+asyncmy://{os.environ["DATABASE_USER"]}:{os.environ["DATABASE_PASSWORD"]}'
               f'@{os.environ["DATABASE_HOST"]}:{os.environ["DATABASE_PORT"]}/{os.environ["TEST_DATABASE_NAME"]}')


@pytest.fixture(scope='session')
def event_loop():
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='session')
def apply_migrations():
    # Create a separate test database
    admin_url = (f'mysql+pymysql://{os.environ["DATABASE_USER"]}:{os.environ["DATABASE_PASSWORD"]}'
                 f'@{os.environ["DATABASE_HOST"]}:{os.environ["DATABASE_PORT"]}/')
    engine = create_engine(admin_url)
    with engine.connect() as conn:
        conn.execute(text(f'DROP DATABASE IF EXISTS {os.environ["TEST_DATABASE_NAME"]}'))
        conn.execute(text(f'CREATE DATABASE {os.environ["TEST_DATABASE_NAME"]}'))
    yield
    with engine.connect() as conn:
        conn.execute(text(f'DROP DATABASE {os.environ["TEST_DATABASE_NAME"]}'))


@pytest.fixture(autouse=True)
async def db(apply_migrations):
    engine = create_async_engine(
        TEST_DB_URL,
        pool_pre_ping=True,
        echo=False
    )
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async_session = sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=True
    )

    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
    await engine.dispose()


@pytest.fixture
async def client(db):
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_session_id] = lambda: "test_session_id"

    async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
    ) as ac:
        yield ac


# Fixture for prepopulating package types
@pytest.fixture(autouse=True)
async def prepopulate_db(db):
    package_types = ['одежда', 'электроника', 'разное']
    await db.execute(text('DELETE FROM package_type WHERE id > 3'))
    for name in package_types:
        db.add(PackageTypeTable(type_name=name))
    await db.commit()
