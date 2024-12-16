import aiogram
from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from emoji import emojize

from bot.callbacks import *
from queue_api import api
from queue_api.api import EventType
from django.conf import settings
from .bot import bot



async def send_swap_request(message: types.Message, second_member_id: str, from_user_id, state: FSMContext):
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


async def send_christmas(callback_data: ChristmasGroupSelectCallback):
    builder = InlineKeyboardBuilder()
    builder.button(text="Санта", callback_data="christmas")
    builder.button(text="Гринч", callback_data="no_christmas")
    a = await bot.send_message(chat_id=callback_data.groupID, text="НОВЫЙ ГОД БУДЕТ. Вступите в клуб Угольных носков. Количество участников сейчас 0", reply_markup=builder.as_markup())
    await api.update_message_id(None, a.message_id,callback_data.groupID)



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


async def putInDb(message: types.Message, state: FSMContext) -> None:
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
    match data['event_type']:
        case EventType.QUEUE:
            thread_id, date, queue_id, notif_date = await api.create_event(data)
            builder.button(text="Создать очередь", callback_data="add_queue")
            builder.button(text="Вывести существующие очереди", callback_data="print_queue")
            builder.button(text="Запросить перемещение в очереди", callback_data="swap")
            builder.adjust(1)
            await message.answer("Очередь была создана", reply_markup=builder.as_markup())
            mes = await bot.send_message(chat_id=data['group_id'], message_thread_id=thread_id,
                                        text=api.print_queue_message(data['text'], date, notif_date))
            await api.update_message_id(queue_id, mes.message_id, data['group_id'])
            await api.create_queue_tasks(queue_id, data["group_id"])
        case EventType.DEADLINE:
            builder.button(text="Создать напоминание", callback_data="add_deadline")
            builder.button(text="Вывести существующие напоминания", callback_data="print_deadline")
            builder.adjust(1)
            thread_id, date, deadline_id, notif_date = await api.create_event(data)
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
        case EventType.SANTA:
            pass
        case _:
            ...


async def deadline_list_return(user_id, messageID):
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


async def queue_return(user_id, messageID):
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


async def render_queue(queue_id: int, private: bool):
    group_id, queue, message_list = await api.print_queue(queue_id, private, bot)
    builder = InlineKeyboardBuilder()
    builder.button(text="Встать в очередь", callback_data=QueueIDCallback(queueID=queue_id))
    builder.button(text="Выйти из очереди", callback_data=RemoveMyself(queueID=queue_id))
    builder.button(text="Узнать свою позицию в очереди", callback_data=FindMyself(queueID=queue_id))
    builder.adjust(1)
    for queue_message_id in message_list:
        try:
            await bot.edit_message_text(text=queue, chat_id=group_id, message_id=queue_message_id,
                                        reply_markup=builder.as_markup(), parse_mode='MarkdownV2')
        except Exception as ex:
            print(ex)
            print(f"Group id: {group_id}; message_id={queue_message_id}")


async def send_notification(queue_id, thread_id, group_id, message):
    mess_id = await api.get_message_id(queue_id, group_id)
    a = await bot.send_message(chat_id=group_id, text=message, message_thread_id=thread_id)
    await api.update_message_id(queue_id, a.message_id, group_id)


async def send_ready(event_id, thread_id, group_id):
    builder = InlineKeyboardBuilder()
    queue_message_id = await api.get_message_id(event_id, group_id)
    try:
        await bot.delete_message(chat_id=group_id, message_id=queue_message_id)
    except Exception:
        pass
    event_type = await api.get_event_type_by_id(event_id)
    if event_type == EventType.QUEUE:
        builder.button(text="Встать в очередь", callback_data=QueueIDCallback(queueID=event_id))
        builder.button(text="Выйти из очереди", callback_data=RemoveMyself(queueID=event_id))
        builder.button(text="Узнать свою позицию в очереди", callback_data=FindMyself(queueID=event_id))
        builder.adjust(1)
        _, message, _ = await api.print_queue(event_id, False, bot)
        mess = await bot.send_message(text=message, chat_id=group_id, message_thread_id=thread_id,
                                      reply_markup=builder.as_markup(), parse_mode='MarkdownV2')
        await api.update_message_id(event_id, mess.message_id, group_id)
    else:
        message = await api.print_deadline(event_id)
        await api.delete_deadline(event_id)
        await bot.send_message(text=message, chat_id=group_id, message_thread_id=thread_id,
                                      reply_markup=builder.as_markup(), parse_mode='MarkdownV2')


