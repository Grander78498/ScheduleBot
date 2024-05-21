from . import *
import datetime


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

    cursor.execute('''CREATE TABLE IF NOT EXISTS gr_notif 
                    (id BIGSERIAL PRIMARY KEY,
                    tg_id BIGINT NOT NULL,
                    message VARCHAR (250),
                    tz INTEGER NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS notif
                    (id BIGSERIAL PRIMARY KEY,
                    group_id BIGINT NOT NULL REFERENCES gr_notif (id) ON DELETE CASCADE,
                    date TIMESTAMPTZ NOT NULL);
                    CREATE TABLE IF NOT EXISTS admin
                    (id SERIAL PRIMARY KEY,
                    group_id BIGINT NOT NULL,
                    admin_id BIGINT NOT NULL);''')
    
    return None


@database_func
def drop_tables(cursor):
    '''
    Удалить таблицы - служебная функция, ПРОСТО ТАК НЕ ИСПОЛЬЗОВАТЬ!!!
    '''

    cursor.execute('''DROP TABLE IF EXISTS notif;
                        DROP TABLE IF EXISTS gr_notif;
                        DROP TABLE IF EXISTS group;''')
    
    return None


@database_func
def insert_notifications(cursor, tg_id: int, message: str, dates: list[str], timezone: int):
    '''
    Добавить напоминалки в бд
    Возвращает созданные напоминания
    
    tg_id - id пользователя в тг
    message - описание напоминалки
    dates - даты напоминаний
    '''

    cursor.execute('INSERT INTO gr_notif (tg_id, message, tz) VALUES (%s, %s, %s) RETURNING id;', (tg_id, message, timezone))
    group_id = cursor.fetchone()
    for date in dates:
        cursor.execute('INSERT INTO notif (group_id, date) VALUES (%s, %s);', (group_id, date))
    cursor.execute('SELECT message, date, tz FROM gr_notif LEFT JOIN notif ON gr_notif.id = group_id WHERE tg_id = %s ORDER BY date;', (tg_id,))
    info = cursor.fetchall()

    return [{key: value for key, value in 
                     zip(['message', 'date', 'timezone'], notification)} 
                     for notification in info]


@database_func
def get_all_notifications(cursor):
    '''
    Получить все напоминания, которые нужно отправить сейчас
    Используется только внутри программы для проверки, какие напоминалки нужно отправить
    '''
    
    cursor.execute("""SELECT tg_id, message, date, tz FROM gr_notif LEFT JOIN notif ON gr_notif.id = group_id
                            WHERE GREATEST(NOW() - date, date - NOW()) < interval '1 MINUTE' ORDER BY date;""")
    all_notifications = cursor.fetchall()

    return [{key: value for key, value in 
                    zip(['tg_id', 'message', 'date', 'timezone'], notification)} 
                     for notification in all_notifications]
        

@database_func
def get_user_notifications(cursor, tg_id: int):
    '''
    Получить все напоминания, которые есть у пользователя
    Возвращает АБСОЛЮТНО всю информацию о напоминаниях, включая id в бд - это очень важно, т.к. по этому же id возможно удаление, поэтому id никуда не девать!

    tg_id - id пользователя tg
    '''

    cursor.execute("""SELECT tg_id, group_id, notif.id AS notif_id, message, tz FROM gr_notif
                            LEFT JOIN notif ON gr_notif.id = group_id WHERE tg_id = %s ORDER BY group_id, date;""", (tg_id,))
    user_notifications = cursor.fetchall()

    return [{key: value for key, value in 
                     zip(['tg_id', 'group_id', 'notif_id', 'message', 'timezone'], notification)} 
                     for notification in user_notifications]
        

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

    cursor.execute("SELECT admin_id FROM group WHERE group_id = %s", (group_id,))
    admins = cursor.fetchall()
    return admins


@database_func
def add_admins(cursor, group_id: int, admins: list[int]):
    '''
    Добавление админов в бд
    '''
    
    for admin in admins:
        cursor.execute('INSERT INTO group (group_id, admin_id) VALUES (%s, %s)', (group_id, admin))
    
    return None
