from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

router = APIRouter(prefix='/api/v1', tags=['deliveries'])

@router.get('/deliveries/test')
async def test(msg: int):
    return {"message": msg}