import os
from dotenv import load_dotenv

load_dotenv()

host = '127.0.0.1'
user = 'postgres'
password = 'postgres'
dbname = 'test'
API_TOKEN = os.getenv("BOT_TOKEN")