import psycopg2
import psycopg2.errorcodes
from config import *


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
        except psycopg2.errorcodes.UNIQUE_VIOLATION as _ex:
            raise _ex
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
                    thread_id BIGINT,
                    group_name VARCHAR (128));
                   
                    CREATE TABLE IF NOT EXISTS queue
                    (id BIGSERIAL PRIMARY KEY,
                    message VARCHAR (4097),
                    date TIMESTAMPTZ NOT NULL,
                    tz INT NOT NULL,
                    creator_id BIGINT NOT NULL,
                    group_tg_id BIGINT NOT NULL);
                   
                    CREATE TABLE IF NOT EXISTS users
                    (id SERIAL PRIMARY KEY,
                    tg_id BIGINT NOT NULL,
                    full_name VARCHAR (128),
                    vote_time TIMESTAMPTZ NOT NULL,
                    queue_id BIGINT NOT NULL REFERENCES queue (id) ON DELETE CASCADE,
                    UNIQUE (tg_id, queue_id));''')
    
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
def add_admins(cursor, group_id: int, admins: list[int], group_name: str, thread_id: int):
    for admin_id in admins:
        cursor.execute("""INSERT INTO admins (tg_id, group_tg_id, group_name, thread_id) 
                       VALUES (%s, %s, %s, %s)""", (admin_id, group_id, group_name, thread_id))

    return None


@database_func
def add_queue(cursor, message: str, date: str, timezone: int, creator_id: int, group_id: int):
    '''
    Добавить очереди в бд
    Возвращает созданные напоминания
    
    message - описание напоминалки
    date - дата начала очереди
    timezone - часовой пояс по Гринвичу
    creator_id - id создателя очереди
    group_id - id группы, в которой создана очередь
    '''

    cursor.execute('INSERT INTO queue (message, date, tz, creator_id, group_tg_id) VALUES (%s, %s, %s, %s, %s);',
                    (message, date, timezone, creator_id, group_id))
    
    return None


@database_func
def get_queue_notifications(cursor):
    '''
    Получить все напоминания о начале очереди (через час), которые нужно отправить
    Используется только внутри программы
    '''
    
    cursor.execute("""SELECT queue.id, thread_id, queue.group_tg_id, message FROM queue 
                   LEFT JOIN admins ON queue.group_tg_id = admins.group_tg_id
                            WHERE NOW() - date < interval '1 HOUR' ORDER BY date;""")
    queue_notifications = cursor.fetchall()

    return [{key: value for key, value in 
                    zip(['queue_id', 'thread_id', 'group_id', 'message'], notification)}
                    for notification in queue_notifications]


@database_func
def get_queue_ready(cursor):
    '''
    Получить все очереди, которые должны сейчас запуститься
    Используется только внутри программы
    '''
    
    cursor.execute("""SELECT queue.id, creator_id, thread_id, queue.group_tg_id, message, group_name, date, tz FROM queue 
                   LEFT JOIN admins ON queue.group_tg_id = admins.group_tg_id
                            WHERE GREATEST(NOW() - date, date - NOW()) < interval '1 MINUTE' ORDER BY date;""")
    queue_notifications = cursor.fetchall()

    return [{key: value for key, value in 
                    zip(['queue_id', 'creator_id', 'thread_id', 'group_id', 'message', 'group_name', 'date', 'timezone'], notification)} 
                    for notification in queue_notifications]


@database_func
def update_queue(cursor, queue_id: int):
    cursor.execute("""UPDATE queue SET is_""")
        

@database_func
def get_admin_queues(cursor, tg_id: int):
    '''
    Получить все очереди, которые есть у админа (как у создателя)

    tg_id - id пользователя tg
    '''

    cursor.execute("""SELECT message, date, tz, group_name FROM admins
                    LEFT JOIN queue ON tg_id = creator_id WHERE tg_id = %s""", (tg_id,))
    admin_queues = cursor.fetchall()

    return [{key: value for key, value in 
                     zip(['message', 'date', 'timezone', 'group_name'], queue)} 
                     for queue in admin_queues]


@database_func
def add_user_to_queue(cursor, queue_id: int, tg_id: int, full_name: str, vote_date: str):
    """
    Добавить пользователя в очередь

    queue_id - id очереди,
    tg_id - id пользователя,
    full_name - полное имя пользователя
    vote_date - дата голосования
    """

    cursor.execute("""INSERT INTO users (tg_id, full_name, vote_date, queue_id)
                   VALUES (%s, %s, %s, %s)""", (tg_id, full_name, vote_date, queue_id))
    
    return None


@database_func
def get_queue(cursor, queue_id: int):
    """
    Получение списка очереди

    queue_id - id очереди в бд
    """


    cursor.execute("""SELECT message, date, tz, creator_id, group_tg_id FROM queue WHERE id = %s""", (queue_id,))
    queue_info = cursor.fetchone()

    cursor.execute("""SELECT tg_id, full_name, vote_date FROM users WHERE queue_id = %s ORDER BY vote_date""", (queue_id))
    queue_members = cursor.fetchall()

    return ({'message': queue_info[0], 'date': queue_info[1], 'creator_id': queue_info[2], 'group_id': queue_info[3]}), \
            [{key: value for key, value in
             zip(['tg_id', 'full_name', 'vote_date'], queue_member)}
             for queue_member in queue_members]


@database_func
def delete_queue(cursor, queue_id: int):
    '''
    Удаление очереди целиком

    queue_id - id очереди в бд
    '''


    cursor.execute("""DELETE FROM queue WHERE id = %s""", (queue_id,))

    return None


@database_func
def delete_queue_member(cursor, queue_id: int, tg_id: int):
    '''
    Удаление одного участника из группы

    queue_id - id очереди из бд
    tg_id - id удаляемого пользователя
    '''


    cursor.execute("""DELETE FROM users WHERE queue_id = %s AND tg_id = %s""", (queue_id, tg_id))

    return None


@database_func
def get_admins(cursor, group_id: int):
    '''
    Получение админов группы
    '''

    cursor.execute("SELECT tg_id, group_name FROM admins WHERE group_tg_id = %s", (group_id,))
    admins = cursor.fetchall()
    return [{key: value for key, value in 
                     zip(['tg_id', 'group_name'], admin)} 
                     for admin in admins] 


@database_func
def get_admin_groups(cursor, tg_id: int):
    '''
    Получение групп у админа
    '''
    
    cursor.execute("SELECT group_tg_id, group_name FROM admins WHERE tg_id = %s", (tg_id,))
    admin_groups = cursor.fetchall()

    return [{key: value for key, value in 
                     zip(['group_tg_id', 'group_name'], group)} 
                     for group in admin_groups]
