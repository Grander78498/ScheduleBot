from . import *

def create_tables():
    try:
        connection = psycopg2.connect(host=host,
                                      user=user,
                                      password=password,
                                      database=dbname)
        
        with connection.cursor() as cursor:
            print('Users created')
            cursor.execute('''CREATE TABLE IF NOT EXISTS notifications 
                                (id BIGSERIAL PRIMARY KEY,
                                tg_id BIGINT NOT NULL,
                                message VARCHAR (250),
                                date TIMESTAMP NOT NULL
                                );''')
    except Exception as _ex:
        print(f'We are fucked: {_ex}')
    finally:
        if connection:
            connection.commit()
            connection.close()


if __name__ == '__main__':
    create_tables()