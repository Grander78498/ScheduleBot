import aiogram
from aiogram import Bot, types
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from emoji import emojize

from bot.callbacks import SwapCallback, DeadLineAcceptCallback, EditDeadline, EditDeadPagination, \
    AdminQueueSelectCallback, QueuePagination, SimpleQueueSelectCallback
from queue_api import api
from queue_api.api import EventType


async def send_swap_request(message: types.Message, second_member_id: str, from_user_id, state: FSMContext, bot: Bot):
    res = (await state.get_data())["swap"]
    queueID = res["queueID"]
    await bot.delete_message(chat_id=from_user_id, message_id=res["first_m"])
    await bot.delete_message(chat_id=from_user_id, message_id=res["second_m"])
    await state.clear()
    result = await api.get_user_id(await api.get_queue_member_id(queueID, from_user_id), second_member_id)
    if result["status"] != "OK":
        await message.answer(result["message"])
    else:
        mess_lichka = await message.answer(result["message"])
        try:
            mes = await bot.send_message(chat_id=result["user_id"],
                                         text="{} (место - {}) отправил(-а) запрос на обмен местами в очереди {}. Ваше текущее место - {}".format(
                                             result['first_name'], result['first_position'], result['queue_name'],
                                             result['second_position']))
            builder = InlineKeyboardBuilder()
            builder.button(text="Отклонить", callback_data=SwapCallback(message_type="Deny",
                                                                        first_user_id=await api.get_queue_member_id(
                                                                            queueID, from_user_id),
                                                                        first_tg_user_id=from_user_id, queueId=queueID,
                                                                        second_user_id=int(second_member_id),
                                                                        message2_id=mes.message_id,
                                                                        message1_id=mess_lichka.message_id))
            builder.button(text="Принять", callback_data=SwapCallback(message_type="Accept",
                                                                      first_user_id=await api.get_queue_member_id(
                                                                          queueID, from_user_id),
                                                                      first_tg_user_id=from_user_id, queueId=queueID,
                                                                      second_user_id=int(second_member_id),
                                                                      message2_id=mes.message_id,
                                                                      message1_id=mess_lichka.message_id))
            await bot.edit_message_reply_markup(chat_id=result["user_id"], message_id=mes.message_id,
                                                reply_markup=builder.as_markup())
            await api.handle_request(await api.get_queue_member_id(queueID, from_user_id), second_member_id,
                                     mess_lichka.message_id, mes.message_id)
            await api.add_request_timer(from_user_id, result["user_id"], mess_lichka.message_id, mes.message_id,
                                        queueID)

        except aiogram.exceptions.TelegramForbiddenError:
            await message.answer(
                "Не удалось отправить запрос - пользователь {} заблокировал бота".format(result['second_name']))


async def short_cut(message: types.Message, state: FSMContext):
    builder = InlineKeyboardBuilder()
    data = await state.get_data()
    if data["event_type"] == EventType.QUEUE:
        builder.button(text="Сейчас", callback_data="now")
        builder.button(text="Через час", callback_data="one_hour")
        builder.button(text="Сегодня", callback_data="today")
        builder.button(text="Завтра", callback_data="tomorrow")
        builder.button(text="Задать самостоятельно", callback_data="custom")
    elif data["event_type"] == EventType.DEADLINE:
        builder.button(text="Через неделю", callback_data="week")
        builder.button(text="Через 2 недели", callback_data="2week")
        builder.button(text="Через месяц", callback_data="one_month")
        builder.button(text="Через полгода", callback_data="half_year")
        builder.button(text="Задать самостоятельно", callback_data="custom")
    builder.adjust(2)
    await message.answer("Выберите время", reply_markup=builder.as_markup())


