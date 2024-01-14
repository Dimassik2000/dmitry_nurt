import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode

import config
from handlers import start
from aiogram.fsm.storage.memory import MemoryStorage
from db import Database
db = Database()
async def main() -> None:
    dp = Dispatcher(storage=MemoryStorage())
    bot = Bot(token=config.BOT_TOKEN, parse_mode=ParseMode.HTML)
    dp.include_router(start.router)
    #db = Database()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())






