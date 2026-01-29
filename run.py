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

async def main():
    # Один Redis-клиент, одна DB (например /0)
    redis_client = await asyncredis.from_url(settings.REDIS_URL)
    
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
            "superbanking": superbanking
        }
    )
    # clients routers
    dp.include_routers(text_router) 
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())