from .imports import *
from .utils import print_date_diff, OFFSET


async def get_deadline_info(deadline_id: int):
    deadline = await Deadline.objects.aget(pk=deadline_id)
    group_id = deadline.group_id
    text = deadline.text
    group = await TelegramGroup.objects.aget(pk=group_id)
    thread_id = group.thread_id
    date = print_date_diff(timezone.now(), deadline.date)
    time_diff = deadline.date - timezone.now()
    if time_diff < timedelta(minutes=2):
        return group_id, text, thread_id, date, ""

    if time_diff >= timedelta(hours=2):
        queue_notif_date = deadline.date - timedelta(hours=1)
    else:
        queue_notif_date = deadline.date - 0.5 * time_diff

    return group_id, text, thread_id, date, print_date_diff(queue_notif_date, deadline.date)


async def delete_deadline_by_status(deadline_status_id: int):
    deadline_status = await DeadlineStatus.objects.aget(pk=deadline_status_id)
    return await delete_deadline(deadline_status.deadline_id)


async def delete_deadline(deadline_id: int):
    deadline = await Deadline.objects.select_related('group').aget(pk=deadline_id)
    tasks = PeriodicTask.objects.filter(name__in=[f"{deadline.text} {deadline.pk} {deadline.group.name}",
                                                  f"Ready {deadline.text} {deadline.pk} {deadline.group.name}"])
    try:
        message_id = (await Message.objects.filter(event_id=deadline.pk).afirst()).message_id
    except Exception:
        message_id = None
    group_id = deadline.group_id
    async for task in tasks:
        await task.adelete()
    await deadline.adelete()
    return message_id, group_id


async def create_deadline_request(user_id: int, group_id: int):
    deadline_request, is_created = await DeadlineRequest.objects.aget_or_create(user_id=user_id, group_id=group_id)
    if not is_created:
        return {'status': 'ERROR', 'message': 'У вас уже есть непроверенный запрос на создание дедлайна'}
    else:
        return {'status': 'OK'}


async def delete_deadline_request(user_id: int, group_id: int):
    deadline_request = await DeadlineRequest.objects.aget(user_id=user_id, group_id=group_id)
    await deadline_request.adelete()


async def get_deadlines(user_id: int, offset: int, for_admin: bool):
    if for_admin:
        deadline_statuses = [deadline_status async for deadline_status in DeadlineStatus.objects.filter(
            (Q(deadline__group__main_admin_id=user_id) | Q(deadline__creator_id=user_id)) &
            Q(user_id=user_id)).order_by('deadline__date')]
    else:
        deadline_statuses = [deadline async for deadline
                             in DeadlineStatus.objects.filter(user_id=user_id).order_by('deadline__date')]
    len_deadlines = len(deadline_statuses)
    deadline_statuses = deadline_statuses[offset:offset + OFFSET]
    if offset + OFFSET >= len_deadlines:
        has_next = False
    else:
        has_next = True
    deadline_list = []
    for deadline_status in deadline_statuses:
        deadline_list.append((deadline_status.pk, deadline_status.is_done))

    if len(deadline_list) == 0:
        return {"status": 'ERROR', "message": 'У вас нет дедов('}
    res = 'Ваши дедлайны:\n'
    for index, deadline_status in enumerate(deadline_statuses, 1):
        deadline = await Deadline.objects.aget(pk=deadline_status.deadline_id)
        res += str(index + offset) + '. '
        res += deadline.text + '\n'
        group = await TelegramGroup.objects.aget(pk=deadline.group_id)
        res += 'Название группы: ' + (group.name if len(group.name) <= 32 else group.name[:29] + '...') + '\n'
        if not for_admin:
            res += f'Статус: {":check_mark_button:" if deadline_status.is_done else ":red_exclamation_mark:"}\n'
        my_date = print_date_diff(timezone.now(), deadline.date)
        res += 'Дедлайн произойдёт через ' + my_date + '\n'
    return {'status': "OK", 'message': res, 'deadline_list': deadline_list, "has_next": has_next}


async def delete_deadline_status(deadline_status_id: int):
    deadline_status = await DeadlineStatus.objects.aget(pk=deadline_status_id)
    await deadline_status.adelete()


async def print_deadline(deadline_id: int):
    deadline = await Deadline.objects.aget(pk=deadline_id)
    return f"Дедлайн {deadline.text} наступил\! Пути назад больше нет"


async def check_deadline_status(deadline_status_id: int):
    try:
        await DeadlineStatus.objects.aget(pk=deadline_status_id)
        return True
    except Exception:
        return False


async def get_deadline_name(deadline_status_id: int):
    deadline_status = await DeadlineStatus.objects.select_related('deadline', 'deadline__group').aget(pk=deadline_status_id)
    return deadline_status.deadline.text, deadline_status.deadline.group.name


def print_deadline_message(text, date):
    return "Дедлайн {} наступит через {}.".format(text, date)
