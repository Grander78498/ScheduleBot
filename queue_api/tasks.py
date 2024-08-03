from celery import shared_task
from asgiref.sync import async_to_sync
from django.utils import timezone
from queue_api.api import print_date_diff
import bot
import asyncio
from .models import *

celery_event_loop = asyncio.new_event_loop()


@shared_task(name="send_ready")
def task_send_ready(object_id, object_type: str):
    if object_type == 'queue':
        _object = Queue.objects.get(pk=object_id)
    else:
        _object = Deadline.objects.get(pk=object_id)
    group = TelegramGroup.objects.get(pk=_object.group_id)
    celery_event_loop.run_until_complete(bot.send_ready(_object.id, group.thread_id, group.tg_id,
                                                        _object.message, object_type))


@shared_task(name="send_notif")
def task_send_notif(object_id, object_type):
    if object_type == 'queue':
        _object = Queue.objects.get(pk=object_id)
    else:
        _object = Deadline.objects.get(pk=object_id)
    group = TelegramGroup.objects.get(pk=_object.group_id)
    if object_type == 'queue':
        message = \
        f"""НАПОМИНАНИЕ!!!
        Очередь {_object.message} будет отправлена через {print_date_diff(timezone.now(), _object.date)}
        """
    else:
        message = \
            f"""НАПОМИНАНИЕ!!!
                До дедлайна {_object.message} осталось {print_date_diff(timezone.now(), _object.date)}
                """
    celery_event_loop.run_until_complete(bot.send_notification(_object.id, group.thread_id, group.tg_id, message))


@shared_task(name="render_queue")
def task_render_queue(queue_id, private):
    Queue.objects.filter(pk=queue_id).update(is_rendering=False)
    celery_event_loop.run_until_complete(bot.render_queue(queue_id, private))


@shared_task(name="swap_delete")
def task_swap_delete(first_id: int, second_id: int, message1_id: int, message2_id: int, queue_id: int):
    celery_event_loop.run_until_complete(bot.edit_request_message(first_id, second_id,
                                                                  message1_id, message2_id, queue_id))