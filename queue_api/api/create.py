from .imports import *
from .utils import print_date_diff, EventType


async def add_admin(group_id: int, admins: list[int], names: list[str], group_name: str, thread_id: int):
    for admin, name in zip(admins, names):
        await add_user_to_group(group_id, admin, name, True, group_name=group_name, thread_id=thread_id)


async def add_user_to_group(group_id: int,
                            user_id: int, user_fullname: str, is_admin: bool = False, group_name = None, thread_id = None):
    if group_name is None:
        group = await TelegramGroup.objects.aget(tg_id=group_id)
    else:
        group, _ = await TelegramGroup.objects.aget_or_create(tg_id=group_id, name=group_name, thread_id=thread_id)
    try:
        user, _ = await TelegramUser.objects.aget_or_create(tg_id=user_id, full_name=user_fullname)
        await user.groups.aadd(group, through_defaults={"is_admin": is_admin})
        await user.asave()
    except Exception as e:
        print(e)


async def create_queue_or_deadline(data_dict):
    message = data_dict['text']
    group_id = data_dict['group_id']
    creator_id = data_dict['creator_id']
    creator = await TelegramUser.objects.aget(pk=creator_id)
    tz = creator.tz
    tz = str(tz).rjust(2, '0') + '00'
    if 'sec' in data_dict:
        date = datetime.strptime(
            f"{data_dict['year']}-{str(data_dict['month']).rjust(2, '0')}-{str(data_dict['day']).rjust(2, '0')} {data_dict['hm']}:{str(data_dict['sec']).rjust(2, '0')}+{tz}",
            "%Y-%m-%d %H:%M:%S%z")
    date = datetime.strptime(
        f"{data_dict['year']}-{str(data_dict['month']).rjust(2, '0')}-{str(data_dict['day']).rjust(2, '0')} {data_dict['hm']}+{tz}",
        "%Y-%m-%d %H:%M%z")
    group = await TelegramGroup.objects.aget(pk=group_id)
    is_queue = data_dict["event_type"] == EventType.QUEUE
    if is_queue:
        queue = await Queue.objects.acreate(message=message, date=date, creator=creator, group=group)
        event_id = queue.pk
    else:
        deadline = await Deadline.objects.acreate(message=message, date=date, creator=creator, group=group)
        event_id = deadline.pk
    time_diff = date - timezone.now()
    if time_diff < timedelta(minutes=2):
        return ((await TelegramGroup.objects.aget(pk=group_id)).thread_id,
                print_date_diff(timezone.now(), date), event_id, "")

    if time_diff >= timedelta(hours=2):
        queue_notif_date = date - timedelta(hours=1)
    else:
        queue_notif_date = date - 0.5 * time_diff

    return ((await TelegramGroup.objects.aget(pk=group_id)).thread_id,
            print_date_diff(timezone.now(), date), event_id, print_date_diff(timezone.now(), queue_notif_date))


async def save_user(tg_id: int, full_name: str):
    user, created = await TelegramUser.objects.aget_or_create(pk=tg_id, full_name=full_name)
    user.is_started = True
    await user.asave()
