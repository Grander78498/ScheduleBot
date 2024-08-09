"""
Функции, которые обновляют значения полей в различных таблицах
"""


from .imports import *
from .utils import check_timezone


async def update_message_id(event_id: int, message_id: int, chat_id: int):
    event = await Event.objects.aget(pk=event_id)
    message, _ = await Message.objects.aget_or_create(event=event, chat_id=chat_id)
    message.message_id = message_id
    await message.asave()


async def update_started(tg_id: int, full_name: str, started: bool):
    user, _ = await TelegramUser.objects.aget_or_create(pk=tg_id, full_name=full_name)
    user.is_started = started
    await user.asave()


async def change_topic(group_id: int, thread_id: int):
    await TelegramGroup.objects.filter(pk=group_id).aupdate(thread_id=thread_id)


async def change_tz(user_id: int, tz: str):
    if check_timezone(tz):
        tz = int(tz)
    else:
        return {'status': 'NO', 'message': 'Опять саратовское время вводишь???. Пробуй ещё'}

    await TelegramUser.objects.filter(pk=user_id).aupdate(tz=tz)
    return {'status': 'OK', 'message': 'Справился с вводом одной цифры'}


async def update_done_status(deadline_status_id: int):
    deadline_status = await DeadlineStatus.objects.aget(pk=deadline_status_id)
    status = deadline_status.is_done
    deadline_status.is_done = not status
    await deadline_status.asave()


async def update_deadline_text(deadline_status_id: int, deadline_text: str):
    deadline = await Deadline.objects.filter(deadline_status_id=deadline_status_id)
    deadline.text = deadline_text
    await deadline.asave()
