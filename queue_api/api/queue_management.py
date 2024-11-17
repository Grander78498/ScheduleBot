"""
Функции, напрямую управляющие очередями
"""


from .imports import *
from .celery_calls import send_render_task
from .utils import get_queue_link, EventType, OFFSET
from aiogram import Bot


QUEUE_COUNT = 25
DEADLINE_COUNT = 35


async def add_user_to_queue(queue_id: int, tg_id: int, full_name: str):
    try:
        queue = await Queue.objects.aget(pk=queue_id)
    except:
        return {"error": "Вы не можете добавиться в эту очередь, поскольку она удалена"}
    user, user_created = await TelegramUser.objects.aget_or_create(pk=tg_id)
    user.full_name = full_name
    _, created = await QueueMember.objects.aget_or_create(user=user, queue=queue)
    if user_created:
        return {"started": False}

    if created:
        await send_render_task(queue_id, False)

    return {"started": user.is_started, "queue_member": not created}


async def print_queue(queue_id: int, private: bool, bot: Bot):
    queue = await Queue.objects.aget(pk=queue_id)
    members = [user async for user in queue.queuemember_set.order_by("pk")]
    res_string = f"Название очереди: {queue.text}\n"
    link = await get_queue_link(queue_id, bot)
    res_string += f"Ссылка для присоединения: {link}\n"
    res_string += "__________________________\n"
    if private:
        for index, member in enumerate(members, 1):
            user = await TelegramUser.objects.aget(pk=member.user_id)
            res_string += (str(index) + '. ')
            res_string += f"{user.full_name[:16]}" + ("..." if len(user.full_name) > 16 else "")
            res_string += f"(`{member.pk}`)"
            res_string += "\n"
    else:
        for index, member in enumerate(members, 1):
            if index == len(members) - 1 and index > 30:
                res_string += '.................\n'
            if index <= 28 or (index <= 30 and len(members) <= 30) or (index >= len(members) - 1 and index > 30):
                user = await TelegramUser.objects.aget(pk=member.user_id)
                res_string += (str(index) + '. ')
                res_string += f"{user.full_name[:32]}" + ("..." if len(user.full_name) > 32 else "")
                res_string += "\n"

    message_list = [message.message_id async for message in queue.message_set.all()]
    wrong_symbols = './()=_-<>'
    for symbol in wrong_symbols:
        res_string = res_string.replace(symbol, f"\\{symbol}")
    return queue.group_id, res_string, message_list


async def print_private_queue(queue_id: int, user_id: int, bot: Bot):
    queue = await Queue.objects.aget(pk=queue_id)
    group = await TelegramGroup.objects.aget(pk=queue.group_id)
    members = [user async for user in queue.queuemember_set.order_by("pk")]
    res_string = f"Название очереди: {queue.text}\n"
    res_string += f"Название группы: {group.name}\n"
    link = await get_queue_link(queue_id, bot)
    res_string += f"Ссылка для присоединения: {link}\n"
    res_string += "__________________________\n"
    dots_added = False
    for index, member in enumerate(members, 1):
        if member.user_id == user_id or index == len(members) or index == 1:
            user = await TelegramUser.objects.aget(pk=member.user_id)
            res_string += (str(index) + '. ')
            res_string += f"{user.full_name[:32]}" + ("..." if len(user.full_name) > 32 else "")
            res_string += "\n"
            if member.user_id == user_id:
                dots_added = False
        elif not dots_added:
            res_string += "............."
            dots_added = True
    message_list = [message.message_id async for message in queue.message_set.all()]
    wrong_symbols = './()=_-><'
    for symbol in wrong_symbols:
        res_string = res_string.replace(symbol, f"\\{symbol}")
    return queue.group_id, res_string, message_list


async def delete_queue(queue_id: int):
    queue = await Queue.objects.select_related('group').aget(pk=queue_id)
    chat_list, message_list = ([message.chat_id async for message in queue.message_set.all()],
                               [message.message_id async for message in queue.message_set.all()])
    tasks = PeriodicTask.objects.filter(name__in=[f"{queue.text} {queue.pk} {queue.group.name}",
                                                  f"Ready {queue.text} {queue.pk} {queue.group.name}"])
    async for task in tasks:
        await task.adelete()
    await queue.adelete()
    return chat_list, message_list


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
    await Queue.objects.filter(pk=queue_id).aupdate(text=message)
    await send_render_task(queue_id, False)


