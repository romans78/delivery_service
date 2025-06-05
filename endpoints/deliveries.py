import logging

from fastapi import APIRouter, Depends, Path, Query, HTTPException, status
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import apaginate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, case, literal_column, String, cast

from utils.session import get_session_id, get_db
from models.packages import PackageCreate, PackageId, PackageType, PackageInfo, PackageInfoNoId
from db.packages import PackageTable, PackageTypeTable

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix='/api/v1', tags=['deliveries'])


@router.post('/package',
             response_model=PackageId,
             description='This method registers a package')
async def register_package(package: PackageCreate,
                           db: AsyncSession = Depends(get_db),
                           session_id: str = Depends(get_session_id)) -> PackageId:
    """
        Registers a new package in the system.

        Creates a package record associated with the current session.
        The Initial delivery cost is set to None until calculated separately.

        Args:
            package (PackageCreate): Package creation payload containing:
                - name: str - Package display name
                - weight: float - Package weight in kg
                - type_name: str - Package type name
                - content_value_usd: float - Declared value in USD
            db (AsyncSession): Database session dependency
            session_id (str): Authenticated session identifier

        Returns:
            PackageId: The ID of the created package
    """
    logger.info(f'Registering package for session id: {session_id}')
    stmt = select(PackageTypeTable.id).where(PackageTypeTable.type_name == package.type_name.lower())
    result = (await db.execute(stmt)).scalars().first()
    if result:
        type_id = result
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Package type {package.type_name.lower()} is not found'
        )
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


@router.get('/package_types',
            response_model=list[PackageType],
            description='This method returns package types and their ids')
async def get_package_types(db: AsyncSession = Depends(get_db)) -> list[PackageType]:
    """
        Retrieves all package types.

        Returns a list of all package types with their identifiers.

        Args:
            db (AsyncSession): Database session dependency

        Returns:
            list[PackageType]: List of package types containing:
                - id: int - Type identifier
                - type_name: str - Type name
     """
    logger.info('Retrieving package types')
    stmt = select(PackageTypeTable)
    result = await db.execute(stmt)
    package_type_list = result.scalars().all()
    return package_type_list


@router.get('/packages',
            response_model=Page[PackageInfo],
            description='This method returns all user packages')
async def get_package_info_by_session_id(
        type_name: str | None = Query(
            None,
            description='Filter by package type name'),
        has_delivery_cost: bool | None = Query(None,
                                               description='Filter by delivery cost calculation availability'),
        db: AsyncSession = Depends(get_db),
        session_id: str = Depends(get_session_id),
        params: Params = Depends()) -> Page[PackageInfo]:
    """
        Retrieves a paginated package list for the current session with filters.

        Args:
            type_name (str | None): Optional type name filter
            has_delivery_cost (bool | None): Filter for delivery cost status:
                - True: Only packages with calculated cost
                - False: Only packages without calculated cost
                - None: All packages (default)
            db (AsyncSession): Database session dependency
            session_id (str): Authenticated session identifier

        Returns:
            Page[PackageInfo]: Paginated result containing:
                - items: list[PackageInfo] - Package data
                - total: int - Total matching packages
                - page: int - Current page number
                - size: int - Items per page
    """
    logger.info(f'Getting packages for session id: {session_id}')

    stmt = select(PackageTable.id, PackageTable.name, PackageTable.weight, PackageTable.type_id,
                  PackageTypeTable.type_name, PackageTable.content_value_usd,
                  case((PackageTable.delivery_cost.is_(None), literal_column('\'Не рассчитано\'')),
                       else_=cast(PackageTable.delivery_cost, String)).label(
                      'delivery_cost')).join(
        PackageTypeTable, PackageTable.type_id == PackageTypeTable.id).where(PackageTable.session_id == session_id)
    if type_name is not None:
        stmt = stmt.where(PackageTypeTable.type_name == type_name)
    if has_delivery_cost is not None:
        if has_delivery_cost:
            stmt = stmt.where(PackageTable.delivery_cost.is_not(None))
        else:
            stmt = stmt.where(PackageTable.delivery_cost.is_(None))
    stmt = stmt.order_by(PackageTable.id)
    return await apaginate(db, stmt, params)


@router.get('/package/{package_id}',
            response_model=PackageInfoNoId | dict[str, str],
            description='This method returns package info by id')
async def get_package_info_by_id(package_id: int = Path(...),
                                 db: AsyncSession = Depends(get_db)) -> PackageInfoNoId | dict[str, str]:
    """
        Retrieves package details by package ID.

        Returns full package information.

        Args:
            package_id (int): Package identifier
            db (AsyncSession): Database session dependency

        Returns:
            PackageInfoNoId | dict: Either package details object or the JSON with the message 'No package for id <id>'
    """
    logger.info(f'Getting package by package id: {package_id}')
    stmt = select(PackageTable.name, PackageTable.weight, PackageTypeTable.type_name,
                  PackageTable.content_value_usd,
                  PackageTable.delivery_cost).join(PackageTypeTable,
                                                   PackageTable.type_id == PackageTypeTable.id).where(
        PackageTable.id == package_id)
    result = (await db.execute(stmt)).first()
    if result:
        package = list(result)
        if package[-1] is None:
            package[-1] = 'Не рассчитано'
        return PackageInfoNoId(name=package[0],
                               weight=package[1],
                               type_name=package[2],
                               content_value_usd=package[3],
                               delivery_cost=package[4])
    else:
        return {'message': f'No package for id {package_id}'}


@router.post('/package/{package_id}/{shipping_company_id}',
             response_model=dict[str, str] | None,
             description='This method tries to assign shipping company id to the registered package')
async def assign_shipping_company_id(package_id: int = Path(...),
                                     shipping_company_id: int = Path(...),
                                     db: AsyncSession = Depends(get_db)) -> dict[str, str] | None:
    """
    Assigns a shipping company ID to a registered package.

    This endpoint assigns a specified shipping company to a package identified by its ID.
    It performs validation to ensure that the shipping company ID is a positive integer,
    the package exists, and it hasn't already been assigned to a different company.

    Parameters:
    - package_id (int): ID of the package to update.
    - shipping_company_id (int): ID of the shipping company to assign.
    - db (AsyncSession): SQLAlchemy asynchronous session dependency.

    Returns:
    - dict[str, str] | None: A message indicating the assignment was successful, or
      raises an HTTPException in case of validation or conflict errors.

    Raises:
    - HTTPException 400: If the shipping company ID is not a positive integer.
    - HTTPException 404: If the package is not found.
    - HTTPException 409: If the package has already been assigned a shipping company.
    """
    logger.info(f'Trying to assign the shipping company id {shipping_company_id}'
                f' to the registered package with id {package_id}')
    if shipping_company_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Shipping company ID must be a positive integer'
        )
    async with db.begin():
        stmt = (
            select(PackageTable)
            .where(PackageTable.id == package_id)
            .with_for_update()
        )
        package = (await db.execute(stmt)).scalar_one_or_none()

        if not package:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Package not found'
            )

        if package.shipping_company_id is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail='Package already assigned to another company'
            )

        # Обновляем значение
        package.shipping_company_id = shipping_company_id
        await db.commit()
    return {'message': 'Package successfully assigned to the shipping company'}
