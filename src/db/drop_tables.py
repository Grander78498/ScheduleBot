from . import *

def drop_tables():
    try:
        connection = psycopg2.connect(host=host,
                                      user=user,
                                      password=password,
                                      database=dbname)
        
        with connection.cursor() as cursor:
            cursor.execute('DROP TABLE IF EXISTS users;')
    except Exception as _ex:
        print(f'We are fucked: {_ex}')
    finally:
        if connection:
            connection.commit()
            connection.close()


if __name__ == '__main__':
    drop_tables()