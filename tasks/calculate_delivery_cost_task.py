import logging
from datetime import datetime

import asyncio
from redis.asyncio import Redis
from sqlalchemy import select, update

from db.packages import PackageTable
from redis_db.redis_setup import get_redis_client
from utils.session import AsyncSessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Calculates delivery cost
def calculate_delivery_cost(weight: float, content_value_usd: float, usd_rate: float | None) -> float | None:
    """
        Calculates delivery cost in roubles.

        Args:
            weight (float): The package weight in kilograms
            content_value_usd (float): THe declared value of package contents in USD
            usd_rate (float | None): The current USD exchange rate

        Returns:
            float | None:
                - The calculated cost in RUB if rate available
                - None if the USD rate is missing
    """
    if not usd_rate:
        logger.warning('No USD rate available for calculating the delivery cost')
        return None
    else:
        delivery_cost_rub = (weight * 0.5 + content_value_usd * 0.01) * usd_rate
        delivery_cost_rub = round(delivery_cost_rub, 2)

    logger.info(f'The calculated delivery cost: {delivery_cost_rub} RUB (rate: {usd_rate})')
    return delivery_cost_rub


async def get_usd_rate(redis_client: Redis) -> float | None:
    """
        Retrieves the USD exchange rate.

        Args:
            redis_client (Redis): Async Redis client instance

        Returns:
            float | None:
                - The USD rate if available
                - None if no rates in Redis
    """
    try:
        # USD rate from redis

        today = datetime.utcnow().strftime('%Y-%m-%d')
        cache_key = f'usd_rate:{today}'

        # Trying to get the current USD rate
        usd_rate = await redis_client.get(cache_key)

        if not usd_rate:
            # If there is no rate for today, then trying to find the last available rate
            keys = await redis_client.keys('usd_rate:*')
            if keys:
                sorted_keys = sorted(keys, reverse=True)
                for key in sorted_keys:
                    usd_rate = await redis_client.get(key)
                    if usd_rate:
                        break

        if not usd_rate:
            logger.warning('No USD rate available for calculating the delivery cost')
            return None

        usd_rate = float(usd_rate)

        return usd_rate

    except Exception as ex:
        logger.error(f'The delivery calculation error: {str(ex)}')
        return None


# Delivery cost calculation task and renewing the delivery_cost field in the package table
async def calculate_delivery_cost_task():
    """
        The background task for periodic delivery cost calculations.
    """
    logger.info('Starting calculating the delivery cost task')
    r = await get_redis_client()
    while True:
        try:
            usd_rate = await get_usd_rate(r)
            async with AsyncSessionLocal() as db:
                stmt = select(PackageTable)
                packages = (await db.execute(stmt)).all()

                for package in packages:
                    delivery_cost = calculate_delivery_cost(package[0].weight, package[0].content_value_usd, usd_rate)
                    update_stmt = update(PackageTable).where(PackageTable.id == package[0].id).values(
                        delivery_cost=delivery_cost)
                    await db.execute(update_stmt)
                    await db.commit()
            # Waiting for 5 minutes before the next calculation
            await asyncio.sleep(300)

        except asyncio.CancelledError:
            logger.info('The delivery cost task cancelled')
            raise
        except Exception as ex:
            logger.error(f'The delivery cost task error: {str(ex)}')
            # Waiting for 20 seconds before repeating
            await asyncio.sleep(20)


# One-time delivery cost calculation task and renewing the delivery_cost field in the package table
async def calculate_delivery_cost_task_one_time():
    """
        Executes single-pass delivery cost calculations for all packages.
    """
    logger.info('Starting calculating the delivery cost task')
    redis_client = await get_redis_client()
    try:
        usd_rate = await get_usd_rate(redis_client)
        async with AsyncSessionLocal() as db:
            stmt = select(PackageTable)
            packages = (await db.execute(stmt)).all()

            for package in packages:
                delivery_cost = calculate_delivery_cost(package[0].weight, package[0].content_value_usd, usd_rate)
                update_stmt = update(PackageTable).where(PackageTable.id == package[0].id).values(
                    delivery_cost=delivery_cost)
                await db.execute(update_stmt)
                await db.commit()
    except asyncio.CancelledError:
        logger.info('The delivery cost task cancelled')
        raise
    except Exception as ex:
        logger.error(f'The delivery cost task error: {str(ex)}')
