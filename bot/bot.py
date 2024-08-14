from aiogram import Bot
from config import config

bot = Bot(token=config.bot_token.get_secret_value())
