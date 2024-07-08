from .models import *


def add_admin(group_id: int, admins: list[int], group_name: str, thread_id: int):
    group = TelegramGroup.objects.create(tg_id=group_id, name=group_name, thread_id=thread_id)
    for admin in admins:
        user = TelegramUser(tg_id=admin)
        user.groups.add(group)
        user.save()