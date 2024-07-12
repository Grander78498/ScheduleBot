import os
from dotenv import load_dotenv

load_dotenv()

HOST = '127.0.0.1'
PORT = '5432'
USER = 'postgres'
PASSWORD = 'postgres'
DBNAME = 'queue_db'
API_TOKEN = os.getenv("BOT_TOKEN")