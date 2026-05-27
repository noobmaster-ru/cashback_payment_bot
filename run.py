import asyncio
import logging
import redis.asyncio as asyncredis

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage, DefaultKeyBuilder

from src.handlers.payment import router as text_router

from src.infrastructure.superbanking import Superbanking
from src.core.config import settings

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/bot.log", encoding="utf-8"),  # сохраняем в файл
        logging.StreamHandler(),  # выводим в консоль
    ],
)

logger = logging.getLogger(__name__)

async def wait_for_redis(redis_client, attempts: int = 10, delay: float = 1.0) -> None:
    for attempt in range(1, attempts + 1):
        try:
            await redis_client.ping()
            logger.info("Redis connection established")
            return
        except Exception as err:
            if attempt == attempts:
                raise RuntimeError("Redis is unavailable") from err
            logger.warning(
                "Redis is unavailable, retrying %s/%s: %s",
                attempt,
                attempts,
                err,
            )
            await asyncio.sleep(delay)

async def main():
    # Один Redis-клиент, одна DB (например /0)
    redis_client = await asyncredis.from_url(settings.REDIS_URL)
    await wait_for_redis(redis_client)
    
    superbanking = Superbanking()
    superbanking.create_banks_ids()

    storage = RedisStorage(
        redis=redis_client,
        key_builder=DefaultKeyBuilder(
            with_bot_id=True,  # чтобы ключи еще и по боту разделялись
        ),
    ) 
    # ============ START =============
    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher(storage=storage)



    # добавляем глобальные данные - чтобы все хэндлеры видели их
    dp.workflow_data.update(
        {
            "superbanking": superbanking,
            "redis_client": redis_client,
        }
    )
    # clients routers
    dp.include_routers(text_router) 
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
