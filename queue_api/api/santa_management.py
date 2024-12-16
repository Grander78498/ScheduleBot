from .imports import *


async def add_user_to_queue(santa_id: int, tg_id: int, full_name: str):
    try:
        queue = await Santa.objects.aget(pk=santa_id)
    except:
        return {"error": "Вы не можете добавиться в эту очередь, поскольку она удалена"}
    user, user_created = await TelegramUser.objects.aget_or_create(pk=tg_id)
    user.full_name = full_name
    _, created = await QueueMember.objects.aget_or_create(user=user, queue=queue)
    if user_created:
        return {"started": False}

    if created:
        await send_render_task(queue_id, False)

    return {"started": user.is_started, "queue_member": not created}