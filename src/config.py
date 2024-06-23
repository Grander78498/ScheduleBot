import os
from dotenv import load_dotenv

load_dotenv()

host = '127.0.0.1'
user = 'postgres'
password = 'postgres'
dbname = 'queue_db'
API_TOKEN = os.getenv("BOT_TOKEN")