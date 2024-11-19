from aiogram import Bot
from pathlib import Path
import os
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env', override=True)
bot = Bot(token=os.environ.get('BOT_TOKEN'))
