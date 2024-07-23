"""
Переработанный logic.py, изначально сделанный Kof3stt и Watson3233
"""


import asyncio

from .models import *
from datetime import datetime, timedelta
from django_celery_beat.models import PeriodicTask, ClockedSchedule
from django.conf import settings
from asgiref.sync import sync_to_async
from django.utils import timezone
import json
import re


async def add_admin(group_id: int, admins: list[int], names: list[str], group_name: str, thread_id: int):
    group, _ = await TelegramGroup.objects.aget_or_create(tg_id=group_id, name=group_name, thread_id=thread_id)
    for admin, name in zip(admins, names):
        try:
            user, _ = await TelegramUser.objects.aget_or_create(tg_id=admin, full_name=name)
            await user.groups.aadd(group, through_defaults={"is_admin": True})
            await user.asave()
        except Exception as e:
            print(e)



async def check_admin(admin_id: int):
    groups = []
    async for group in TelegramGroup.objects.filter(telegramuser=admin_id, groupmember__is_admin=True):
        groups.append(group)
    return groups


async def add_queue(data_dict):
    message = data_dict['text']
    group_id = data_dict['group_id']
    creator_id = data_dict['creator_id']
    creator = await TelegramUser.objects.aget(pk=creator_id)
    tz = creator.tz
    tz = str(tz).rjust(2, '0') + '00'
    date = datetime.strptime(
        f"{data_dict['year']}-{str(data_dict['month']).rjust(2, '0')}-{str(data_dict['day']).rjust(2, '0')} {data_dict['hm']}+{tz}",
        "%Y-%m-%d %H:%M%z")
    group = await TelegramGroup.objects.aget(pk=group_id)
    queue = await Queue.objects.acreate(message=message, date=date, creator=creator, group=group)

    if not settings.DEBUG:
        clocked, _ = await ClockedSchedule.objects.aget_or_create(clocked_time=queue.date)
        await PeriodicTask.objects.acreate(
            clocked=clocked,
            name=f"Queue {queue.message}. Created by {creator.full_name}",
            task="send_queue",
            one_off=True,
            args=json.dumps([queue.pk]),
            expires=queue.date + timedelta(seconds=10)
        )
    else:
        from bot import queue_send, queue_notif_send

        # if queue.date > timezone.now():
        #     await asyncio.sleep((queue.date - timezone.now()).seconds)
        await queue_notif_send(queue.pk, group.thread_id, group.pk, queue.message)
        await queue_send(queue.pk, group.thread_id, group.pk, queue.message)

    return ((await TelegramGroup.objects.aget(pk=group_id)).thread_id,
            queue.date)


def check_time(time, year, month, day):
    '''Функция для проверки корректности времени'''
    check_time_format = bool(re.fullmatch(r'(([01]\d)|(2[0-3])):[0-5]\d', time))
    if not check_time_format:
        return 'TimeError'
    current_date = datetime.now()
    given_date = datetime.strptime(
        f'{day}.{month}.{year} {time}', '%d.%m.%Y %H:%M')
    # Здесь убрать true при нормальном запуске!!!
    if True or (given_date - current_date).total_seconds() >= 2 * 3600:
        return "It's okay it's fine"
    return "EarlyQueueError"


def check_timezone(tz):
    '''Функция проверки корректности временной зоны'''
    return bool(re.fullmatch(r'\-?\d', tz))


async def add_user_to_queue(queue_id: int, tg_id: int, full_name: str):
    queue = await Queue.objects.aget(pk=queue_id)
    user, user_created = await TelegramUser.objects.aget_or_create(pk=tg_id, full_name=full_name)
    if user_created:
        return {"started": False}
    _, created = await QueueMember.objects.aget_or_create(user=user, queue=queue)
    return {"started": user.is_started, "queue_member": not created}


async def print_queue(queue_id: int, private: bool):
    queue = await Queue.objects.aget(pk=queue_id)
    members = [user async for user in queue.queuemember_set.order_by("pk")]
    res_string = f"Название очереди: {queue.message}\n"
    res_string += "\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\n"
    for index, member in enumerate(members, 1):
        user = await TelegramUser.objects.aget(pk=member.user_id)
        res_string += (str(index) + '\. ')
        res_string += f"{user.full_name}"
        if private:
            res_string += f"\(`{member.pk}`\)"
        res_string += "\n"
    return queue.group_id, queue.message_id, res_string


async def update_message_id(queue_id: int, message_id: int):
    await Queue.objects.filter(pk=queue_id).aupdate(message_id=message_id)


async def get_message_id(queue_id: int):
    return (await Queue.objects.aget(pk=queue_id)).message_id


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
        await queue_member.adelete()
        return 'Correct'
    except Exception:
        return 'Incorrect'


async def delete_queue_member_by_id(queue_id: int, tg_id: int):
    try:
        queue_member = await QueueMember.objects.aget(queue_id=queue_id, user_id=tg_id)
        await queue_member.adelete()
        return 'Correct'
    except Exception:
        return 'Incorrect'


async def rename_queue(queue_id: int, message: str):
    await Queue.objects.filter(pk=queue_id).aupdate(message=message)


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
    creator_queues = [queue async for queue in Queue.objects.filter(creator_id=user_id)]
    return await print_all_queues(user_id, creator_queues, True)


async def get_user_queues(tg_id: int):
    user = await TelegramUser.objects.aget(pk=tg_id)
    user_queues = [queue async for queue in user.queue.all()]
    return await print_all_queues(tg_id, user_queues, False)

async def remove_first(queue_id: int):
    try:
        queue = await Queue.objects.aget(pk=queue_id)
        first_user = await queue.queuemember_set.afirst()
        await first_user.adelete()
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
        return {'status': 'NO', 'message': 'Опять саратовское время вводишь???'}

    await TelegramUser.objects.filter(pk=user_id).aupdate(tz=tz)
    return {'status': 'OK', 'message': 'Справился с вводом одной цифры'}
