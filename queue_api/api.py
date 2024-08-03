"""
Переработанный logic.py, изначально сделанный Kof3stt и Watson3233
"""


import asyncio

from .models import *
from datetime import datetime, timedelta
from django_celery_beat.models import PeriodicTask, ClockedSchedule, IntervalSchedule, SECONDS
from django.conf import settings
from django.db.models import F
from asgiref.sync import sync_to_async
from django.utils import timezone
import json
import re


def check_text(text: str, max_len):
    if len(text.encode('utf-8')) >= max_len:
        return {'status': 'NO', 'message': 'Насрал много байтов - повтори ввод названия'}
    return {'status': 'OK'}


async def get_bot_name(bot):
    return (await bot.get_me()).username


async def add_admin(group_id: int, admins: list[int], names: list[str], group_name: str, thread_id: int):
    for admin, name in zip(admins, names):
        await add_user_to_group(group_id, admin, name, True, group_name=group_name, thread_id=thread_id)


async def add_user_to_group(group_id: int,
                            user_id: int, user_fullname: str, is_admin: bool = False, group_name = None, thread_id = None):
    if group_name is None:
        group = await TelegramGroup.objects.aget(tg_id=group_id)
    else:
        group, _ = await TelegramGroup.objects.aget_or_create(tg_id=group_id, name=group_name, thread_id=thread_id)
    try:
        user, _ = await TelegramUser.objects.aget_or_create(tg_id=user_id, full_name=user_fullname)
        await user.groups.aadd(group, through_defaults={"is_admin": is_admin})
        await user.asave()
    except Exception as e:
        print(e)


async def check_admin(admin_id: int):
    groups = []
    async for group in TelegramGroup.objects.filter(telegramuser=admin_id, groupmember__is_admin=True):
        groups.append(group)
    return groups


async def create_queue_tasks(object_id: int, group_id: int, object_type: str):
    if object_type == "queue":
        _object = await Queue.objects.aget(pk=object_id)
    else:
        _object = await Deadline.objects.aget(pk=object_id)
    group = await TelegramGroup.objects.aget(pk=group_id)
    time_diff = _object.date - timezone.now()
    if time_diff >= timedelta(hours=2):
        queue_notif_date = _object.date - timedelta(hours=1)
    else:
        queue_notif_date = _object.date - 0.5 * time_diff

    if not settings.DEBUG:
        clocked_queue, _ = await ClockedSchedule.objects.aget_or_create(clocked_time=_object.date)
        clocked_notif, _ = await ClockedSchedule.objects.aget_or_create(clocked_time=queue_notif_date)
        if time_diff >= timedelta(minutes=2):
            await PeriodicTask.objects.acreate(
                clocked=clocked_notif,
                name=f"{_object.message} {_object.pk} {group.name}",
                task="send_notif",
                one_off=True,
                args=json.dumps([_object.pk, object_type]),
                expires=queue_notif_date + timedelta(seconds=10)
            )
        await PeriodicTask.objects.acreate(
            clocked=clocked_queue,
            name=f"Ready {_object.message} {_object.pk} {group.name}",
            task="send_ready",
            one_off=True,
            args=json.dumps([_object.pk, object_type]),
            expires=_object.date + timedelta(seconds=10)
        )
    else:
        from bot import send_ready, send_notification
        await asyncio.sleep(7)
        await send_notification(_object.pk, group.thread_id, group.pk, _object.message, object_type)
        await asyncio.sleep(3)
        await send_ready(_object.pk, group.thread_id, group.pk, _object.message, object_type)


