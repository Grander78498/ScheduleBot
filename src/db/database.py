from . import *


def insert_user(name: str):
    try:
        connection = psycopg2.connect(host=host,
                                      user=user,
                                      password=password,
                                      database=dbname)
        
        with connection.cursor() as cursor:
            cursor.execute('INSERT INTO users (name) VALUES (%s);', (name,))

    except Exception as _ex:
        print(f'We are fucked: {_ex}')
    finally:
        if connection:
            connection.commit()
            connection.close()


def test_db():
    try:
        connection = psycopg2.connect(host=host,
                                      user=user,
                                      password=password,
                                      database=dbname)
        
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM users;')
            all_users = cursor.fetchall()
        print(all_users)
    except Exception as _ex:
        print(f'We are fucked: {_ex}')
    finally:
        if connection:
            connection.commit()
            connection.close()