from . import *

def create_tables():
    try:
        connection = psycopg2.connect(host=host,
                                      user=user,
                                      password=password,
                                      database=dbname)
        
        with connection.cursor() as cursor:
            print('Users created')
            cursor.execute('''CREATE TABLE users
                           (user_id SERIAL PRIMARY KEY,
                           name VARCHAR (50) NOT NULL);''')
    except Exception as _ex:
        print(f'We are fucked: {_ex}')
    finally:
        if connection:
            connection.commit()
            connection.close()


if __name__ == '__main__':
    create_tables()