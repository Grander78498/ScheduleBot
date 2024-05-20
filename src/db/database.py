from . import *
import datetime


def insert_user(tg_id: int, message: str, date: datetime):
    '''
    Добавить напоминалку в бд
    
    tg_id - id пользователя в тг
    message - описание напоминалки
    date - дата напоминания
    '''
    try:
        connection = psycopg2.connect(host=host,
                                      user=user,
                                      password=password,
                                      database=dbname)
        
        with connection.cursor() as cursor:
            cursor.execute('INSERT INTO notifications (tg_id, message, date) VALUES (%s);', (tg_id, message, date))

    except Exception as _ex:
        print(f'We are fucked: {_ex}')
    finally:
        if connection:
            connection.commit()
            connection.close()


def get_all_notifications():
    '''
    Получить все напоминания
    Используется только внутри программы для проверки, какие напоминалки нужно отправить
    '''
    try:
        connection = psycopg2.connect(host=host,
                                      user=user,
                                      password=password,
                                      database=dbname)
        
        with connection.cursor() as cursor:
            cursor.execute('SELECT date, message, tg_id FROM notifications ORDER BY date;')
            all_notifications = cursor.fetchall()

    except Exception as _ex:
        print(f'We are fucked: {_ex}')
    finally:
        if connection:
            connection.commit()
            connection.close()
            return all_notifications
        

def get_user_notifications(tg_id: int):
    '''
    Получить все напоминания, которые есть у пользователя
    Возвращает АБСОЛЮТНО всю информацию о напоминаниях, включая id в бд - это очень важно, т.к. по этому же id возможно удаление, поэтому id никуда не девать!

    tg_id - id пользователя tg
    '''
    try:
        connection = psycopg2.connect(host=host,
                                      user=user,
                                      password=password,
                                      database=dbname)
        
        with connection.cursor() as cursor:
            cursor.execute('SELECT id, date, message FROM notifications ORDER BY date WHERE tg_id = %s;', (tg_id,))
            user_notifications = cursor.fetchall()

    except Exception as _ex:
        print(f'We are fucked: {_ex}')
    finally:
        if connection:
            connection.commit()
            connection.close()
            return user_notifications
        

def delete_one_notification(id: int):
    '''
    Удаление конкретной напоминалки

    id - id в БД!
    '''
    try:
        connection = psycopg2.connect(host=host,
                                      user=user,
                                      password=password,
                                      database=dbname)
        
        with connection.cursor() as cursor:
            cursor.execute('DELETE FROM notifications WHERE id = %s;', (id,))

    except Exception as _ex:
        print(f'We are fucked: {_ex}')
    finally:
        if connection:
            connection.commit()
            connection.close()


def delete_user_notifications(tg_id: int):
    '''
    Удаление всех напоминалок у пользователя 

    id - id в БД!
    '''
    try:
        connection = psycopg2.connect(host=host,
                                      user=user,
                                      password=password,
                                      database=dbname)
        
        with connection.cursor() as cursor:
            cursor.execute('DELETE FROM notifications WHERE id = %s;', (id,))

    except Exception as _ex:
        print(f'We are fucked: {_ex}')
    finally:
        if connection:
            connection.commit()
            connection.close()