async def putInDb(message: types.Message, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    try:
        await state.clear()
        if "RemoveMessageyear" in data:
            del data["RemoveMessageyear"]
        if "RemoveMessagemonth" in data:
            del data["RemoveMessagemonth"]
        if "RemoveMessageday" in data:
            del data["RemoveMessageday"]
        if "renameQueue" in data:
            del data["renameQueue"]
        data["creator_id"] = message.chat.id
    except Exception:
        print("Error")
    builder = InlineKeyboardBuilder()
    if data["event_type"] == EventType.QUEUE:
        thread_id, date, queue_id, notif_date = await api.create_queue_or_deadline(data)
        builder.button(text="Создать очередь", callback_data="add_queue")
        builder.button(text="Вывести существующие очереди", callback_data="print_queue")
        builder.button(text="Запросить перемещение в очереди", callback_data="swap")
        builder.adjust(1)
        await message.answer("Очередь была создана", reply_markup=builder.as_markup())
        mes = await bot.send_message(chat_id=data['group_id'], message_thread_id=thread_id,
                                     text=api.print_queue_message(data['text'], date, notif_date))
        await api.update_message_id(queue_id, mes.message_id, data['group_id'])
        await api.create_queue_tasks(queue_id, data["group_id"])
    else:
        builder.button(text="Создать напоминание", callback_data="add_deadline")
        builder.button(text="Вывести существующие напоминания", callback_data="print_deadline")
        builder.adjust(1)
        thread_id, date, deadline_id, notif_date = await api.create_queue_or_deadline(data)
        if data["deadline_roots"]:
            await message.answer("Дедлайн создан", reply_markup=builder.as_markup())
            mes = await bot.send_message(chat_id=data['group_id'], message_thread_id=thread_id,
                                         text=api.print_deadline_message(data['text'], date))
            await api.update_message_id(deadline_id, mes.message_id, data['group_id'])
            await api.create_queue_tasks(deadline_id, data["group_id"])
        else:
            res = await api.create_deadline_request(message.from_user.id, data['group_id'])
            if res['status'] == 'ERROR':
                await message.answer(res['message'])
            else:
                await message.answer("Так как вы не являетесь админом этой группы, запрос послан одному из админов. Ожидайте его решения",reply_markup=builder.as_markup())
                admin_id, admin_full_name = await api.get_group_admin(data['group_id'])
                builder_admin = InlineKeyboardBuilder()
                m = await bot.send_message(chat_id=admin_id, text="Пользователь {} отправил вам ({}) дедлайн {} в группе {}".format(message.from_user.full_name, admin_full_name, data["text"], (await api.get_group_name(data["group_id"]))))
                builder_admin.button(text="Отклонить", callback_data=DeadLineAcceptCallback(deadline_id=deadline_id, user_id=message.from_user.id, solution=False, message_id=m.message_id))
                builder_admin.button(text="Принять", callback_data=DeadLineAcceptCallback(deadline_id=deadline_id, user_id=message.from_user.id, solution=True, message_id=m.message_id))
                await bot.edit_message_reply_markup(chat_id=admin_id, message_id=m.message_id,
                                                    reply_markup=builder_admin.as_markup())


async def deadline_list_return(user_id, messageID, bot: Bot):
    res = await api.get_deadlines(user_id, 0, True)
    builder = InlineKeyboardBuilder()
    r = await bot.edit_message_text(text=res["message"], chat_id=user_id,
                                    message_id=messageID)
    if res["status"]!="OK":
        builder.button(text="Создать напоминание", callback_data="add_deadline")
        builder.button(text="Вывести существующие напоминания", callback_data="print_deadline")
        builder.button(text="Управление напоминаниями", callback_data="edit_deadline")
        builder.adjust(1)
        await bot.edit_message_reply_markup(chat_id=user_id, message_id=messageID, reply_markup=builder.as_markup())
    else:
        has_next = res['has_next']
        len_d = 0
        for dead_id, _ in res["deadline_list"]:
            builder.button(text=("{}".format(len_d+1)), callback_data=EditDeadline(deadline_id=dead_id, message_id=r.message_id))
            len_d+=1
        buttons = [5 for _ in range(len_d//5)]
        if len_d%5!=0:
            buttons.append(len_d%5)
        if has_next:
            builder.button(text=emojize(":right_arrow:"), callback_data=EditDeadPagination(offset = api.OFFSET, message_id=r.message_id))
            buttons.append(1)
        builder.adjust(*buttons)
        await bot.edit_message_reply_markup(chat_id=user_id, message_id=r.message_id, reply_markup=builder.as_markup())


async def queue_return(user_id, messageID, bot: Bot):
    _dict = await api.get_all_queues(user_id, 0, False)
    status = _dict["status"]
    r = await bot.edit_message_text(text=_dict["message"], chat_id=user_id,
                                    message_id=messageID, parse_mode='MarkdownV2')
    if status!="OK":
        await bot.edit_message_text(chat_id=user_id, message_id=messageID, text=_dict["message"])
        uilder = InlineKeyboardBuilder()
        await bot.edit_message_reply_markup(chat_id=user_id, message_id=messageID,
                                            reply_markup=uilder.as_markup())
    else:
        lenq = len(_dict["data"])
        has_next = _dict["has_next"]
        queueList = [queue["id"] for queue in _dict["data"]]
        names = [queue["name"] for queue in _dict["data"]]
        is_creators = [queue["is_creator"] for queue in _dict["data"]]
        st = _dict["message"]
        builder = InlineKeyboardBuilder()
        for i in range(lenq):
            builder.button(text="{}".format(i + 1),
                           callback_data= (AdminQueueSelectCallback(queueID=queueList[i], delete_message_id=r.message_id, queueName=names[i])) if is_creators[i] else SimpleQueueSelectCallback(queueID=queueList[i], delete_message_id=r.message_id, queueName=names[i]))
        buttons = [5 for _ in range(lenq//5)]
        if lenq%5!=0:
            buttons.append(lenq%5)
        if has_next:
            builder.button(text=emojize(":right_arrow:"), callback_data=QueuePagination(offset = api.OFFSET, message_id=r.message_id))
            buttons.append(1)
        builder.adjust(*buttons)
        await bot.edit_message_reply_markup(chat_id=user_id, message_id=r.message_id,
                                            reply_markup=builder.as_markup())
