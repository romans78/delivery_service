import logging

from fastapi import APIRouter

from tasks.calculate_delivery_cost_task import calculate_delivery_cost_task_one_time
from tasks.usd_rate_task import usd_rate_task_one_time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix='/api/v1', tags=['admin'])


@router.post('/tasks/refresh_usd_rate', description='This method manually refreshes USD rate')
async def manual_refresh_usd_rate():
    """
        Manually triggers an immediate refresh of the USD exchange rate.

        This endpoint forces an update of the USD conversion rate by executing
        the same routine used in scheduled tasks.

        Raises:
            HTTPException: 500 error if any exception occurs during processing
    """
    logger.info('Manual refresh USD rate')
    try:
        return await usd_rate_task_one_time()
    except Exception as e:
        logger.error(f'Manual USD rate refresh failed: {str(e)}')
        raise


@router.post('/tasks/calculate_delivery_cost', description='This method manually calculates delivery cost')
async def calculate_delivery_cost():
    """
        Manually triggers delivery cost calculation.

        Executes an on-demand run of the delivery cost calculation.

        Raises:
            HTTPException: 500 error if critical failure occurs in processing
    """
    logger.info('Manual calculation of delivery cost')
    try:
        return await calculate_delivery_cost_task_one_time()
    except Exception as e:
        logger.error(f'Manual calculation of delivery cost failed: {str(e)}')
        raise
