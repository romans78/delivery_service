import logging
from datetime import datetime, timedelta

import asyncio
import httpx

from redis_db.redis_setup import get_redis_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Fetches the USD rate and stores it into redis
async def fetch_and_store_rate():
    """
        Fetches the USD exchange rate and stores it in Redis.

        Returns:
            float | None:
                - The USD rate on success
                - None on failure
    """
    logger.info('Fetching USD/RUB rate from CBR...')
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                'https://www.cbr-xml-daily.ru/daily_json.js',
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            usd_rate = data['Valute']['USD']['Value']

            r = await get_redis_client()
            today = datetime.utcnow().strftime('%Y-%m-%d')
            cache_key = f'usd_rate:{today}'

            try:
                # Saving for two days in case of weekend
                await r.setex(cache_key, 48 * 3600, usd_rate)
                logger.info(f'USD rate updated: {usd_rate}')
            except ConnectionError:
                logger.error('Redis connection error during set')
            except Exception as ex:
                logger.error(f'Failed to save rate to Redis: {str(ex)}')

            return usd_rate
    except httpx.HTTPError as ex:
        logger.error(f'HTTP error: {str(ex)}')
    except Exception as ex:
        logger.error(f'Failed to fetch USD rate: {str(ex)}')
    return None


# Task for periodic the USD exchange rate updates
async def usd_rate_task():
    """
        The background task for the USD rate updates.
    """
    logger.info('Starting rate update task')

    await fetch_and_store_rate()

    while True:
        try:
            # Time till the next update (12:00 Moscow timezone)
            now = datetime.utcnow()
            next_run = (now + timedelta(days=1)).replace(
                hour=9, minute=0, second=0, microsecond=0  # UTC 9:00
            )

            # If it is already after 12:00, then the next run is set
            if now > next_run:
                next_run += timedelta(days=1)

            sleep_seconds = (next_run - now).total_seconds()
            logger.info(f"Next rate update in {sleep_seconds:.0f} seconds at {next_run} UTC")

            # Sleeps till the next update
            await asyncio.sleep(sleep_seconds)

            # Checks if the working day
            if next_run.weekday() < 5:
                await fetch_and_store_rate()
            else:
                logger.info("Skipping update on weekend")
        except asyncio.CancelledError:
            logger.error("USD rate update task cancelled")
            raise
        except Exception as ex:
            logger.error(f"Scheduler error: {str(ex)}")
            await asyncio.sleep(60)


# Executes the USD exchange rate update by request
async def usd_rate_task_one_time():
    """
        Executes a single USD rate update request.
    """
    logger.info("Starting the rate update task")
    try:
        await fetch_and_store_rate()
    except asyncio.CancelledError:
        logger.error("The USD rate update task cancelled")
        raise
    except Exception as ex:
        logger.error(f"Scheduler error: {str(ex)}")
        await asyncio.sleep(60)
