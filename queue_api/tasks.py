from celery import shared_task
from django.utils import timezone
from telethon import TelegramClient
from bot import send_ready, send_notification, render_queue, edit_request_message, session_begin, session_end
import asyncio
from .models import *
from config import config

celery_event_loop = asyncio.new_event_loop()


@shared_task(name="send_ready")
def task_send_ready(event_id):
    event = Event.objects.get(pk=event_id)
    group = TelegramGroup.objects.get(pk=event.group_id)
    celery_event_loop.run_until_complete(send_ready(event.id, group.thread_id, group.tg_id))


@shared_task(name="send_notif")
def task_send_notif(event_id):
    event = Event.objects.select_related('queue', 'deadline').get(pk=event_id)
    group = TelegramGroup.objects.get(pk=event.group_id)
    try:
        getattr(event, "queue")
        message = \
            f"""НАПОМИНАНИЕ!!!\nОчередь {event.text} станет активна через {event.date.strftime('%d/%m/%Y, %H:%M:%S')}"""
    except Exception:
        message = \
            f"""НАПОМИНАНИЕ!!!\nДо дедлайна {event.text} осталось {event.date.strftime('%d/%m/%Y, %H:%M:%S')}"""
    celery_event_loop.run_until_complete(send_notification(event.id, group.thread_id, group.tg_id, message))


@shared_task(name="render_queue")
def task_render_queue(queue_id, private):
    Queue.objects.filter(pk=queue_id).update(is_rendering=False)
    celery_event_loop.run_until_complete(render_queue(queue_id, private))


@shared_task(name="swap_delete")
def task_swap_delete(first_id: int, second_id: int, message1_id: int, message2_id: int, queue_id: int):
    celery_event_loop.run_until_complete(edit_request_message(first_id, second_id,
                                                              message1_id, message2_id, queue_id))


async def get_users(client: TelegramClient, group_id, bot_id):
    users = []
    async for user in client.iter_participants(group_id):
        if user.id != bot_id:
            users.append({'id': user.id, 'full_name': (user.first_name if user.first_name is not None else "")
                                                      + (" " + user.last_name if user.last_name is not None else "")})
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


@shared_task(name='session_begin')
def task_session_begin(group_id: int, thread_id: int):
    student_group = StudentGroup.objects.get(pk=group_id)
    student_group.is_session = True
    student_group.save()
    celery_event_loop.run_until_complete(session_begin(group_id, thread_id))


@shared_task(name='session_end')
def task_session_end(group_id: int, thread_id: int):
    student_group = StudentGroup.objects.get(pk=group_id)
    if student_group.is_session:
        student_group.is_session = False
        student_group.save()
        celery_event_loop.run_until_complete(session_end(group_id, thread_id))
