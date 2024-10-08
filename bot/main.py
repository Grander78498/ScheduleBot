import asyncio
import logging
from aiogram import Dispatcher

from .bot import bot


from django.conf import settings

from .handlers import router as handler_router
from .text_handling import router as echo_router
from .student_game import router as student_router


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


dp = Dispatcher()
dp.include_router(handler_router)
dp.include_router(student_router)
dp.include_router(echo_router)


async def main():
    logging.basicConfig(level=logging.INFO)
    logger.info(f"DEBUG = {settings.DEBUG}")
    await dp.start_polling(bot, allowed_updates=["message", "callback_query", "chat_member", "my_chat_member"])


if __name__ == "__main__":
    asyncio.run(main())