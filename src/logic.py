import database
import datetime
import re


def add_admin(group_id: int, admins: list[int], group_name: str):
    '''Функция для ...'''
    adm = database.get_admins(group_id)
    stash = []
    for item in adm:
        stash.append(item.get('tg_id', None))
    admins = [i for i in admins if i not in stash]
    database.add_admins(group_id, admins, group_name)


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
    date = f"{data_dict['day']}.{data_dict['month']}.{data_dict['year']} {data_dict['hm']}+{timezone}"
    database.add_queue(message, date, timezone, creator_id, group_id)


def check_time(time):
    '''Функция для проверки корректности времени'''
    return bool(re.fullmatch(r'(([01]\d)|(2[0-3])):[0-5]\d', time))


def check_timezone(timezone):
    '''Функция проверки корректности временной зоны'''
    return bool(re.fullmatch(r'\-?\d', timezone))


def add_user_to_queue(queue_id: int, tg_id: int, full_name: str, vote_date: datetime.datetime):
    '''Функция для ...'''
    try:
        database.add_user_to_queue(queue_id, tg_id, full_name, str(vote_date))
    except Exception:
        pass


def print_queue(queue_id: int):
    '''Функция для ...'''
    queue_info = database.get_queue(queue_id)
    # {'message': 'Lol', 'date': datetime.datetime, 'creator_id': 1242141, 'group_id': 12412421} [{'tg_id': 42646, 'full_name': 'Egor', 'vote_date': datetime.datetime} .......]
    group_info, users_info = queue_info
    res_string = 'Формирование очереди завершено\n'
    res_string += f"Название очереди: {group_info['message']}\n"
    for index, user in enumerate(users_info, 1):
        res_string += (str(index) + '. ')
        res_string += user['full_name']
    return res_string


def get_creator_queues(user_id: int):
    '''Функция для ...'''
    creator_queues = database.get_admin_queues(user_id)
    if not creator_queues:
        return 'У вас нет созданных очередей('
    res = 'Ваши очереди:\n'
    for index, queue in enumerate(creator_queues, 1):
        res += str(index) + '. '
        res += queue['message'] + '\n'
        res += 'Название группы: ' + queue['full_name'] + '\n'
        my_date = (queue['date'] + datetime.timedelta(hours=queue['timezone'])).strftime('%Y-%m-%d %H:%M') #ЫЫЫ важна...может быть...
        res += 'Дата активации очереди: ' + my_date + '\n'
    return res


def get_queue_position(queue_id: int,tg_id: int):
    '''Функция для ...'''
    # {'message': 'Lol', 'date': datetime.datetime, 'creator_id': 1242141, 'group_id': 12412421} [{'tg_id': 42646, 'full_name': 'Egor', 'vote_date': datetime.datetime} .......]
    queue_info = database.get_queue(queue_id)
    _, users_info = queue_info
    mas=[user_info['tg_id'] for user_info in users_info]
    return 'Ваше место в очереди: {}'.format(mas.index(tg_id)+1)

def get_queue_notif():
    data=database.get_queue_notifications()
    return data

def already_queue():
    queue_data=database.get_queue_ready()
    for elem in queue_data:
        elem['message'] = f"Очередь {elem['message']} была создана"
        elem['admin_message'] = f"Очередь {elem['message']} была создана в группе {elem['group_name']}"
    return queue_data
