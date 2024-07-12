import asyncio

from .models import *
from datetime import datetime, timedelta
from django_celery_beat.models import PeriodicTask, ClockedSchedule
from django.conf import settings
from django.utils import timezone
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
    tz = '0' + str(int(data_dict['timezone']) + 3) + '00'
    group_id = data_dict['group_id']
    creator_id = data_dict['creator_id']
    date = datetime.strptime(
        f"{data_dict['year']}-{str(data_dict['month']).rjust(2, '0')}-{str(data_dict['day']).rjust(2, '0')} {data_dict['hm']}+{tz}",
        "%Y-%m-%d %H:%M%z")
    creator = await TelegramUser.objects.aget(pk=creator_id)
    group = await TelegramGroup.objects.aget(pk=group_id)
    queue = await Queue.objects.acreate(message=message, date=date, tz=tz, creator=creator, group=group)
    clocked = (await ClockedSchedule.objects.aget_or_create(
        clocked_time=queue.date
    ))[0]

    if not settings.DEBUG:
        await PeriodicTask.objects.acreate(
            clocked=clocked,
            name=f"Queue {queue.message}. Created by {creator.full_name}",
            task="send_queue",
            one_off=True,
            args=json.dumps([queue.pk]),
            expires=queue.date + timedelta(seconds=10)
        )
    else:
        from .bot import queue_send

        if queue.date > timezone.now():
            await asyncio.sleep((queue.date - timezone.now()).seconds)
        await queue_send(queue.pk, group.thread_id, group.pk, queue.message)

    return ((await TelegramGroup.objects.aget(pk=group_id)).thread_id,
            queue.date)