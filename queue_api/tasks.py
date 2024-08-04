from celery import shared_task
from asgiref.sync import async_to_sync
from django.utils import timezone
from queue_api.api import print_date_diff
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