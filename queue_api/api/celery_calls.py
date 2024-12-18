"""
Функции, создающие задачи в celery
"""


from .imports import *


async def create_queue_tasks(event_id: int, group_id: int):
    event = await Event.objects.select_related('queue', 'deadline', 'creator').aget(pk=event_id)
    group = await TelegramGroup.objects.aget(pk=group_id)
    time_diff = event.date - timezone.now()
    if time_diff >= timedelta(hours=2):
        queue_notif_date = event.date - timedelta(hours=1)
    else:
        queue_notif_date = event.date - 0.5 * time_diff

    if not settings.DEBUG:
        clocked_queue, _ = await ClockedSchedule.objects.aget_or_create(clocked_time=event.date)
        clocked_notif, _ = await ClockedSchedule.objects.aget_or_create(clocked_time=queue_notif_date)
        if time_diff >= timedelta(minutes=2):
            await PeriodicTask.objects.acreate(
                clocked=clocked_notif,
                name=f"{event.text} {event.pk} {group.name}",
                task="send_notif",
                one_off=True,
                args=json.dumps([event.pk]),
                expires=queue_notif_date + timedelta(seconds=10)
            )
        await PeriodicTask.objects.acreate(
            clocked=clocked_queue,
            name=f"Ready {event.text} {event.pk} {group.name}",
            task="send_ready",
            one_off=True,
            args=json.dumps([event.pk]),
            expires=event.date + timedelta(minutes=1)
        )
    else:
        from bot import send_ready, send_notification
        try:
            getattr(event, "queue")
            message = \
                f"""НАПОМИНАНИЕ!!!\nОчередь {event.text} будет создана {(event.date + timedelta(hours=event.creator.tz)).strftime('%d/%m/%Y, %H:%M:%S')}"""
        except Exception as e:
            message = \
                f"""НАПОМИНАНИЕ!!!\nДедлайн {event.text} наступит {(event.date + timedelta(hours=event.creator.tz)).strftime('%d/%m/%Y, %H:%M:%S')}"""
        await asyncio.sleep(7)
        await send_notification(event.pk, group.thread_id, group.pk, message)
        await asyncio.sleep(3)
        await send_ready(event.pk, group.thread_id, group.pk)


async def add_request_timer(first_id: int, second_id: int, message1_id: int, message2_id: int, queue_id: int):
    if not settings.DEBUG:
        from queue_api.tasks import task_swap_delete
        task_swap_delete.apply_async(args=(first_id, second_id, message1_id, message2_id, queue_id), countdown=300)
    else:
        from bot import edit_request_message
        await asyncio.sleep(10)
        await edit_request_message(first_id, second_id, message1_id, message2_id, queue_id)


async def send_render_task(queue_id: int, private: bool):
    if not settings.DEBUG:
        queue = await Queue.objects.aget(pk=queue_id)
        if not queue.is_rendering:
            from queue_api.tasks import task_render_queue

            queue.is_rendering = True
            task_render_queue.apply_async(args=(queue.pk, private), countdown=0.75)
            await queue.asave()
    else:
        from bot import render_queue
        await render_queue(queue_id, private)


# async def santa_render_task(santa_id: int, private: bool):
#     if not settings.DEBUG:
#         santa = await Santa.objects.aget(pk=santa_id)
#         if not santa.is_rendering:
#             from queue_api.tasks import task_render_queue

#             santa.is_rendering = True
#             task_render_queue.apply_async(args=(santa.pk, private), countdown=0.75)
#             await santa.asave()
#     else:
#         from bot import send_christmas
#         await send_christmas(queue_id, private)
