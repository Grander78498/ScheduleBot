import psycopg2
import psycopg2.errorcodes
from ..config import *


def database_func(func):
    def inner(*arg):
        try:
            connection = psycopg2.connect(host=host,
                                        user=user,
                                        password=password,
                                        database=dbname)
            connection.autocommit = True
            
            with connection.cursor() as cursor:
                result = func(cursor, *arg)
        except psycopg2.errors.lookup('23505') as _ex:
            raise _ex
        except Exception as _ex:
            print(f'We are fucked: {_ex}')
        finally:
            if connection:
                connection.close()
                return result
    return inner
