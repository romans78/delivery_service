from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy import insert
from sqlalchemy.orm import sessionmaker

from models.packages import PackageCreate, PackageId, PackageType
from utils.db_utils import DATABASE_URL
from contextlib import asynccontextmanager
from db.packages import Package

router = APIRouter(prefix='/api/v1', tags=['deliveries'])

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=50,
    max_overflow=20,
    pool_recycle=3600
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=True,
    info=None
)


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

@router.post('/package',
             response_model=PackageId,
             description='This method registers a package')
async def register_package(package: PackageCreate, db: AsyncSession = Depends(get_db)):
    d = package.__dict__

    #stmt = insert(Package).values(d).returning(Package.id)
    new_package = Package(**d)
    db.add(new_package)
    await db.commit()
    await db.refresh(new_package)
    id = new_package.id
    return PackageId(id=id)



