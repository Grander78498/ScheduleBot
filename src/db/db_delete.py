from .database import database_func

@database_func
def delete_queue(cursor, queue_id: int):
    '''
    Удаление очереди целиком

    queue_id - id очереди в бд
    '''
    cursor.execute("""SELECT group_id, queue_message_id FROM queue WHERE id = %s;""", (queue_id,))
    queue_info = cursor.fetchone()
    cursor.execute("""DELETE FROM queue WHERE id = %s;""", (queue_id,))

    return queue_info



@database_func
def delete_queue_member(cursor, queue_id: int, tg_id: int):
    '''
    Удаление одного участника из группы

    queue_id - id очереди из бд
    tg_id - id удаляемого пользователя
    '''
    cursor.execute("""SELECT group_id, queue_message_id FROM queue WHERE id = %s;""", (queue_id,))
    queue_info = cursor.fetchone()
    cursor.execute("""DELETE FROM queue_member WHERE queue_id = %s AND user_id = %s""", (queue_id, tg_id))

    return queue_info


@database_func
def drop_tables(cursor):
    '''
    Удалить таблицы - служебная функция, ПРОСТО ТАК НЕ ИСПОЛЬЗОВАТЬ!!!
    '''

    cursor.execute('''DROP TABLE IF EXISTS admin;
                      DROP TABLE IF EXISTS queue_member;
                      DROP TABLE IF EXISTS queue;
                      DROP TABLE IF EXISTS users;
                      DROP TABLE IF EXISTS groups;''')
    
    return None