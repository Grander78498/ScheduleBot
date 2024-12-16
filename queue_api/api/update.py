"""
Функции, которые обновляют значения полей в различных таблицах
"""


from .imports import *
from .utils import check_timezone
from .deadline_management import print_deadline_message


async def update_message_id(event_id: int | None, message_id: int, chat_id: int):
    if event_id is None:
        santa = await Santa.objects.select_related('event_ptr').aget(group_id=chat_id)
        event = santa.event_ptr
    else:
        event = await Event.objects.aget(pk=event_id)
    message, _ = await Message.objects.aget_or_create(event=event, chat_id=chat_id)
    message.message_id = message_id
    await message.asave()


async def update_started(tg_id: int, full_name: str, started: bool):
    user, _ = await TelegramUser.objects.aget_or_create(pk=tg_id)
    user.full_name = full_name
    user.is_started = started
    await user.asave()


async def change_topic(group_id: int, thread_id: int):
    await TelegramGroup.objects.filter(pk=group_id).aupdate(thread_id=thread_id)


async def change_tz(user_id: int, tz: str):
    if check_timezone(tz):
        tz = int(tz) + 3
    else:
        return {'status': 'NO', 'message': 'Опять саратовское время вводишь??? Пробуй ещё'}

    await TelegramUser.objects.filter(pk=user_id).aupdate(tz=tz)
    return {'status': 'OK', 'message': 'Часовой пояс был успешно изменён'}


async def update_done_status(deadline_status_id: int):
    deadline_status = await DeadlineStatus.objects.aget(pk=deadline_status_id)
    status = deadline_status.is_done
    deadline_status.is_done = not status
    await deadline_status.asave()


async def update_deadline_text(deadline_status_id: int, deadline_text: str):
    deadline = await Deadline.objects.aget(deadlinestatus__id=deadline_status_id)
    if deadline.text == deadline_text:
        return {"status": 'ERROR', 'message': 'Ну и зачем вводить то же самое название?'}
    deadline.text = deadline_text
    message_id = (await Message.objects.filter(event_id=deadline.pk).afirst()).message_id
    text = print_deadline_message(deadline_text, deadline.date.strftime('%d/%m/%Y, %H:%M:%S'))
    chat_id = deadline.group_id
    await deadline.asave()
    return {"status": 'OK', "data": (message_id, text, chat_id)}
