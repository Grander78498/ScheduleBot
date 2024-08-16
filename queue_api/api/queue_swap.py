"""
Функции, которые вызываются при обработке запроса на перемещение в очереди
"""


from .imports import *
from .queue_management import get_queue_position
from .celery_calls import send_render_task


async def get_user_id(first_member_id: int, second_member_id: str):
    first = await QueueMember.objects.aget(pk=first_member_id)
    queue = await Queue.objects.aget(pk=first.queue_id)
    try:
        second_member_id = int(second_member_id)
    except Exception:
        return {'status': 'Incorrect input', 'message': 'Ты долбаёб блять хули ты хуйню какую-то пихаешь??????'}

    if second_member_id not in [member.pk async for member in queue.queuemember_set.all()]:
        return {'status': 'Wrong queue', 'message': 'Хули ты в неправильную очередь лезешь уёбок????????'}
    if second_member_id == first_member_id:
        return {'status': 'Self chosen', 'message': 'Самолайк == самоотсос'}
    second = await QueueMember.objects.aget(pk=second_member_id)
    return {'status': 'OK', 'user_id': second.user_id, 'message': 'Ваш запрос был успешно отправлен',
            'first_name': (await TelegramUser.objects.aget(pk=first.user_id)).full_name, 'queue_name': queue.text,
            'first_position': await get_queue_position(first.pk), 'second_position': await get_queue_position(second.pk),
            'second_name': (await TelegramUser.objects.aget(pk=second.user_id)).full_name}


async def swap_places(first_member_id: int, second_member_id: int):
    first = await QueueMember.objects.aget(pk=first_member_id)
    second = await QueueMember.objects.aget(pk=second_member_id)
    first.pk, second.pk = second.pk, first.pk
    await first.asave()
    await second.asave()
    await send_render_task(first.queue_id, False)


async def handle_request(first_member_id: int, second_member_id: str, first_message_id: int, second_message_id: int):
    first_member = await QueueMember.objects.aget(pk=first_member_id)
    second_member = await QueueMember.objects.aget(pk=second_member_id)
    await SwapRequest.objects.acreate(first_member=first_member, second_member=second_member, first_message_id=first_message_id, second_message_id=second_message_id)


async def remove_request(first_id: int, second_id: int, queue_id: int):
    first_member = await QueueMember.objects.aget(user_id=first_id, queue_id=queue_id)
    second_member = await QueueMember.objects.aget(user_id=second_id, queue_id=queue_id)
    await SwapRequest.objects.filter(first_member=first_member, second_member=second_member).adelete()
    return second_member.pk


async def check_requests(user_id: int, queue_id: int):
    queue_member = await QueueMember.objects.aget(user_id=user_id, queue_id=queue_id)
    has_in_requests = (await queue_member.second_member.acount()) != 0
    has_out_requests = (await queue_member.first_member.acount()) != 0
    return {'in': has_in_requests, 'out': has_out_requests}


async def remove_all_in_requests(member_id: int):
    queue_member = await QueueMember.objects.aget(pk=member_id)
    all_in_requests = queue_member.second_member.all()
    result = [{"first_member": (await QueueMember.objects.aget(pk=req.first_member_id)).user_id,
               "first_message_id": req.first_message_id,
               "second_message_id": req.second_message_id} async for req in all_in_requests]
    await all_in_requests.adelete()
    return result
