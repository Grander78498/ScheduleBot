"""
Функции, напрямую управляющие очередями
"""


from .imports import *
from .celery_calls import send_render_task
from .utils import get_queue_link


async def add_user_to_queue(queue_id: int, tg_id: int, full_name: str):
    try:
        queue = await Queue.objects.aget(pk=queue_id)
    except:
        return {"error": "Да ты бы ещё за хлебом 2к10 года пошёл, срарый пердед"}
    user, user_created = await TelegramUser.objects.aget_or_create(pk=tg_id, full_name=full_name)
    _, created = await QueueMember.objects.aget_or_create(user=user, queue=queue)
    if user_created:
        return {"started": False}

    if created:
        await send_render_task(queue_id, False)

    return {"started": user.is_started, "queue_member": not created}


async def print_queue(queue_id: int, private: bool, bot_name: str):
    queue = await Queue.objects.aget(pk=queue_id)
    members = [user async for user in queue.queuemember_set.order_by("pk")]
    res_string = f"Название очереди: {queue.text}\n"
    link = await get_queue_link(queue_id, bot_name)
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
            if index == len(members) - 1 and index > 10:
                print('.................\n')
            if index <= 8 or (index <= 10 and len(members) <= 10) or (index >= len(members) - 1 and index > 10):
                user = await TelegramUser.objects.aget(pk=member.user_id)
                res_string += (str(index) + '. ')
                res_string += f"{user.full_name[:32]}" + ("..." if len(user.full_name) > 32 else "")
                res_string += "\n"

    message_list = [message.message_id async for message in queue.message_set.all()]
    wrong_symbols = './()=_'
    for symbol in wrong_symbols:
        res_string = res_string.replace(symbol, f"\\{symbol}")
    print(res_string)
    return queue.group_id, res_string, message_list


async def print_private_queue(queue_id: int, user_id: int, bot_name: str):
    queue = await Queue.objects.aget(pk=queue_id)
    group = await TelegramGroup.objects.aget(pk=queue.group_id)
    members = [user async for user in queue.queuemember_set.order_by("pk")]
    res_string = f"Название очереди: {queue.text}\n"
    res_string += f"Название группы: {group.name}\n"
    link = await get_queue_link(queue_id, bot_name)
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
    wrong_symbols = './()=_'
    for symbol in wrong_symbols:
        res_string = res_string.replace(symbol, f"\\{symbol}")
    print(res_string)
    return queue.group_id, res_string, message_list


async def delete_queue(queue_id: int):
    queue = await Queue.objects.aget(pk=queue_id)
    chat_list, message_list = ([message.chat_id async for message in queue.message_set.all()],
                               [message.message_id async for message in queue.message_set.all()])
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


async def get_all_queues(user_id: int):
    user = await TelegramUser.objects.aget(pk=user_id)
    queue_list = [queue async for queue in user.queue.all().order_by('date')]
    creator_list = [queue async for queue in Queue.objects.filter(creator_id=user_id).order_by('date')]
    if len(set(queue_list).union(set(creator_list))) == 0:
        return {"status": 404, "message": 'У вас нет очередей('}
    res = 'Ваши очереди:\n'
    for index, queue in enumerate(queue_list, 1):
        res += str(index) + '. '
        res += queue.text + '\n'
        group = await TelegramGroup.objects.aget(pk=queue.group_id)
        user = await TelegramUser.objects.aget(pk=user_id)
        res += 'Название группы: ' + group.name + '\n'
        res += f'Статус: {"создатель" if queue.creator_id == user_id else "участник"}'
        my_date = (queue.date + timedelta(hours=user.tz)).strftime(
            '%Y-%m-%d %H:%M')
        res += 'Дата активации очереди: ' + my_date + '\n'
    return {"status": "OK", "data": [{"id": queue.pk, "name": queue.text, "is_creator": queue.creator_id == user_id}
        for queue in list(set(queue_list).union(set(creator_list)))], "message":res}
    # return ([queue.pk for queue in queue_list], len(queue_list),
    #         res, [queue.text for queue in queue_list])


# async def get_creator_queues(user_id: int):
#     creator_queues = [queue async for queue in Queue.objects.filter(creator_id=user_id).order_by('date')]
#     return await print_all_queues(user_id, creator_queues, True)


# async def get_user_queues(tg_id: int):
#     user = await TelegramUser.objects.aget(pk=tg_id)
#     user_queues = [queue async for queue in user.queue.all().order_by('date')]
#     return await print_all_queues(tg_id, user_queues, False)


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

