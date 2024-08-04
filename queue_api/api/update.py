from .imports import *
from .utils import check_timezone


async def update_message_id(event_id: int, message_id: int):
    await Event.objects.filter(pk=event_id).aupdate(message_id=message_id)


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
