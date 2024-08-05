"""
Функции, напрямую управляющие очередями
"""


from .imports import *
from .celery_calls import send_render_task


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


async def get_queue_member_id(queue_id: int, tg_id: int):
    queue_member = await QueueMember.objects.aget(queue_id=queue_id, user_id=tg_id)
    return queue_member.pk


async def get_queue_position(member_id: int):
    member = await QueueMember.objects.aget(pk=member_id)
    queue = await Queue.objects.aget(pk=member.queue_id)
    member_list = [mb async for mb in queue.queuemember_set.order_by("pk")]
    return member_list.index(member) + 1

