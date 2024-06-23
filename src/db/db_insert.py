from .database import database_func


@database_func
def create_tables(cursor):
    '''
    Создать таблицы, если не существуют
    Функция будет вызываться при каждом запуске бота
    '''

    cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users
                    (id BIGINT,
                    full_name VARCHAR (128),
                    PRIMARY KEY (id));

                    CREATE TABLE IF NOT EXISTS groups
                    (id BIGINT,
                    group_name VARCHAR (128),
                    thread_id BIGINT,
                    PRIMARY KEY (id));

                    CREATE TABLE IF NOT EXISTS queue
                    (id BIGSERIAL,
                    message VARCHAR (64),
                    date TIMESTAMPTZ NOT NULL,
                    tz INT NOT NULL,
                    is_started BOOLEAN NOT NULL,
                    is_notified BOOLEAN NOT NULL,
                    creator_id BIGINT REFERENCES users (id),
                    group_id BIGINT REFERENCES groups (id),
                    message_id BIGINT,
                    queue_message_id BIGINT,
                    PRIMARY KEY (id));
                    
                    CREATE TABLE IF NOT EXISTS admin
                    (user_id BIGINT REFERENCES users (id),
                    group_id BIGINT REFERENCES groups (id),
                    PRIMARY KEY (user_id, group_id));

                    CREATE TABLE IF NOT EXISTS queue_member
                    (queue_id BIGINT REFERENCES queue (id),
                    user_id BIGINT REFERENCES users (id));
                    ''')
    
    return None


@database_func
def add_group(cursor, group_id: int, group_name: int, thread_id: int):
    cursor.execute("""INSERT INTO groups VALUES (%s, %s, %s)""", (group_id, group_name, thread_id))

    return None


@database_func
def add_admin(cursor, group_id: int, admin_id: int):
    cursor.execute("""INSERT INTO users (id) VALUES (%s) 
                      ON CONFLICT (id) DO NOTHING""", (admin_id,))
    cursor.execute("""INSERT INTO admin (user_id, group_id) VALUES (%s, %s)""", (admin_id, group_id))

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

    cursor.execute('INSERT INTO queue (message, date, tz, is_started, is_notified, creator_id, group_id) VALUES (%s, %s, %s, FALSE, FALSE, %s, %s);',
                    (message, date, timezone, creator_id, group_id))
    
    return None


@database_func
def add_user_to_queue(cursor, queue_id: int, user_id: int, full_name: str, vote_date: str):
    """
    Добавить пользователя в очередь

    queue_id - id очереди,
    user_id - id пользователя
    full_name - его полное имя
    vote_date - дата голосования
    """

    cursor.execute("""INSERT INTO users VALUES (%s, %s)
                      ON CONFLICT (id) DO UPDATE users SET full_name = %s""",
                      (user_id, full_name, full_name))

    cursor.execute("""INSERT INTO queue_member VALUES (%s, %s)""", 
                    (queue_id, user_id, vote_date))
    
    return None
