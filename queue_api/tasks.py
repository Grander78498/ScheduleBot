from celery import shared_task
from asgiref.sync import async_to_sync
import bot
import asyncio
from .models import *

celery_event_loop = asyncio.new_event_loop()


@shared_task(name="send_queue")
def task_send_queue(queue_id):
    queue = Queue.objects.get(pk=queue_id)
    group = TelegramGroup.objects.get(pk=queue.group_id)
    celery_event_loop.run_until_complete(bot.queue_send(queue.id, group.thread_id, group.tg_id, queue.message))


@shared_task(name="queue_notif")
def task_queue_notif(queue_id):
    queue = Queue.objects.get(pk=queue_id)
    group = TelegramGroup.objects.get(pk=queue.group_id)
    celery_event_loop.run_until_complete(bot.queue_notif_send(queue.id, group.thread_id, group.tg_id, queue.message))


@shared_task(name="render_queue")
def task_render_queue(queue_id, private):
    Queue.objects.filter(pk=queue_id).update(is_rendering=False)
    celery_event_loop.run_until_complete(bot.render_queue(queue_id, private))
