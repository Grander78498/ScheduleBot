from celery import shared_task
from asgiref.sync import async_to_sync
from django.utils import timezone
from queue_api.api import print_date_diff
from telethon import TelegramClient
import bot
import asyncio
from .models import *
from config import config

celery_event_loop = asyncio.new_event_loop()


@shared_task(name="send_ready")
def task_send_ready(event_id):
    event = Event.objects.get(pk=event_id)
    group = TelegramGroup.objects.get(pk=event.group_id)
    celery_event_loop.run_until_complete(bot.send_ready(event.id, group.thread_id, group.tg_id))


@shared_task(name="send_notif")
def task_send_notif(event_id):
    event = Event.objects.get(pk=event_id)
    group = TelegramGroup.objects.get(pk=event.group_id)
    try:
        getattr(event, "queue")
        message = \
            f"""НАПОМИНАНИЕ!!!
        Очередь {event.text} будет отправлена через {print_date_diff(timezone.now(), event.date)}
        """
    except Exception:
        message = \
            f"""НАПОМИНАНИЕ!!!
                До дедлайна {event.text} осталось {print_date_diff(timezone.now(), event.date)}
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


async def get_users(client: TelegramClient, group_id, bot_id):
    users = []
    async for user in client.iter_participants(group_id):
        if user.id != bot_id:
            users.append({'id': user.id, 'full_name': (user.first_name if user.first_name is not None else "")
                                                      + " " + (user.last_name if user.last_name is not None else "")})
    return users


@shared_task(name="get_users")
def task_get_users(group_id: int, bot_id):
    api_id = config.api_id
    api_hash = config.api_hash.get_secret_value()
    bot_token = config.bot_token.get_secret_value()

    client_bot = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)
    with client_bot:
        result = asyncio.get_event_loop().run_until_complete(get_users(client_bot, group_id, bot_id))
        return result
