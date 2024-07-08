from .models import *


async def add_admin(group_id: int, admins: list[int], group_name: str, thread_id: int):
    group, _ = await TelegramGroup.objects.aget_or_create(tg_id=group_id, name=group_name, thread_id=thread_id)
    for admin in admins:
        user, _ = await TelegramUser.objects.aget_or_create(tg_id=admin, is_admin=True)
        await user.groups.aadd(group)
        await user.asave()