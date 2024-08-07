from .imports import *
from .utils import print_date_diff


async def get_deadline_info(deadline_id: int):
    deadline = await Deadline.objects.get(pk=deadline_id)
    group_id = deadline.group_id
    text = deadline.text
    group = await TelegramGroup.objects.get(pk=group_id)
    thread_id = group.thread_id
    date = print_date_diff(timezone.now(), deadline.date)
    time_diff = date - timezone.now()
    if time_diff < timedelta(minutes=2):
        return group_id, text, thread_id, date, ""

    if time_diff >= timedelta(hours=2):
        queue_notif_date = date - timedelta(hours=1)
    else:
        queue_notif_date = date - 0.5 * time_diff

    return group_id, text, thread_id, date, print_date_diff(queue_notif_date, date)
