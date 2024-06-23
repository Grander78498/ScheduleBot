import psycopg2
from .config import *
from psycopg2.extensions import adapt, register_adapter, AsIs


class User:
    def __init__(self, tg_id, full_name):
        self.tg_id = tg_id
        self.full_name = full_name

    def __str__(self):
        return f'{self.tg_id} - {self.full_name}'


def adapt_user(user: User):
    attributes = user.__dict__.keys()
    for attr in attributes:
        setattr(user, attr, adapt(getattr(user, attr)))
    return AsIs((", ".join("{}" for _ in attributes)).format(*[getattr(user, attr) for attr in attributes]))


register_adapter(User, adapt_user)


def main():
    try:
        connection = psycopg2.connect(host=host,
                                    user=user,
                                    password=password,
                                    database=dbname)
        connection.autocommit = True
        
        with connection.cursor() as cursor:
            cursor.execute("CREATE TABLE IF NOT EXISTS users (tg_id BIGINT, full_name VARCHAR(128));")
            cursor.execute("INSERT INTO users (tg_id, full_name) VALUES (%s)", (User(163713, 'fisuda'),))
            cursor.execute("SELECT * FROM users")
            result = cursor.fetchone()
            users = User(*result)
            print(users)

    except Exception as _ex:
        print(f'We are fucked: {_ex}')
    finally:
        if connection:
            connection.close()