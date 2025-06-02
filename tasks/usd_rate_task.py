import logging

import asyncio
import httpx
from datetime import datetime, timedelta
from redis_db.redis_setup import get_redis_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# функция для получения и сохранения в redis курса доллара
async def fetch_and_store_rate():
    logger.info("Fetching USD/RUB rate from CBR...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.cbr-xml-daily.ru/daily_json.js",
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            usd_rate = data["Valute"]["USD"]["Value"]

            r = await get_redis_client()
            today = datetime.utcnow().strftime("%Y-%m-%d")
            cache_key = f"usd_rate:{today}"

            try:
                # сохраняем на двое суток, на случай выходных
                await r.setex(cache_key, 48 * 3600, usd_rate)
                logger.info(f"USD rate updated: {usd_rate}")
            except ConnectionError:
                logger.error("Redis connection error during set")
            except Exception as e:
                logger.error(f"Failed to save rate to Redis: {str(e)}")

            return usd_rate
    except httpx.HTTPError as e:
        logger.error(f"HTTP error: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to fetch USD rate: {str(e)}")
    return None

# задача для периодического обновления курса
async def usd_rate_task():
    logger.info("Starting rate update task")

    await fetch_and_store_rate()

    while True:
        try:
            # время до следующего обновления (12:00 по Москве)
            now = datetime.utcnow()
            next_run = (now + timedelta(days=1)).replace(
                hour=9, minute=0, second=0, microsecond=0  #UTC 9:00
            )

            # если уже прошло 12:00, устанавливаем следующий run
            if now > next_run:
                next_run += timedelta(days=1)

            sleep_seconds = (next_run - now).total_seconds()
            logger.info(f"Next rate update in {sleep_seconds:.0f} seconds at {next_run} UTC")

            # спим до следующего обновления
            await asyncio.sleep(sleep_seconds)

            # проверяем, если будний день
            if next_run.weekday() < 5:
                await fetch_and_store_rate()
            else:
                logger.info("Skipping update on weekend")
        except asyncio.CancelledError:
            logger.error("USD rate update task cancelled")
            raise
        except Exception as e:
            logger.error(f"Scheduler error: {str(e)}")
            await asyncio.sleep(60)

# задача для обновления курса один раз
async def usd_rate_task_one_time():
    logger.info("Starting rate update task")
    await fetch_and_store_rate()
    try:
        await fetch_and_store_rate()
    except asyncio.CancelledError:
        logger.error("USD rate update task cancelled")
        raise
    except Exception as e:
        logger.error(f"Scheduler error: {str(e)}")
        await asyncio.sleep(60)
