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
    try:
        first_period_task = await PeriodicTask.objects.aget(name=f"{group.pk} begin")
        second_period_task = await PeriodicTask.objects.aget(name=f"{group.pk} end")
        await first_period_task.adelete()
        await second_period_task.adelete()
    except Exception:
        pass
    await group.adelete()


async def delete_group_member(group_id: int, user_id: int):
    from bot.utils import send_message_to_new_main_admin

    member = await GroupMember.objects.aget(user_id=user_id, groups_id=group_id)
    group = await TelegramGroup.objects.aget(pk=group_id)
    await member.adelete()
    if group.main_admin_id == user_id:
        new_main_admin = (await GroupMember.objects.select_related('user')
                          .filter(groups_id=group_id, is_admin=True).order_by('?').afirst()).user
        group.main_admin = new_main_admin
        await send_message_to_new_main_admin(new_main_admin.pk, new_main_admin.full_name, group_id,
                                             group.name, group.thread_id)
        await group.asave()


async def check_main_admin(group_id: int, admin_id: int):
    group = await TelegramGroup.objects.aget(tg_id=group_id)
    if group.main_admin_id == admin_id:
        return {"status": "OK"}
    else:
        return {"status": "ERROR", "message": "Вы не главный админ, не притворяйтесь"}


async def check_possible_main_admin(group_id: int, admin_id: int):
    try:
        is_admin = (await GroupMember.objects.aget(user_id=admin_id, groups_id=group_id)).is_admin
        if is_admin:
            return {"status": "OK"}
        else:
            return {"status": "ERROR", "message": "Нельзя назначить главным админом не админа"}
    except Exception:
        return {"status": "ERROR", "message": "Нельзя назначить главным админом человека со стороны"}


async def get_group_name(group_id: int):
    group = await TelegramGroup.objects.aget(tg_id=group_id)
    return group.name


async def get_thread_id(group_id: int):
    return (await TelegramGroup.objects.aget(pk=group_id)).thread_id

