from .imports import *
from .utils import print_date_diff


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


async def delete_deadline(deadline_id: int):
    deadline = await Deadline.objects.aget(pk=deadline_id)
    await deadline.adelete()


async def create_deadline_request(user_id: int, group_id: int):
    deadline_request, is_created = await DeadlineRequest.objects.aget_or_create(user_id=user_id, group_id=group_id)
    if not is_created:
        return {'status': 'ERROR', 'message': 'Ваш запрос послан нахуй заранее - у вас уже есть непроверенный запрос на создание дедлайна'}
    else:
        return {'status': 'OK'}


async def delete_deadline_request(user_id: int, group_id: int):
    deadline_request = await DeadlineRequest.objects.aget(user_id=user_id, group_id=group_id)
    await deadline_request.adelete()
