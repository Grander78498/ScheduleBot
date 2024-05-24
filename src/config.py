import os

host = os.getenv('host') if os.getenv('host') is not None else '127.0.0.1'
user = 'postgres'
password = 'postgres'
dbname = 'test'