def print_date_diff(date1, date2):
    # от 1 минуты до 1 часа - в минутах
    # от 1 часа до 6 часов - в 30 минутах
    # от 6 часов до суток - в часах
    # от суток до двух = завтра
    # от двух суток до трёх = послезавтра
    # всё остальное - через недели и дни
    if date2 < date1:
        return '0 секунд'

    diff = date2 - date1
    if diff.days == 0:
        if diff.seconds < 60:
            ending = ""
            if diff.seconds % 10 == 1 and diff.seconds != 11:
                ending = "у"
            elif diff.seconds % 10 in range(2, 5) and diff.seconds not in range(12, 15):
                ending = "ы"

            return f"{diff.seconds} секунд{ending}"
        elif 60 <= diff.seconds < 3600:
            minutes = diff.seconds // 60
            ending = ""
            if minutes % 10 == 1 and minutes != 11:
                ending = "у"
            elif minutes % 10 in range(2, 5) and minutes not in range(12, 15):
                ending = "ы"

            if diff.seconds < 600:
                seconds = diff.seconds % 60
                seconds_ending = ""
                if seconds % 10 == 1 and seconds != 11:
                    seconds_ending = "у"
                elif seconds % 10 in range(2, 5) and seconds not in range(12, 15):
                    seconds_ending = "ы"
                return f"{minutes} минут{ending} и {seconds} секунд{seconds_ending}"

            return f"{minutes} минут{ending}"
        elif 3600 <= diff.seconds < 24 * 3600:
            hours = diff.seconds // 3600
            ending = "ов"
            if hours % 10 == 1 and hours != 11:
                ending = ""
            elif hours % 10 in range(2, 5) and hours not in range(12, 15):
                ending = "а"

            if diff.seconds < 3600 * 60:
                minutes = (diff.seconds // 60) % 60
                minutes_ending = ""
                if minutes % 10 == 1 and minutes != 11:
                    minutes_ending = "у"
                elif minutes % 10 in range(2, 5) and minutes not in range(12, 15):
                    minutes_ending = "ы"
                return f"{hours} час{ending} и {minutes} минут{minutes_ending}"

            return f"{hours} час{ending}"
    elif 1 <= diff.days < 2:
        return "завтра"
    elif 2 <= diff.days < 3:
        return f"послезавтра"
    elif diff.days >= 3:
        weeks = diff.days // 7
        days = diff.days % 7
        week_ending = "ь"
        if weeks % 10 == 1 and weeks != 11:
            week_ending = "ю"
        elif weeks % 10 in range(2, 5) and weeks not in range(12, 15):
            week_ending = "и"

        day_ending = "ней"
        if days % 10 == 1:
            day_ending = "ень"
        elif days % 10 in range(2, 5) and days not in range(12, 15):
            day_ending = "ня"

        if weeks == 0:
            return f"{days} д{day_ending}"
        elif days == 0:
            return f"{weeks} недел{week_ending}"
        else:
            return f"{weeks} недел{week_ending} и {days} д{day_ending}"


async def create_queue_or_deadline(data_dict):
    message = data_dict['text']
    group_id = data_dict['group_id']
    creator_id = data_dict['creator_id']
    creator = await TelegramUser.objects.aget(pk=creator_id)
    tz = creator.tz
    tz = str(tz).rjust(2, '0') + '00'
    if 'sec' in data_dict:
        date = datetime.strptime(
        f"{data_dict['year']}-{str(data_dict['month']).rjust(2, '0')}-{str(data_dict['day']).rjust(2, '0')} {data_dict['hm']}:{str(data_dict['sec']).rjust(2, '0')}+{tz}",
        "%Y-%m-%d %H:%M:%S%z")
    date = datetime.strptime(
        f"{data_dict['year']}-{str(data_dict['month']).rjust(2, '0')}-{str(data_dict['day']).rjust(2, '0')} {data_dict['hm']}+{tz}",
        "%Y-%m-%d %H:%M%z")
    group = await TelegramGroup.objects.aget(pk=group_id)
    is_queue = data_dict["object_type"] == "queue"
    if is_queue:
        queue = await Queue.objects.acreate(message=message, date=date, creator=creator, group=group)
        object_id = queue.pk
    else:
        deadline = await Deadline.objects.acreate(message=message, date=date, creator=creator, group=group)
        object_id = deadline.pk
    time_diff = date - timezone.now()
    if time_diff < timedelta(minutes=2):
        return ((await TelegramGroup.objects.aget(pk=group_id)).thread_id,
                print_date_diff(timezone.now(), date), object_id, "")

    if time_diff >= timedelta(hours=2):
        queue_notif_date = date - timedelta(hours=1)
    else:
        queue_notif_date = date - 0.5 * time_diff

    return ((await TelegramGroup.objects.aget(pk=group_id)).thread_id,
            print_date_diff(timezone.now(), date), object_id, print_date_diff(timezone.now(), queue_notif_date))


async def check_time(time, year, month, day, user_id):
    '''Функция для проверки корректности времени'''
    check_time_format = bool(re.fullmatch(r'(([01]\d)|(2[0-3])):[0-5]\d', time))
    if not check_time_format:
        return 'TimeError'
    user = await TelegramUser.objects.aget(pk=user_id)
    tz = user.tz
    tz = str(tz).rjust(2, '0') + '00'
    current_date = timezone.now()
    given_date = datetime.strptime(
        f"{year}-{str(month).rjust(2, '0')}-{str(day).rjust(2, '0')} {time}+{tz}",
        "%Y-%m-%d %H:%M%z")
    if given_date >= current_date or (current_date - given_date).total_seconds() >= 60:
        return "It's okay it's fine"
    return "EarlyQueueError"


def check_timezone(tz):
    '''Функция проверки корректности временной зоны'''
    return bool(re.fullmatch(r'\-?\d', tz))


async def send_render_task(queue_id: int, private: bool):
    if not settings.DEBUG:
        queue = await Queue.objects.aget(pk=queue_id)
        if not queue.is_rendering:
            from queue_api.tasks import task_render_queue

            queue.is_rendering = True
            task_render_queue.apply_async(args=(queue.pk, private), countdown=0.75)
            await queue.asave()
    else:
        from bot import render_queue
        await render_queue(queue_id, private)


async def add_user_to_queue(queue_id: int, tg_id: int, full_name: str):
    try:
        queue = await Queue.objects.aget(pk=queue_id)
    except:
        return {"error": "Да ты бы ещё за хлебом 2к10 года пошёл, срарый пердед"}
    user, user_created = await TelegramUser.objects.aget_or_create(pk=tg_id, full_name=full_name)
    if user_created:
        return {"started": False}
    _, created = await QueueMember.objects.aget_or_create(user=user, queue=queue)

    if created:
        await send_render_task(queue_id, False)

    return {"started": user.is_started, "queue_member": not created}


async def print_queue(queue_id: int, private: bool):
    queue = await Queue.objects.aget(pk=queue_id)
    members = [user async for user in queue.queuemember_set.order_by("pk")]
    res_string = f"Название очереди: {queue.message}\n"
    res_string += "__________________________\n".replace('_', '\_')
    for index, member in enumerate(members, 1):
        if index == len(members) - 1 and index > 10:
            print('.................\n'.replace('.', '\.'))
        if index <= 8 or (index <= 10 and len(members) <= 10) or (index >= len(members) - 1 and index > 10):
            user = await TelegramUser.objects.aget(pk=member.user_id)
            res_string += (str(index) + '\. ')
            res_string += f"{user.full_name[:32]}" + ("\.\.\." if len(user.full_name) > 32 else "")
            if private:
                res_string += f"\(`{member.pk}`\)"
            res_string += "\n"
    return queue.group_id, queue.message_id, res_string


async def update_message_id(queue_id: int, message_id: int, object_type: str):
    if object_type == "queue":
        await Queue.objects.filter(pk=queue_id).aupdate(message_id=message_id)
    else:
        await Deadline.objects.filter(pk=queue_id).aupdate(message_id=message_id)


async def get_message_id(queue_id: int, object_type: str):
    if object_type == "queue":
        return (await Queue.objects.aget(pk=queue_id)).message_id
    else:
        return (await Deadline.objects.aget(pk=queue_id)).message_id


async def get_queue_link(queue_id: int):
    queue = await Queue.objects.aget(pk=queue_id)
    link = f"https://t.me/c/{int(str(queue.group_id)[4:])}/{queue.message_id}"
    return link


async def delete_queue(queue_id: int):
    queue = await Queue.objects.aget(pk=queue_id)
    group_id, message_id = queue.group_id, queue.message_id
    await queue.adelete()
    return group_id, message_id


async def delete_queue_member(queue_member_id: str):
    try:
        queue_member = await QueueMember.objects.aget(pk=int(queue_member_id))
        queue = await Queue.objects.aget(pk=queue_member.queue_id)
        await queue_member.adelete()
        await send_render_task(queue.pk, False)
        return 'Correct'
    except Exception:
        return 'Incorrect'


async def delete_queue_member_by_id(queue_id: int, tg_id: int):
    try:
        queue_member = await QueueMember.objects.aget(queue_id=queue_id, user_id=tg_id)

        await queue_member.adelete()
        await send_render_task(queue_id, False)
        return 'Correct'
    except Exception:
        return 'Incorrect'


async def rename_queue(queue_id: int, message: str):
    await Queue.objects.filter(pk=queue_id).aupdate(message=message)
    await send_render_task(queue_id, False)


async def print_all_queues(user_id: int, queue_list: list[Queue], is_admin: bool):
    if len(queue_list) == 0 or queue_list[0].pk is None:
        if is_admin:
            return [], 0, 'у вас нет созданных очередей(', []
        else:
            return [], 0, 'у вас нет  очередей в которых вы состоите(', []
    res = 'Ваши очереди:\n'
    for index, queue in enumerate(queue_list, 1):
        res += str(index) + '. '
        res += queue.message + '\n'
        group = await TelegramGroup.objects.aget(pk=queue.group_id)
        user = await TelegramUser.objects.aget(pk=user_id)
        res += 'Название группы: ' + group.name + '\n'
        my_date = (queue.date + timedelta(hours=user.tz)).strftime(
            '%Y-%m-%d %H:%M')
        res += 'Дата активации очереди: ' + my_date + '\n'
    return ([queue.pk for queue in queue_list], len(queue_list),
            res, [queue.message for queue in queue_list])


async def get_creator_queues(user_id: int):
    creator_queues = [queue async for queue in Queue.objects.filter(creator_id=user_id).order_by('date')]
    return await print_all_queues(user_id, creator_queues, True)


async def get_user_queues(tg_id: int):
    user = await TelegramUser.objects.aget(pk=tg_id)
    user_queues = [queue async for queue in user.queue.all().order_by('date')]
    return await print_all_queues(tg_id, user_queues, False)

async def remove_first(queue_id: int):
    try:
        queue = await Queue.objects.aget(pk=queue_id)
        first_user = await queue.queuemember_set.afirst()
        await first_user.adelete()
        await send_render_task(queue_id, False)
        return True
    except Exception:
        return False


async def save_user(tg_id: int, full_name: str):
    user, created = await TelegramUser.objects.aget_or_create(pk=tg_id, full_name=full_name)
    user.is_started = True
    await user.asave()


async def get_queue_member_id(queue_id: int, tg_id: int):
    queue_member = await QueueMember.objects.aget(queue_id=queue_id, user_id=tg_id)
    return queue_member.pk


async def get_user_id(first_member_id: int, second_member_id: str):
    first = await QueueMember.objects.aget(pk=first_member_id)
    queue = await Queue.objects.aget(pk=first.queue_id)
    try:
        second_member_id = int(second_member_id)
    except Exception:
        return {'status': 'Incorrect input', 'message': 'Ты долбаёб блять хули ты хуйню какую-то пихаешь??????'}

    if second_member_id not in [member.pk async for member in queue.queuemember_set.all()]:
        return {'status': 'Wrong queue', 'message': 'Хули ты в неправильную очередь лезешь уёбок????????'}
    if second_member_id == first_member_id:
        return {'status': 'Self chosen', 'message': 'Самолайк == самоотсос'}
    second = await QueueMember.objects.aget(pk=second_member_id)
    return {'status': 'OK', 'user_id': second.user_id, 'message': 'Ай молодца, сосни-ка хуйца',
            'first_name': (await TelegramUser.objects.aget(pk=first.user_id)).full_name, 'queue_name': queue.message,
            'first_position': await get_queue_position(first.pk), 'second_position': await get_queue_position(second.pk),
            'second_name': (await TelegramUser.objects.aget(pk=second.user_id)).full_name}


async def get_queue_position(member_id: int):
    member = await QueueMember.objects.aget(pk=member_id)
    queue = await Queue.objects.aget(pk=member.queue_id)
    member_list = [mb async for mb in queue.queuemember_set.order_by("pk")]
    return member_list.index(member) + 1


async def swap_places(first_member_id: int, second_member_id: int):
    first = await QueueMember.objects.aget(pk=first_member_id)
    second = await QueueMember.objects.aget(pk=second_member_id)
    first.pk, second.pk = second.pk, first.pk
    await first.asave()
    await second.asave()
    await send_render_task(first.queue_id, False)


async def update_started(tg_id: int, full_name: str, started: bool):
    user, _ = await TelegramUser.objects.aget_or_create(pk=tg_id, full_name=full_name)
    user.is_started = started
    await user.asave()


async def change_topic(group_id: int, thread_id: int):
    await TelegramGroup.objects.filter(pk=group_id).aupdate(thread_id=thread_id)


async def change_tz(user_id: int, tz: str):
    if check_timezone(tz):
        tz = int(tz)
    else:
        return {'status': 'NO', 'message': 'Опять саратовское время вводишь???. Пробуй ещё'}

    await TelegramUser.objects.filter(pk=user_id).aupdate(tz=tz)
    return {'status': 'OK', 'message': 'Справился с вводом одной цифры'}


async def handle_request(first_member_id: int, second_member_id: int, first_message_id: int, second_message_id: int):
    first_member = await QueueMember.objects.aget(pk=first_member_id)
    second_member = await QueueMember.objects.aget(pk=second_member_id)
    await SwapRequest.objects.acreate(first_member=first_member, second_member=second_member, first_message_id=first_message_id, second_message_id=second_message_id)


async def add_request_timer(first_id: int, second_id: int, message1_id: int, message2_id: int, queue_id: int):
    if not settings.DEBUG:
        from tasks import task_swap_delete
        task_swap_delete.apply_async(args=(first_id, second_id, message1_id, message2_id, queue_id), countdown=300)
    else:
        from bot import edit_request_message
        await asyncio.sleep(10)
        await edit_request_message(first_id, second_id, message1_id, message2_id, queue_id)


async def remove_request(first_id: int, second_id: int, queue_id: int):
    first_member = await QueueMember.objects.aget(user_id=first_id, queue_id=queue_id)
    second_member = await QueueMember.objects.aget(user_id=second_id, queue_id=queue_id)
    await SwapRequest.objects.filter(first_member=first_member, second_member=second_member).adelete()
    return second_member.pk


async def check_requests(user_id: int, queue_id: int):
    queue_member = await QueueMember.objects.aget(user_id=user_id, queue_id=queue_id)
    has_in_requests = (await queue_member.second_member.acount()) != 0
    has_out_requests = (await queue_member.first_member.acount()) != 0
    return {'in': has_in_requests, 'out': has_out_requests}


async def remove_all_in_requests(member_id: int):
    queue_member = await QueueMember.objects.aget(pk=member_id)
    all_in_requests = queue_member.second_member.all()
    result = [{"first_member": (await QueueMember.objects.aget(pk=req.first_member_id)).user_id,
               "first_message_id": req.first_message_id,
               "second_message_id": req.second_message_id} async for req in all_in_requests]
    await all_in_requests.adelete()
    return result
