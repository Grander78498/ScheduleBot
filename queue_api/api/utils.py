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


def print_date_diff(date1, date2) -> str:
    # от 1 минуты до 1 часа - в минутах
    # от 1 часа до 6 часов - в 30 минутах
    # от 6 часов до суток - в часах
    # от суток до двух = завтра
    # от двух суток до трёх = послезавтра
    # всё остальное - через недели и дни
    if date2 < date1:
        return '0 секунд'

    diff = date2 - date1
    if diff.days == 0:
        if diff.seconds < 60:
            ending = ""
            if diff.seconds % 10 == 1 and diff.seconds != 11:
                ending = "у"
            elif diff.seconds % 10 in range(2, 5) and diff.seconds not in range(12, 15):
                ending = "ы"

            return f"{diff.seconds} секунд{ending}"
        elif 60 <= diff.seconds < 3600:
            minutes = diff.seconds // 60
            ending = ""
            if minutes % 10 == 1 and minutes != 11:
                ending = "у"
            elif minutes % 10 in range(2, 5) and minutes not in range(12, 15):
                ending = "ы"

            if diff.seconds < 60 * 10:
                seconds = diff.seconds % 60
                seconds_ending = ""
                if seconds % 10 == 1 and seconds != 11:
                    seconds_ending = "у"
                elif seconds % 10 in range(2, 5) and seconds not in range(12, 15):
                    seconds_ending = "ы"
                return f"{minutes} минут{ending} и {seconds} секунд{seconds_ending}"

            return f"{minutes} минут{ending}"
        elif 3600 <= diff.seconds < 24 * 3600:
            hours = diff.seconds // 3600
            ending = "ов"
            if hours % 10 == 1 and hours != 11:
                ending = ""
            elif hours % 10 in range(2, 5) and hours not in range(12, 15):
                ending = "а"

            if diff.seconds < 3600 * 6:
                minutes = (diff.seconds // 60) % 60
                if minutes != 0:
                    minutes_ending = ""
                    if minutes % 10 == 1 and minutes != 11:
                        minutes_ending = "у"
                    elif minutes % 10 in range(2, 5) and minutes not in range(12, 15):
                        minutes_ending = "ы"
                    return f"{hours} час{ending} и {minutes} минут{minutes_ending}"

            return f"{hours} час{ending}"
    elif 1 <= diff.days < 2:
        return "завтра"
    elif 2 <= diff.days < 3:
        return f"послезавтра"
    elif diff.days >= 3:
        weeks = diff.days // 7
        days = diff.days % 7
        week_ending = "ь"
        if weeks % 10 == 1 and weeks != 11:
            week_ending = "ю"
        elif weeks % 10 in range(2, 5) and weeks not in range(12, 15):
            week_ending = "и"

        day_ending = "ней"
        if days % 10 == 1:
            day_ending = "ень"
        elif days % 10 in range(2, 5) and days not in range(12, 15):
            day_ending = "ня"

        if weeks == 0:
            return f"{days} д{day_ending}"
        elif days == 0:
            return f"{weeks} недел{week_ending}"
        else:
            return f"{weeks} недел{week_ending} и {days} д{day_ending}"


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
        return {'status': 'NO', 'message': 'Насрал много байтов - повтори ввод названия'}
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
    event = await Event.objects.aget(pk=event_id)
    if 'queue' in dir(event):
        return EventType.QUEUE
    return EventType.DEADLINE


async def get_message_id(event_id: int, chat_id: int):
    message, created = await Message.objects.aget_or_create(event_id=event_id, chat_id=chat_id)
    if created:
        return None
    return message.message_id


async def get_queue_link(queue_id: int, bot: Bot):
    # return "https://t.me/{}?start=queue_add{}".format(bot_name, encrypt(queue_id))
    return await create_start_link(bot, str(queue_id), encode=True)

async def check_user_in_queue(user_id, queue_id):
    try:
        queue = await Queue.objects.aget(pk=queue_id)
    except Exception as a:
        return {"status":"ERROR","message":"Очередь сожрала Скворцова"}
    try:
        mem = await QueueMember.objects.aget(queue_id=queue_id, user_id=user_id)
        return {"status":"OK"}
    except Exception as b:
        return {"status":"ERROR","message":"Тебя выкинули, либо лох, либо хорош"}
