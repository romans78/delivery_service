from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from models.packages import PackageCreate, PackageId

router = APIRouter(prefix='/api/v1', tags=['deliveries'])


@router.get('/deliveries/test')
async def test(msg: int):
    return {"message": msg}


@router.post('/package',
             response_model=PackageId,
             description='This method registers a package')
async def register_package(package: PackageCreate):
    return PackageId(id=str(package.content_value_usd))
