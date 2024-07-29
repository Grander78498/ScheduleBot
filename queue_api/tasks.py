from celery import shared_task
from asgiref.sync import async_to_sync
from bot import queue_send, queue_notif_send
from .models import *


@shared_task(name="send_queue")
def send_queue(queue_id):
    queue = Queue.objects.get(pk=queue_id)
    group = TelegramGroup.objects.get(pk=queue.group_id)
    async_to_sync(queue_send)(queue.id, group.thread_id, group.tg_id, queue.message)


@shared_task(name="queue_notif")
def queue_notif(queue_id):
    queue = Queue.objects.get(pk=queue_id)
    group = TelegramGroup.objects.get(pk=queue.group_id)
    async_to_sync(queue_notif_send)(queue.id, group.thread_id, group.tg_id, queue.message)
