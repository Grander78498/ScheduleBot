import psycopg2
from .config import *


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
        except Exception as _ex:
            print(f'We are fucked: {_ex}')
        finally:
            if connection:
                connection.close()
                return result
    return inner


@database_func
def create_tables(cursor):
    '''
    Создать таблицы, если не существуют
    Функция будет вызываться при каждом запуске бота
    '''

    cursor.execute('''CREATE TABLE IF NOT EXISTS admins
                    (id BIGSERIAL PRIMARY KEY,
                    tg_id BIGINT NOT NULL,
                    group_tg_id BIGINT NOT NULL,
                    group_name VARCHAR (128));
                   
                    CREATE TABLE IF NOT EXISTS queue
                    (id BIGSERIAL PRIMARY KEY,
                    message VARCHAR (250),
                    date TIMESTAMPTZ NOT NULL,
                    tz INT NOT NULL,
                    creator_id BIGINT NOT NULL,
                    group_tg_id BIGINT NOT NULL);
                   
                    CREATE TABLE IF NOT EXISTS users
                    (id SERIAL PRIMARY KEY,
                    tg_id BIGINT NOT NULL,
                    full_name VARCHAR (128),
                    vote_time TIMESTAMPTZ NOT NULL,
                    queue_id BIGINT NOT NULL REFERENCES queue (id) ON DELETE CASCADE);''')
    
    return None


@database_func
def drop_tables(cursor):
    '''
    Удалить таблицы - служебная функция, ПРОСТО ТАК НЕ ИСПОЛЬЗОВАТЬ!!!
    '''

    cursor.execute('''DROP TABLE IF EXISTS admins;
                        DROP TABLE IF EXISTS users;
                        DROP TABLE IF EXISTS queue;''')
    
    return None


@database_func
def add_admins(cursor, group_id: int, admins: list[int], group_name: str):
    for admin_id in admins:
        cursor.execute("""INSERT INTO admins (tg_id, group_id, group_name) VALUES (%s, %s, %s)""", (admin_id, group_id, group_name))

    return None


@database_func
def add_queue(cursor, message: str, date: list[str], timezone: int, creator_id: int, group_id: int):
    '''
    Добавить очереди в бд
    Возвращает созданные напоминания
    
    tg_id - id пользователя в тг
    message - описание напоминалки
    dates - даты напоминаний
    '''

    cursor.execute('INSERT INTO gr_notif (message, date, tz, creator_id, group_tg_id) VALUES (%s, %s, %s, %s, %s);',
                    (message, date, timezone, creator_id, group_id))
    
    return None


@database_func
def get_queue_notifications(cursor):
    '''
    Получить все напоминания, которые нужно отправить сейчас
    Используется только внутри программы для проверки, какие напоминалки нужно отправить
    '''
    
    cursor.execute("""SELECT group_tg_id, message, date, tz FROM queue
                            WHERE NOW() - date < interval '1 HOUR' ORDER BY date;""")
    queue_notifications = cursor.fetchall()

    return [{key: value for key, value in 
                    zip(['group_id', 'message', 'date', 'timezone'], notification)} 
                    for notification in queue_notifications]
        

@database_func
def get_admin_queues(cursor, tg_id: int):
    '''
    Получить все напоминания, которые есть у пользователя
    Возвращает АБСОЛЮТНО всю информацию о напоминаниях, включая id в бд - это очень важно, т.к. по этому же id возможно удаление, поэтому id никуда не девать!

    tg_id - id пользователя tg
    '''

    cursor.execute("""SELECT tg_id, message, date, tz, admins.group_tg_id, group_name FROM admins
                    LEFT JOIN queue ON admins.group_tg_id = queue.group_tg_id WHERE tg_id = %s""", (tg_id,))
    admin_queues = cursor.fetchall()

    return [{key: value for key, value in 
                     zip(['tg_id', 'message', 'date', 'timezone', 'group_id', 'group_name'], queue)} 
                     for queue in admin_queues]
        

@database_func
def delete_one_notification(cursor, id: int):
    '''
    Удаление конкретной напоминалки

    id - id в БД!
    '''

    cursor.execute('DELETE FROM notif WHERE id = %s;', (id,))

    return None


@database_func
def delete_group_notifications(cursor, id: int):
    '''
    Удаление группы напоминалок

    id - id в БД!
    '''

    cursor.execute('DELETE FROM gr_notif WHERE id = %s;', (id,))

    return None


@database_func
def get_admins(cursor, group_id: int):
    '''
    Получение админов группы
    '''

    cursor.execute("SELECT tg_id, group_name FROM admins WHERE group_tg_id = %s", (group_id,))
    admins = cursor.fetchall()
    return admins