async def get_all_queues(user_id: int, offset: int, for_swap: bool):
    sub_q = QueueMember.objects.filter(user_id=user_id).values_list("queue", flat=True)
    if not for_swap:
#        queue_list = [queue async for queue in
#                      Queue.objects.filter(Q(creator_id=user_id) | Q(queuemember__user_id=user_id)).order_by("date")]
        queue_list = [queue async for queue in
                      Queue.objects.filter(Q(creator_id=user_id) | Q(id__in=sub_q)).order_by("date")]
    else:
        queue_list = [queue async for queue in
                      Queue.objects.filter(id__in=sub_q).order_by("date")]
    len_queues = len(queue_list)
    queue_list = queue_list[offset:offset + OFFSET]
    if offset + OFFSET >= len_queues:
        has_next = False
    else:
        has_next = True
    if len(queue_list) == 0:
        return {"status": 404, "message": 'У вас нет очередей('}
    res = 'Ваши очереди:\n'
    for index, queue in enumerate(queue_list, 1):
        res += str(index + offset) + '. '
        res += queue.text + '\n'
        group = await TelegramGroup.objects.aget(pk=queue.group_id)
        user = await TelegramUser.objects.aget(pk=user_id)
        res += 'Название группы: ' + (group.name if len(group.name) <= 32 else group.name[:29] + '...') + '\n'
        res += f'Статус: {"создатель" if queue.creator_id == user_id else "участник"}\n'
        my_date = (queue.date + timedelta(hours=user.tz)).strftime(
            '%Y-%m-%d %H:%M')
        res += 'Дата активации очереди: ' + my_date + '\n'
    wrong_symbols = './()=_-'
    for symbol in wrong_symbols:
        res = res.replace(symbol, f"\\{symbol}")
    return {"status": "OK", "data": [{"id": queue.pk, "name": queue.text, "is_creator": queue.creator_id == user_id}
            for queue in queue_list], "message": res, "has_next": has_next}


async def remove_first(queue_id: int):
    try:
        queue = await Queue.objects.aget(pk=queue_id)
        first_user = await queue.queuemember_set.afirst()
        await first_user.adelete()
        await send_render_task(queue_id, False)
        return True
    except Exception:
        return False


async def get_queue_member_id(queue_id: int, tg_id: int):
    queue_member = await QueueMember.objects.aget(queue_id=queue_id, user_id=tg_id)
    return queue_member.pk


async def get_queue_position(member_id: int):
    member = await QueueMember.objects.aget(pk=member_id)
    queue = await Queue.objects.aget(pk=member.queue_id)
    member_list = [mb async for mb in queue.queuemember_set.order_by("pk")]
    return member_list.index(member) + 1


async def check_event_count(user_id: int, event_type: EventType):
    is_queue = event_type == EventType.QUEUE
    if is_queue and (await Queue.objects.filter(creator_id=user_id).acount()) > QUEUE_COUNT:
        return {"status": "ERROR", "message": "Куда тебе столько очередей то???"}
    if not is_queue and (await Deadline.objects.filter(creator_id=user_id).acount()) > DEADLINE_COUNT:
        return {"status": "ERROR", "message": "Куда тебе столько дедлайнов то???"}
    return {"status": 'OK'}


def print_queue_message(text, date, notif_date):
    return "Очередь {} будет создана {}.".format(text, date) + \
            (" Напоминание будет отправлено {}".format(notif_date)
             if notif_date != "" else "")


async def check_user_in_queue(user_id, queue_id):
    try:
        queue = await Queue.objects.aget(pk=queue_id)
    except Exception as a:
        return {"status":"ERROR","message":"Очередь уже была удалена"}
    try:
        mem = await QueueMember.objects.aget(queue_id=queue_id, user_id=user_id)
        return {"status":"OK"}
    except Exception as b:
        return {"status":"ERROR","message":"Тебя выкинули из очереди"}
