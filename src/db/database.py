import psycopg2
from src.db.config import *

def test_db():
    try:
        connection = psycopg2.connect(host=host,
                                      user=user,
                                      password=password,
                                      database=dbname)
        
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM users')
            all_users = cursor.fetchall()
        print(all_users)
    except Exception as _ex:
        print(f'We are fucked: {_ex}')
    finally:
        if connection:
            connection.close()