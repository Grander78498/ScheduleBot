from .models import *
from datetime import datetime
from django_celery_beat.models import PeriodicTask, IntervalSchedule
import json


async def add_admin(group_id: int, admins: list[int], group_name: str, thread_id: int):
    group, _ = await TelegramGroup.objects.aget_or_create(tg_id=group_id, name=group_name, thread_id=thread_id)
    for admin in admins:
        user, _ = await TelegramUser.objects.aget_or_create(tg_id=admin)
        await user.groups.aadd(group, through_defaults={"is_admin": True})
        await user.asave()


async def check_admin(admin_id: int):
    groups = []
    async for group in TelegramGroup.objects.filter(telegramuser=admin_id, groupmember__is_admin=True):
        groups.append(group)
    return groups


async def add_queue(data_dict):
    message = data_dict['text']
    timezone = '0' + str(int(data_dict['timezone']) + 3) + '00'
    group_id = data_dict['group_id']
    creator_id = data_dict['creator_id']
    date = datetime.strptime(
        f"{data_dict['year']}-{str(data_dict['month']).rjust(2, '0')}-{str(data_dict['day']).rjust(2, '0')} {data_dict['hm']}+{timezone}",
        "%Y-%m-%d %H:%M%z")
    creator = await TelegramUser.objects.aget(pk=creator_id)
    group = await TelegramGroup.objects.aget(pk=group_id)
    queue = await Queue.objects.acreate(message=message, date=date, tz=timezone, creator=creator, group=group)

    await PeriodicTask.objects.acreate(
        name=f"Queue {queue.message}. Created by {creator.full_name}",
        task="send_queue",
        interval=(await IntervalSchedule.objects.aget_or_create(every=15, period='seconds'))[0],
        args=json.dumps([queue.pk]),
        start_time=queue.date
    )

    return ((await TelegramGroup.objects.aget(pk=group_id)).thread_id,
            queue.date)