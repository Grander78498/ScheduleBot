"""
Просто полезные функции и один класс-перечисление
"""


from .imports import *
from aiogram.utils.deep_linking import create_start_link
from aiogram import Bot

# telethon_event_loop = asyncio.new_event_loop()


OFFSET = 3


class EventType(Enum):
    QUEUE = 1
    DEADLINE = 2
    SANTA = 3


async def check_time(time, year, month, day, user_id):
    '''Функция для проверки корректности времени'''
    check_time_format = bool(re.fullmatch(r'(([01]\d)|(2[0-3])):[0-5]\d', time))
    if not check_time_format:
        return 'TimeError'
    user = await TelegramUser.objects.aget(pk=user_id)
    tz = user.tz
    tz = str(tz).rjust(2, '0') + '00'
    current_date = timezone.now()
    given_date = datetime.strptime(
        f"{year}-{str(month).rjust(2, '0')}-{str(day).rjust(2, '0')} {time}+{tz}",
        "%Y-%m-%d %H:%M%z")
    if given_date >= current_date or (current_date - given_date).total_seconds() <= 60:
        return "It's okay it's fine"
    return "EarlyQueueError"


def check_timezone(tz):
    """
    Функция проверки корректности временной зоны
    """
    return bool(re.fullmatch(r'-?\d', tz))


def check_text(text: str, max_len):
    if len(text.encode('utf-8')) >= max_len:
        return {'status': 'NO', 'message': 'Слишком длинное название - повторите ввод'}
    return {'status': 'OK'}


async def get_group_link(group_id: int):
    group = await TelegramGroup.objects.aget(tg_id=group_id)
    if group.thread_id is None:
        link = f"https://t.me/c/{int(str(group_id)[4:])}/1"
    else:
        link = f"https://t.me/c/{int(str(group_id)[4:])}/{group.thread_id}"
    return link


async def get_queue_message_link(queue_id: int, user_id: int):
    queue = await Queue.objects.aget(pk=queue_id)
    group = await TelegramGroup.objects.aget(pk=queue.group_id)
    if user_id not in [user.pk async for user in group.telegramuser_set.all()]:
        return ""
    message = await Message.objects.aget(event_id=queue.pk, chat_id=group.pk)
    link = f"https://t.me/c/{int(str(queue.group_id)[4:])}/{message.message_id}"
    return link


async def get_event_type_by_id(event_id) -> EventType:
    event = await Event.objects.select_related('queue', 'deadline').aget(pk=event_id)
    try:
        getattr(event, 'queue')
        return EventType.QUEUE
    except Exception:
        return EventType.DEADLINE


async def get_message_id(event_id: int, chat_id: int):
    message, created = await Message.objects.aget_or_create(event_id=event_id, chat_id=chat_id)
    if created:
        return None
    return message.message_id


async def get_queue_link(queue_id: int, bot: Bot):
    # return "https://t.me/{}?start=queue_add{}".format(bot_name, encrypt(queue_id))
    return await create_start_link(bot, str(queue_id), encode=True)


async def get_stats():
    user_count = await TelegramUser.objects.acount()
    queue_count = await Queue.objects.acount()
    deadline_count = await Deadline.objects.acount()
    group_count = await TelegramGroup.objects.acount()

    res_string = ""
    res_string += f"Количество пользователей: {user_count}\n"
    res_string += f"Количество групп: {group_count}\n"
    res_string += f"Количество созданных очередей: {queue_count}\n"
    res_string += f"Количество созданных дедлайнов: {deadline_count}\n"

    return res_string
