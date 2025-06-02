from typing import List, Optional

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.packages import PackageCreate, PackageId, PackageType, PackageInfo, PaginatedPackages
from db.packages import PackageTable, PackageTypeTable
from utils.session import get_session_id, get_db
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate

router = APIRouter(prefix='/api/v1', tags=['deliveries'])


@router.post('/package',
             response_model=PackageId,
             description='This method registers a package')
async def register_package(package: PackageCreate,
                           db: AsyncSession = Depends(get_db),
                           session_id: str = Depends(get_session_id)):
    stmt = select(PackageTypeTable.id).where(PackageTypeTable.type_name == package.type_name.lower())
    type_id = list((await db.execute(stmt)).first())[0]
    new_package = PackageTable(
        name=package.name,
        weight=package.weight,
        type_id=type_id,
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


# @router.get('/packages', response_model=PaginatedPackages,
#             description='This method returns all user packages')
# async def get_packages_by_session(page: int = Query(1, ge=1, description='Номер страницы'),
#                                   limit: int = Query(10, ge=1, le=100, description='Записей на странице'),
#                                   type_name: Optional[str] = Query(None, description='Фильтр по типу посылки'),
#                                   has_delivery_cost: Optional[bool] = Query(None, description='Фильтр по наличию расчёта стоимости'),
#                                   db: AsyncSession = Depends(get_db),
#                                   session_id: str = Depends(get_session_id)):
#     offset = (page - 1) * limit
#
#     stmt = select(PackageTable.id, PackageTable.name, PackageTable.weight, PackageTable.type_id,
#                   PackageTypeTable.type_name, PackageTable.content_value_usd, PackageTable.delivery_cost).join(
#         PackageTypeTable, PackageTable.type_id == PackageTypeTable.id).where(PackageTable.session_id == session_id)
#     if type_name is not None:
#         stmt = stmt.where(PackageTypeTable.type_name==type_name)
#     if has_delivery_cost is not None:
#         if has_delivery_cost:
#             stmt = stmt.where(PackageTable.delivery_cost.is_not(None))
#         else:
#             stmt = stmt.where(PackageTable.delivery_cost.is_(None))
#     stmt = stmt.offset(offset).limit(limit)
#     result = (await db.execute(stmt)).all()
#
#     packages = result
#     return result

@router.get('/packages', response_model=Page[PackageInfo],
            description='This method returns all user packages')
async def get_package_info_by_session_id(type_name: Optional[str] = Query(None, description='Фильтр по типу посылки'),
                                         has_delivery_cost: Optional[bool] = Query(None, description='Фильтр по наличию расчёта стоимости'),
                                         db: AsyncSession = Depends(get_db),
                                         session_id: str = Depends(get_session_id)):
    stmt = select(PackageTable.id, PackageTable.name, PackageTable.weight, PackageTable.type_id,
                  PackageTypeTable.type_name, PackageTable.content_value_usd, PackageTable.delivery_cost).join(
        PackageTypeTable, PackageTable.type_id == PackageTypeTable.id).where(PackageTable.session_id == session_id)
    if type_name is not None:
        stmt = stmt.where(PackageTypeTable.type_name==type_name)
    if has_delivery_cost is not None:
        if has_delivery_cost:
            stmt = stmt.where(PackageTable.delivery_cost.is_not(None))
        else:
            stmt = stmt.where(PackageTable.delivery_cost.is_(None))
    stmt = stmt.order_by(PackageTable.id)
    return await paginate(db, stmt)



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
                           type_name=package[2],
                           content_value_usd=package[3],
                           delivery_cost=package[4])
    else:
        return {"message": f"No package for id {package_id}"}