async def update_deadline_info(res, user_id, message_id):
    builder = InlineKeyboardBuilder()
    if res["status"]!="OK":
        builder.button(text="Создать напоминание", callback_data="add_deadline")
        builder.button(text="Вывести существующие напоминания", callback_data="print_deadline")
        builder.adjust(1)
        await bot.edit_message_text(chat_id=user_id, text=emojize(res["message"]), message_id=message_id)
        await bot.edit_message_reply_markup(chat_id=user_id, message_id=message_id, reply_markup=builder.as_markup())
    else:
        has_next = res['has_next']
        await bot.edit_message_text(chat_id=user_id,text=emojize(res["message"]), message_id=message_id)
        len_d = 0
        for dead_id, is_done in res["deadline_list"]:
            builder.button(text=("{}".format(len_d + 1)), callback_data=CanbanDesk(deadline_status_id=dead_id, is_done=is_done, message_id=message_id))
            len_d += 1
        buttons = [5 for _ in range(len_d // 5)]
        if len_d % 5 != 0:
            buttons.append(len_d % 5)
        if has_next:
            builder.button(text=emojize(":right_arrow:"), callback_data=DeadPagination(offset=api.OFFSET, message_id=message_id))
            buttons.append(1)
        builder.adjust(*buttons)
        try:
            await bot.edit_message_reply_markup(chat_id=user_id, message_id=message_id, reply_markup=builder.as_markup())
        except Exception as e:
            print(e)


async def delete_request_messages(first_message_id: int, second_message_id: int, chat1_id, chat2_id):
    try:
        await bot.delete_message(chat_id=chat1_id, message_id=first_message_id)
        await bot.delete_message(chat_id=chat2_id, message_id=second_message_id)
    except:
        await bot.send_message(chat_id=chat1_id, text="You are gay")
        await bot.send_message(chat_id=chat2_id, text="You are gay")


async def edit_request_message(first_id: int, second_id: int, message1_id: int, message2_id: int, queue_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(text="Удалить запрос",
                   callback_data=RemoveSwapRequest(first_m_id=message1_id, second_m_id=message2_id,
                                                   first_user_id=first_id, second_user_id=second_id, queue_id=queue_id))
    try:
        await bot.edit_message_reply_markup(chat_id=first_id, message_id=message1_id,
                                            reply_markup=builder.as_markup())
    except Exception as ex:
        print("FFFFFFFFFFFFFFFFFFFFFFFFFFFFFF", ex)


async def cmd_startgroup(message: types.Message) -> None:
    if message.chat.type == "supergroup":
        chat_admins = await bot.get_chat_administrators(message.chat.id)
        d = []
        names = []
        for admin in chat_admins:
            userId = admin.user.id
            name = admin.user.full_name
            d.append(userId)
            names.append(name)
        await api.add_admin(message.chat.id, d, bot.id, names, message.chat.title, message.message_thread_id)
        if not settings.DEBUG:
            from queue_api.tasks import task_get_users
            result = task_get_users.delay(message.chat.id, (await bot.get_me()).id)
            await message.answer(
                "Здравствуйте, уважаемые пользователи! Для того, чтобы создать очередь, админ группы должен написать в личное сообщение боту.\n/help - для вывода дополнительных команд")
            users = result.get()
            for user in users:
                await api.add_user_to_group(message.chat.id, user['id'], user['full_name'],
                                            False, message.chat.title, message.message_thread_id)
        else:
            await message.answer(
                "Здравствуйте, уважаемые пользователи! Для того, чтобы создать очередь, админ группы должен написать в личное сообщение боту.\n/help - для вывода дополнительных команд")


async def get_bot_name():
    return (await bot.get_me()).username


async def session_begin(group_id: int, thread_id: int):
    await bot.send_message(chat_id=group_id, message_thread_id=thread_id, text='СЕССИЯ НАЧАЛАСЬ!!!')


async def session_end(group_id: int, thread_id: int):
    await bot.send_message(chat_id=group_id, message_thread_id=thread_id, text='СЕССИЯ ЗАКОНЧИЛАСЬ(((')


async def send_message_to_new_main_admin(user_id: int, user_name: str, group_id: int, group_name: str, thread_id: int):
    try:
        await bot.send_message(chat_id=user_id, text=f'Боги увидели в вас великую силу и назначили главным админом в группе {group_name}. Пользуйтесь этой силой с умом! Если боитесь свалившегося на вас груза, то можете переназначить эту должность на другого админа с помощью команды /set_main_admin')
    except Exception:
        await bot.send_message(chat_id=group_id, message_thread_id=thread_id,
                               text=f'Новым главным админом был назначен {user_name}. Если он боится свалившегося на него груза, то он может переназначить эту должность на другого админа с помощью команды /set_main_admin')
