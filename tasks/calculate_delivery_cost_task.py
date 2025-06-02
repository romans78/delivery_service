from redis.asyncio import Redis
from datetime import datetime
import logging
import asyncio
from sqlalchemy import select, update
from db.packages import PackageTable
from redis_db.redis_setup import get_redis_client
from utils.session import AsyncSessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# рассчитывает стоимость доставки
def calculate_delivery_cost(weight: float, content_value_usd: float, usd_rate: float | None) -> float | None:

    if not usd_rate:
        logger.warning("No USD rate available for calculating delivery cost")
        return None
    else:
        delivery_cost_rub = (weight * 0.5 + content_value_usd * 0.01) * usd_rate
        delivery_cost_rub = round(delivery_cost_rub, 2)

    logger.info(f"Calculated delivery cost: {delivery_cost_rub} RUB (rate: {usd_rate})")
    return delivery_cost_rub


async def get_usd_rate(r: Redis) -> float | None:
    try:
        # курс из redis

        today = datetime.utcnow().strftime("%Y-%m-%d")
        cache_key = f"usd_rate:{today}"

        # пробуем получить текущий курс
        usd_rate = await r.get(cache_key)

        if not usd_rate:
            # если нет курса за сегодня, ищем последний доступный
            keys = await r.keys("usd_rate:*")
            if keys:
                sorted_keys = sorted(keys, reverse=True)
                for key in sorted_keys:
                    usd_rate = await r.get(key)
                    if usd_rate:
                        break

        if not usd_rate:
            logger.warning("No USD rate available for calculating delivery cost")
            return None

        usd_rate = float(usd_rate)

        return usd_rate

    except Exception as e:
        logger.error(f"Delivery calculation error: {str(e)}")
        return None


# задача расчета стоимости доставки и обновления поля delivery_cost в таблице package
async def calculate_delivery_cost_task():
    logger.info("Starting calculating delivery cost task")
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
            # ждем 5 минут перед следующим расчетом
            await asyncio.sleep(300)

        except asyncio.CancelledError:
            logger.info("Delivery cost task cancelled")
            raise
        except Exception as e:
            logger.error(f"Delivery cost task error: {str(e)}")
            # ждем 20 секунд перед повторной попыткой
            await asyncio.sleep(20)


# задача расчета стоимости доставки и обновления поля delivery_cost в таблице package один раз
async def calculate_delivery_cost_task_one_time():
    logger.info("Starting calculating delivery cost task")
    r = await get_redis_client()

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


    except asyncio.CancelledError:
        logger.info("Delivery cost task cancelled")
        raise
    except Exception as e:
        logger.error(f"Delivery cost task error: {str(e)}")

