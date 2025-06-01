from typing import List

from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy import select, insert
from sqlalchemy.orm import sessionmaker

from models.packages import PackageCreate, PackageId, PackageType, PackageInfo
from utils.db_utils import DATABASE_URL
from db.packages import PackageTable, PackageTypeTable
from utils.session import get_session_id

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
async def register_package(package: PackageCreate,
                           db: AsyncSession = Depends(get_db),
                           session_id: str = Depends(get_session_id)):
    new_package = PackageTable(
        name=package.name,
        weight=package.weight,
        type_id=1,
        content_value_usd=package.content_value_usd,
        session_id=session_id,
        delivery_cost=None
    )
    db.add(new_package)
    await db.commit()
    await db.refresh(new_package)
    package_id = new_package.id
    return PackageId(id=package_id)


@router.get('/package_types', response_model=List[PackageType],
            description='This method returns package types and their ids')
async def get_package_types(db: AsyncSession = Depends(get_db)):
    stmt = select(PackageTypeTable)
    result = await db.scalars(stmt)
    package_type_list = result.all()
    return package_type_list


@router.get('/packages', response_model=List[PackageInfo] | dict[str, str],
            description='This method returns all user packages')
async def get_packages_by_session(db: AsyncSession = Depends(get_db),
                                  session_id: str = Depends(get_session_id)):
    stmt = select(PackageTable.name, PackageTable.weight, PackageTypeTable.type_name.label('type'),
                  PackageTable.content_value_usd,
                  PackageTable.delivery_cost).join(PackageTypeTable,
                                                   PackageTable.type_id == PackageTypeTable.id).where(
        PackageTable.session_id == session_id)
    result = (await db.execute(stmt)).all()
    return result


@router.get('/package/{package_id}', response_model=PackageInfo | dict[str, str],
            description='This method returns package info by id')
async def get_package_info_by_id(package_id: int = Path(...), db: AsyncSession = Depends(get_db)):
    stmt = select(PackageTable.name, PackageTable.weight, PackageTypeTable.type_name.label('type'),
                  PackageTable.content_value_usd,
                  PackageTable.delivery_cost).join(PackageTypeTable,
                                                   PackageTable.type_id == PackageTypeTable.id).where(
        PackageTable.id == package_id)
    result = (await db.execute(stmt)).first()
    if result:
        package = list(result)
        if package[-1] is None:
            package[-1] = 'Не рассчитано'
        return PackageInfo(name=package[0],
                           weight=package[1],
                           type=package[2],
                           content_value_usd=package[3],
                           delivery_cost=package[4])
    else:
        return {"message": f"No package for id {package_id}"}
