from .imports import *
from .celery_calls import send_render_task


async def add_user_to_santa(tg_id: int, full_name: str, group_id: int):
    try:
        santa = await Santa.objects.aget(group_id=group_id)
    except:
        return {"error": "Вы не можете добавиться в клуб Тайного Санты, поскольку набор уже завершён"}
    user, user_created = await TelegramUser.objects.aget_or_create(pk=tg_id)
    user.full_name = full_name
    _, created = await SantaMember.objects.aget_or_create(user=user, santa=santa)
    if user_created:
        return {"started": False}

    return {"started": user.is_started, "santa_member": not created}


async def update_santa(group_id: int):
    santa = await Santa.objects.select_related('event_ptr').aget(group_id=group_id)
    count_members = await SantaMember.objects.filter(santa=santa).acount()
    message, _ = await Message.objects.aget_or_create(event=santa.event_ptr, chat_id=group_id)
    return message.message_id, count_members


async def add_user_to_grinch(tg_id: int, group_id: int):
    try:
        santa = await Santa.objects.aget(group_id=group_id)
        santa_member = await SantaMember.objects.aget(user_id=tg_id, santa=santa)

        await santa_member.adelete()
        return 'Correct'
    except Exception:
        return 'Incorrect'
    

async def get_pairs(group_id: int):
    santa = await Santa.objects.aget(group_id=group_id)
    santa_members = [member async for member in SantaMember.objects.filter(santa=santa).select_related('user')]
    copied_members = [member async for member in SantaMember.objects.filter(santa=santa).order_by('?').select_related('user')]
    while any(el1.user_id == el2.user_id for (el1, el2) in zip(santa_members, copied_members)):
        copied_members = [member async for member in SantaMember.objects.filter(santa=santa).order_by('?').select_related('user')]
    return [
        {
            "id1": el1.user_id,
            "name1": el1.user.full_name,
            'id2': el2.user_id,
            'name2': el2.user.full_name
        }
        for (el1, el2) in zip(santa_members, copied_members)
    ]