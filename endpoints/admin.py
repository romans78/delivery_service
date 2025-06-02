import logging
from fastapi import APIRouter
from tasks.calculate_delivery_cost_task import calculate_delivery_cost_task_one_time
from tasks.usd_rate_task import usd_rate_task_one_time


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix='/api/v1', tags=['admin'])

@router.post('/tasks/refresh_usd_rate')
async def manual_refresh_usd_rate():
    logger.info("Manual refresh USD rate")
    try:
        return await usd_rate_task_one_time()
    except Exception as e:
        logger.error(f'Manual USD rate refresh failed: {str(e)}')
        raise

@router.post('/tasks/calculate_delivery_cost')
async def calculate_delivery_cost():
    logger.info("Manual calculation of delivery cost")
    try:
        return await calculate_delivery_cost_task_one_time()
    except Exception as e:
        logger.error(f'Manual calculation of delivery cost failed: {str(e)}')
        raise