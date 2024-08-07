from .imports import *


async def check_admin(admin_id: int):
    groups = []
    async for group in TelegramGroup.objects.filter(telegramuser=admin_id, groupmember__is_admin=True):
        groups.append(group)
    return groups


async def get_user_groups(user_id: int):
    groups = []
    async for group_mem in GroupMember.objects.select_related("groups").filter(user_id=user_id):
        groups.append((group_mem.groups, group_mem.is_admin))
    return groups


async def get_group_admin(group_id: int):
    admin = (await TelegramGroup.objects.select_related("main_admin").aget(pk=group_id)).main_admin
    return admin.pk, admin.full_name


async def delete_group(group_id: int):
    group = await TelegramGroup.objects.aget(tg_id=group_id)
    await group.adelete()


async def delete_group_member(group_id: int, user_id: int):
    member = await GroupMember.objects.aget(user_id=user_id, groups_id=group_id)
    await member.adelete()


async def check_main_admin(group_id: int, admin_id: int):
    group = await TelegramGroup.objects.aget(tg_id=group_id)
    if group.main_admin_id == admin_id:
        return {"status": "OK"}
    else:
        return {"status": "ERROR", "message": "Ты здесь никто, ты - огузок!!!"}


async def check_possible_main_admin(group_id: int, admin_id: int):
    is_admin = (await GroupMember.objects.aget(user_id=admin_id, groups_id=group_id)).is_admin
    if is_admin:
        return {"status": "OK"}
    else:
        return {"status": "ERROR", "message": "Пытаешься назначить огузка шефом???????"}