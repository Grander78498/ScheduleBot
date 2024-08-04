from celery import shared_task
from asgiref.sync import async_to_sync
from django.utils import timezone
from queue_api.api import print_date_diff
from telethon import TelegramClient
import bot
import asyncio
from .models import *

celery_event_loop = asyncio.new_event_loop()


@shared_task(name="send_ready")
def task_send_ready(event_id):
    event = Event.objects.get(pk=event_id)
    group = TelegramGroup.objects.get(pk=event.group_id)
    celery_event_loop.run_until_complete(bot.send_ready(event.id, group.thread_id, group.tg_id,
                                                        event.message))


@shared_task(name="send_notif")
def task_send_notif(event_id):
    event = Event.objects.get(pk=event_id)
    group = TelegramGroup.objects.get(pk=event.group_id)
    try:
        getattr(event, "queue")
        message = \
        f"""НАПОМИНАНИЕ!!!
        Очередь {event.message} будет отправлена через {print_date_diff(timezone.now(), event.date)}
        """
    except Exception:
        message = \
            f"""НАПОМИНАНИЕ!!!
                До дедлайна {event.message} осталось {print_date_diff(timezone.now(), event.date)}
                """
    celery_event_loop.run_until_complete(bot.send_notification(event.id, group.thread_id, group.tg_id, message))


@shared_task(name="render_queue")
def task_render_queue(queue_id, private):
    Queue.objects.filter(pk=queue_id).update(is_rendering=False)
    celery_event_loop.run_until_complete(bot.render_queue(queue_id, private))


@shared_task(name="swap_delete")
def task_swap_delete(first_id: int, second_id: int, message1_id: int, message2_id: int, queue_id: int):
    celery_event_loop.run_until_complete(bot.edit_request_message(first_id, second_id,
                                                                  message1_id, message2_id, queue_id))


async def get_users(client: TelegramClient, group_id):
    users = []
    print(dir(client))
    async for user in client.iter_participants(group_id):
        users.append({'id': user.id, 'full_name': (user.first_name if user.first_name is not None else "")
            + " " + (user.last_name if user.last_name is not None else "")})
    return users


@shared_task(name="get_users")
def task_get_users(group_id: int):
    api_id = 26588665
    api_hash = "f9662262f669c9c65d5c8d550db647cc"
    bot_token = "6733084480:AAECacPclPo0emdVottudh9o9yoSqJP7BGs"

    client_bot = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token) 
    with client_bot:
        result = asyncio.get_event_loop().run_until_complete(get_users(client_bot, group_id))
        return result
