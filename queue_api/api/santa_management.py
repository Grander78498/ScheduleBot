from .imports import *
from .celery_calls import send_render_task


async def add_user_to_santa(tg_id: int, full_name: str):
    try:
        santa = await Santa.objects.all()
    except:
        return {"error": "Вы не можете добавиться в клуб Тайного Санты, поскольку набор уже завершён"}
    user, user_created = await TelegramUser.objects.aget_or_create(pk=tg_id)
    user.full_name = full_name
    _, created = await SantaMember.objects.aget_or_create(user=user, santa=santa)
    if user_created:
        return {"started": False}

    # if created:
    #     await send_render_task(1, False)

    return {"started": user.is_started, "santa_member": not created}


async def add_user_to_grinch(tg_id: int):
    try:
        santa_member = await SantaMember.objects.aget(user_id=tg_id)

        await santa_member.adelete()
        return 'Correct'
    except Exception:
        return 'Incorrect'
    

async def get_pairs(group_id: int):
    santa_members = await SantaMember.objects.all().select_related('user__full_name')
    copied_members = await SantaMember.objects.all().order_by('?')
    while all(el1.user_id != el2.user_id for (el1, el2) in zip(santa_members, copied_members)):
        copied_members = await SantaMember.objects.all().order_by('?')
    return [
        {
            "id1": el1.user_id,
            "name1": el1.user.full_name,
            'id2': el2.user_id,
            'name2': el2.user.full_name
        }
    ]