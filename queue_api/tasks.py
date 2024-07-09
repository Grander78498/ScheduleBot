from celery import shared_task
from django_celery_beat.models import PeriodicTask
from asgiref.sync import async_to_sync
from .bot import queue_send
from .models import *


@shared_task(name="send_queue")
def send_queue(queue_id):
    queue = Queue.objects.get(pk=queue_id)
    creator = TelegramUser.objects.get(pk=queue.creator_id)
    group = TelegramGroup.objects.get(pk=queue.group_id)
    task = PeriodicTask.objects.get(name=f"Queue {queue.message}. Created by {creator.full_name}")
    async_to_sync(queue_send)(queue.id, group.thread_id, group.tg_id, queue.message)
    task.delete()
