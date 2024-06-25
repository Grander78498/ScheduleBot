from .database import database_func


@database_func
def get_queue(cursor, queue_id: int):
    """
    Получение списка очереди

    queue_id - id очереди в бд
    """


    cursor.execute("""SELECT message, creator_id, queue.group_id, queue_message_id FROM queue
                      WHERE queue.id = %s""", (queue_id,))
    queue_info = cursor.fetchone()

    cursor.execute("""SELECT user_id, full_name, vote_time FROM queue_member
                      JOIN users ON users.id = user_id
                      WHERE queue.id = %s ORDER BY vote_time;""", (queue_id,))
    queue_members = cursor.fetchall()

    return ({'message': queue_info[0], 'creator_id': queue_info[1],
              'group_id': queue_info[2], 'queue_message_id': queue_info[3]}), \
            [{key: value for key, value in
             zip(['tg_id', 'full_name', 'vote_date'], queue_member)}
             for queue_member in queue_members]


@database_func
def get_admin_queues(cursor, tg_id: int):
    '''
    Получить все очереди, которые есть у админа (как у создателя)

    tg_id - id пользователя tg
    '''

    cursor.execute("""SELECT queue.id, message, date, tz, group_name FROM queue 
                     JOIN groups ON groups.id = queue.group_id
                     WHERE creator_id = %s
                     ORDER BY group_name, date""", (tg_id,))
    admin_queues = cursor.fetchall()

    queue_list = [{key: value for key, value in
                    zip(['queue_id', 'message', 'date', 'timezone', 'group_name'], queue)}
                    for queue in admin_queues]

    return queue_list


@database_func
def get_queue_notifications(cursor):
    '''
    Получить все напоминания о начале очереди (через час), которые нужно отправить
    Используется только внутри программы
    '''
    
    cursor.execute("""SELECT queue.id, queue.group_id, message, thread_id FROM queue 
                        JOIN groups ON queue.group_id = groups.id
                        WHERE GREATEST(date - NOW(), NOW() - date) < interval '1 HOUR' AND is_notified = FALSE
                        ORDER BY date;""")
    queue_notifications = cursor.fetchall()
    for queue_notif in queue_notifications:
        cursor.execute("""UPDATE queue SET is_notified = TRUE WHERE id = %s;""", (queue_notif[0],))

    return [{key: value for key, value in 
                    zip(['queue_id', 'group_id', 'message', 'thread_id'], notification)}
                    for notification in queue_notifications]


@database_func
def get_queue_ready(cursor):
    '''
    Получить все очереди, которые должны сейчас запуститься
    Используется только внутри программы
    '''
    
    cursor.execute("""SELECT queue.id, creator_id, queue.group_id, message, thread_id, group_name FROM queue 
                        JOIN groups ON queue.group_id = groups.id
                        WHERE GREATEST(date - NOW(), NOW() - date) < interval '10 SECONDS' AND is_started = FALSE
                        ORDER BY date;""")
    queue_notifications = cursor.fetchall()
    for queue_notif in queue_notifications:
        cursor.execute("""UPDATE queue SET is_started = TRUE WHERE id = %s;""", (queue_notif[0],))

    return [{key: value for key, value in 
                    zip(['queue_id', 'creator_id', 'group_id', 'message', 'thread_id', 'group_name'], notification)}
                    for notification in queue_notifications]


@database_func
def get_message_id(cursor, queue_id: int):
    cursor.execute("""SELECT message_id FROM queue WHERE id = %s""", (queue_id,))
    result = cursor.fetchone()[0]

    return result


@database_func
def get_thread_id(cursor, group_id: int):
    cursor.execute("""SELECT thread_id FROM groups WHERE id = %s;""", (group_id,))
    result = cursor.fetchone()[0]

    return result


@database_func
def get_admins(cursor, group_id: int):
    '''
    Получение админов группы
    '''

    cursor.execute("""SELECT user_id, group_name FROM admin JOIN groups ON groups.id = group_id
                     WHERE group_id = %s""", (group_id,))
    admins = cursor.fetchall()
    return [{key: value for key, value in 
                     zip(['tg_id', 'group_name'], admin)} 
                     for admin in admins] 


@database_func
def get_admin_groups(cursor, tg_id: int):
    '''
    Получение групп у админа
    '''
    
    cursor.execute("""SELECT group_id, group_name FROM admin JOIN groups ON group_id = groups.id
                     WHERE user_id = %s""", (tg_id,))
    admin_groups = cursor.fetchall()

    return [{key: value for key, value in 
                     zip(['group_tg_id', 'group_name'], group)} 
                     for group in admin_groups]