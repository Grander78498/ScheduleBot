from src import db as database
import datetime
import re


def add_admin(group_id: int, admins: list[int], group_name: str, thread_id: int):
    '''Функция для ...'''
    try:
        database.add_group(group_id, group_name, thread_id)
    except Exception:
        pass

    for admin_id in admins:
        try:
            database.add_admin(group_id, admin_id)
        except Exception:
            continue


def check_admin(user_id: int):
    '''Функция для ...'''
    return database.get_admin_groups(user_id)


def add_queue(data_dict):
    '''Функия для ...'''
    # {'text': 'fdsdfdsfs', 'year': 2024, 'month': 5, 'day': 25, 'timezone': '0', 'hm': '12:09', group_id: id_int, creator_id: id_int}
    message = data_dict['text']
    timezone = int(data_dict['timezone']) + 3
    group_id = data_dict['group_id']
    creator_id = data_dict['creator_id']
    date = f"{data_dict['year']}-{str(data_dict['month']).rjust(2, '0')}-{str(data_dict['day']).rjust(2, '0')} {data_dict['hm']}+{timezone}"
    database.add_queue(message, date, timezone, creator_id, group_id)

    return database.get_thread_id(group_id), date


def check_time(time, year, month, day):
    '''Функция для проверки корректности времени'''
    check_time_format = bool(re.fullmatch(r'(([01]\d)|(2[0-3])):[0-5]\d', time))
    if not check_time_format:
        return 'TimeError'
    current_date = datetime.datetime.now()
    given_date = datetime.datetime.strptime(
        f'{day}.{month}.{year} {time}', '%d.%m.%Y %H:%M')
    # Здесь убрать true при нормальном запуске!!!
    if True or (given_date - current_date).total_seconds() >= 2 * 3600:
        return "It's okay it's fine"
    return "EarlyQueueError"


def check_timezone(timezone):
    '''Функция проверки корректности временной зоны'''
    return bool(re.fullmatch(r'\-?\d', timezone))


def add_user_to_queue(queue_id: int, tg_id: int, full_name: str, vote_date: datetime.datetime):
    '''Функция для ...'''
    database.add_user_to_queue(queue_id, tg_id, full_name, vote_date.strftime('%Y-%m-%d %H:%M:%S'))


def print_queue(queue_id: int):
    '''Функция для ...'''
    queue_info = database.get_queue(queue_id)
    # {'message': 'Lol', 'date': datetime.datetime, 'creator_id': 1242141, 'group_id': 12412421} [{'tg_id': 42646, 'full_name': 'Egor', 'vote_date': datetime.datetime} .......]
    group_info, users_info = queue_info
    print(group_info)
    res_string = f"Название очереди: <b>{group_info['message']}</b>\n"
    res_string += "__________________________\n"
    for index, user in enumerate(users_info, 1):
        res_string += (str(index) + '. ')
        res_string += user['full_name'] + "\n"
    return group_info['group_id'], group_info['queue_message_id'], res_string


def get_creator_queues(user_id: int):
    '''Функция для ...'''
    creator_queues = database.get_admin_queues(user_id)
    if len(creator_queues) == 0 or creator_queues[0]["queue_id"] is None:
        return [], 0, 'У вас нет созданных очередей(', []
    res = 'Ваши очереди:\n'
    for index, queue in enumerate(creator_queues, 1):
        res += str(index) + '. '
        res += queue['message'] + '\n'
        res += 'Название группы: ' + queue['group_name'] + '\n'
        my_date = (queue['date'] + datetime.timedelta(hours=queue['timezone'] - 3)).strftime(
            '%Y-%m-%d %H:%M')  #ЫЫЫ важна...может быть...
        res += 'Дата активации очереди: ' + my_date + '\n'
    return [queue['queue_id'] for queue in creator_queues], len(creator_queues), res, [queue['message'] for queue in
                                                                                       creator_queues]


def get_queue_position(queue_id: int, tg_id: int):
    '''Функция для ...'''
    # {'message': 'Lol', 'date': datetime.datetime, 'creator_id': 1242141, 'group_id': 12412421} [{'tg_id': 42646, 'full_name': 'Egor', 'vote_date': datetime.datetime} .......]
    queue_info = database.get_queue(queue_id)
    queue_info, users_info = queue_info
    mas = [user_info['tg_id'] for user_info in users_info]
    return 'Ваше место в очереди {}: {}'.format(queue_info['message'], mas.index(tg_id) + 1)


def get_queue_notif():
    data = database.get_queue_notifications()
    for elem in data:
        elem['message'] = f"Напоминание!!!\nОчередь {elem['message']} будет создана через час"
    return data


def already_queue():
    queue_data = database.get_queue_ready()
    for elem in queue_data:
        elem['message'] = f"Очередь {elem['message']} была создана"
        elem['admin_message'] = f"{elem['message']} в группе {elem['group_name']}"
    return queue_data


def update_message_id(queue_id: int, message_id: int):
    database.update_message_id(queue_id, message_id)


def get_message_id(queue_id: int):
    return database.get_message_id(queue_id)


def update_queue_message_id(queue_id: int, queue_message_id: int):
    database.update_queue_message_id(queue_id, queue_message_id)


def delete_queue(queue_id: int):
    return database.delete_queue(queue_id)


def rename_queue(queue_id: int, message: str):
    database.update_queue_name(queue_id, message)


def delete_queue_member(queue_id: int, queue_position: str):
    _, users_info = database.get_queue(queue_id)
    try:
        queue_position = int(queue_position)
    except Exception:
        return "Incorrect"
    if queue_position > len(users_info) or queue_position <= 0:
        return "Doesn't exist"
    tg_id = users_info[queue_position - 1]['tg_id']
    return database.delete_queue_member(queue_id, tg_id)
