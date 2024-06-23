from .database import database_func


@database_func
def update_queue_message_id(cursor, queue_id: int, queue_message_id: int):
    cursor.execute("""UPDATE queue SET queue_message_id = %s WHERE id = %s""", (queue_message_id, queue_id))

    return None


@database_func
def update_message_id(cursor, queue_id: int, message_id: int):
    cursor.execute("""UPDATE queue SET message_id = %s WHERE id = %s""", (message_id, queue_id))

    return None


@database_func
def update_queue_ready(cursor, queue_id: int):
    cursor.execute("""UPDATE queue SET is_started = TRUE WHERE id = %s""", (queue_id,))

    return None


@database_func
def update_queue_name(cursor, queue_id: int, message: str):
    cursor.execute("""UPDATE queue SET message = %s WHERE id = %s""", (message, queue_id))
    cursor.execute("""SELECT group_id, queue_message_id FROM queue WHERE id = %s;""", (queue_id,))
    queue_info = cursor.fetchone()

    return queue_info