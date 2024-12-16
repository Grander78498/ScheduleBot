import asyncio
import datetime
from dateutil.relativedelta import relativedelta
from aiogram.dispatcher.router import Router
from aiogram.filters.command import Command, CommandStart, CommandObject
from aiogram import F
from aiogram.filters import ChatMemberUpdatedFilter, KICKED, MEMBER, IS_ADMIN, RESTRICTED, LEFT, ADMINISTRATOR, CREATOR
from aiogram.types import ChatMemberUpdated
from aiogram.types import Message, CallbackQuery
from aiogram.utils.deep_linking import decode_payload

from emoji import emojize
from .states import *
from .utils import *

from .bot import bot

router = Router()

months = {
    1: ["Январь", 31],
    2: ["Февраль", 28],
    3: ["Март", 31],
    4: ["Апрель", 30],
    5: ["Май", 31],
    6: ["Июнь", 30],
    7: ["Июль", 31],
    8: ["Август", 31],
    9: ["Сентябрь", 30],
    10: ["Октябрь", 31],
    11: ["Ноябрь", 30],
    12: ["Декабрь", 31]
}


@router.chat_member(ChatMemberUpdatedFilter(member_status_changed=(ADMINISTRATOR | CREATOR) << (KICKED | LEFT | RESTRICTED | MEMBER)))
async def added_admin(event: ChatMemberUpdated):
    await api.change_admin_status(event.new_chat_member.user.id, event.chat.id, True)


@router.chat_member(ChatMemberUpdatedFilter(member_status_changed=(ADMINISTRATOR | CREATOR) >> (RESTRICTED | MEMBER)))
async def deleted_admin(event: ChatMemberUpdated):
    await api.change_admin_status(event.new_chat_member.user.id, event.chat.id, False)


@router.message(Command("queue"))
async def print_info_queue(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="Создать очередь", callback_data="add_queue")
    builder.button(text="Вывести существующие очереди", callback_data="print_queue")
    builder.button(text="Запросить перемещение в очереди", callback_data="swap")
    builder.adjust(1)
    await message.answer("Здравствуйте, вам доступен следующий функционал по очередям\n", reply_markup=builder.as_markup())

@router.message(Command("set_main_admin"))
async def set_main_admin(message: types.Message, state: FSMContext):
    if message.chat.type == "private":
        await message.answer("Данная команда доступна только в группе")
    elif message.chat.type == "supergroup":
        res = await api.check_main_admin(message.chat.id, message.from_user.id)
        if res['status'] == 'ERROR':
            mes = await message.answer(res['message'])
            await asyncio.sleep(5)
            await bot.delete_message(chat_id=message.chat.id, message_id=mes.message_id)
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
            await state.update_data(set_main_admin={"message_id": message.message_id, "status": "ERROR",
                                                    'bot_message_id': mes.message_id})
            await state.set_state(Event.set_main_admin)
        else:
            mes = await message.answer('Перешлите сообщение от того администратора, которого вы хотите назначить')
            await state.update_data(set_main_admin={"message_id": message.message_id, "status": "OK",
                                                    'bot_message_id': mes.message_id})
            await state.set_state(Event.set_main_admin)


@router.message(Command("deadline"))
async def print_info_deadline(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="Создать напоминание", callback_data="add_deadline")
    builder.button(text="Вывести существующие напоминания", callback_data="print_deadline")
    builder.button(text="Управление напоминаниями", callback_data="edit_deadline")
    builder.adjust(1)
    await message.answer("Здравствуйте, вам доступен следующий функционал по дедлайнам\n", reply_markup=builder.as_markup())


@router.message(Command("mary_crhi"))
async def mary_crhistmas(message: types.Message):
        groups = await api.check_admin(call.message.chat.id)
        if len(groups) == 0:
            await call.message.answer("У тебя нет групп, где ты админ, нового года не будет")
        else:
            builder = InlineKeyboardBuilder()
            await state.update_data(event_type=EventType.QUEUE)
            for group in groups:
                builder.button(text=group.name,
                               callback_data=GroupSelectCallback(groupID=group.tg_id, is_admin = True))
            builder.adjust(1)
            mes = await call.message.answer("У тебя есть доступ к этим группам", reply_markup=builder.as_markup())
            await state.update_data(event_message_id=mes.message_id)



@router.message(Command("change_topic"))
async def change_topic(message: types.Message):
    ok = True if message.from_user.id in [i.user.id for i in
                                          (await bot.get_chat_administrators(message.chat.id))] else False
    if ok:
        await api.change_topic(message.chat.id, message.message_thread_id)
        await message.answer(text="Тема изменена успешно")
        await cmd_startgroup(message)
    else:
        try:
            await bot.send_message(text="Пошёл нахуй пидорас уёбище блядское хули лезешь не туда???",
                                   chat_id=message.from_user.id)
        except aiogram.exceptions.TelegramForbiddenError:
            pass


@router.message(CommandStart())
@router.message(CommandStart(deep_link=True))
async def cmd_start(message: types.Message, command: CommandObject) -> None:
    if message.chat.type == "private":
        if len(str(message.text).split()) > 1:
            args = command.args
            queueID = int(decode_payload(args))
            await api.save_user(message.chat.id, message.from_user.full_name)
            await api.add_user_to_queue(queueID, message.chat.id, message.from_user.full_name)
            # Здесь был render queue
            link = await api.get_queue_message_link(queueID, message.from_user.id)
            return_builder = InlineKeyboardBuilder()
            if len(link) != 0:
                return_builder.button(text="Вернуться в группу", url=link)
            await message.answer("Тебя добавили в очередь", reply_markup=return_builder.as_markup())
        elif len(str(message.text).split()) == 1:
            builder_add = InlineKeyboardBuilder()
            builder_add.button(text="Добавить бота в группу",
                               url="https://t.me/{}?startgroup={}&admin=pin_messages+delete_messages".format(await get_bot_name(), message.chat.id))
            builder_add.adjust(1)
            await api.save_user(message.chat.id, message.from_user.full_name)
            await message.answer(
                "Приветствую!\nС помощью данного бота можно удобно создавать очереди и дедлайны, чтобы было легче справляться со студенческими трудностями\n"
                "/queue - для управления очередями\n"
                "/deadline - для управления дедлайнами\n"
                "/help - для вывода краткой помощи",
                reply_markup=builder_add.as_markup())
    elif message.chat.type == "supergroup":
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)


@router.message(Command('stats'))
async def command_stats(message: types.Message) -> None:
    if message.chat.type == "private":
        await message.answer(await api.get_stats())


@router.message(Command("change_tz"))
async def cmd_change_tz(message: types.Message, state: FSMContext):
    await message.answer("Введите новый часовой пояс")
    await state.set_state(Event.tz)


@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=KICKED))
async def user_blocked_bot(event: ChatMemberUpdated):
    if event.chat.type == "private":
        await api.update_started(event.from_user.id, event.from_user.full_name, False)


@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=MEMBER))
async def user_unblocked_bot(event: ChatMemberUpdated):
    if event.chat.type == "private":
        await api.update_started(event.from_user.id, event.from_user.full_name, True)


@router.callback_query(RemoveSwapRequest.filter(F.first_m_id != 0))
async def remove_swap(call: CallbackQuery, callback_data: RemoveSwapRequest):
    await api.remove_request(callback_data.first_user_id, callback_data.second_user_id, callback_data.queue_id)
    await delete_request_messages(callback_data.first_m_id, callback_data.second_m_id, callback_data.first_user_id,
                                  callback_data.second_user_id)


@router.callback_query(SwapCallback.filter(F.queueId != 0))
async def swap_result(call: CallbackQuery, callback_data: SwapCallback, state: FSMContext):
    current_member_id = await api.remove_request(callback_data.first_tg_user_id, call.from_user.id,
                                                 callback_data.queueId)
    if callback_data.message_type == "Deny":
        await bot.send_message(chat_id=callback_data.first_tg_user_id, text="Ваш запрос был отклонён")
    else:
        await api.swap_places(callback_data.first_user_id, callback_data.second_user_id)
        # Здесь был render queue
        await bot.send_message(chat_id=callback_data.first_tg_user_id,
                               text="Ваш запрос был удовлетворён. Вы поменяны в очереди")
    await delete_request_messages(callback_data.message1_id, callback_data.message2_id, callback_data.first_tg_user_id,
                                  call.from_user.id)
    deletable = await api.remove_all_in_requests(current_member_id)
    for elem in deletable:
        await delete_request_messages(elem["first_message_id"], elem["second_message_id"], elem["first_member"],
                                      call.from_user.id)
        await bot.send_message(chat_id=elem["first_member"], text="Ваш запрос был отклонён")
    await call.answer()


@router.callback_query(QueueSwapPagination.filter(F.offset != -1))
async def swap_pagin(call: CallbackQuery, callback_data: QueueSwapPagination):
    _dict = await api.get_all_queues(call.from_user.id, callback_data.offset, True)
    status = _dict["status"]
    if status!="OK":
        await call.message.answer(_dict["message"])
    else:
        lenq = len(_dict["data"])
        has_next = _dict["has_next"]
        queueList = [queue["id"] for queue in _dict["data"]]
        names = [queue["name"] for queue in _dict["data"]]
        st = _dict["message"]
        r = await bot.edit_message_text(text=st,chat_id=call.from_user.id, message_id=callback_data.message_id, parse_mode="MarkdownV2")
        builder = InlineKeyboardBuilder()
        for i in range(lenq):
            builder.button(text="{}".format(i + callback_data.offset + 1),
                           callback_data=QueueSelectForSwapCallback(queueID=queueList[i],
                                                                    queueName=names[i]))
        buttons = [5 for _ in range(lenq//5)]
        if lenq%5!=0:
            buttons.append(lenq%5)
        nav_button = 0
        if callback_data.offset != 0:
            builder.button(text=emojize(":left_arrow:"), callback_data=QueueSwapPagination(offset = callback_data.offset - api.OFFSET, message_id=callback_data.message_id))
            nav_button += 1
        if has_next:
            builder.button(text=emojize(":right_arrow:"), callback_data=QueueSwapPagination(offset = callback_data.offset + api.OFFSET, message_id=callback_data.message_id))
            nav_button += 1
        buttons.append(nav_button)
        builder.adjust(*buttons)
        await bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=r.message_id,
                                            reply_markup=builder.as_markup())
    await call.answer()



@router.callback_query(QueuePagination.filter(F.offset != -1))
async def queue_pagin(call: CallbackQuery, callback_data: QueuePagination):
    _dict = await api.get_all_queues(call.from_user.id, callback_data.offset, False)
    status = _dict["status"]
    if status!="OK":
        await call.message.answer(_dict["message"])
    else:
        lenq = len(_dict["data"])
        has_next = _dict["has_next"]
        queueList = [queue["id"] for queue in _dict["data"]]
        names = [queue["name"] for queue in _dict["data"]]
        is_creators = [queue["is_creator"] for queue in _dict["data"]]
        st = _dict["message"]
        r = await bot.edit_message_text(text=st,chat_id=call.from_user.id, message_id=callback_data.message_id, parse_mode="MarkdownV2")
        builder = InlineKeyboardBuilder()
        for i in range(lenq):
            builder.button(text="{}".format(i + callback_data.offset + 1),
                           callback_data= (AdminQueueSelectCallback(queueID=queueList[i], delete_message_id=r.message_id, queueName=names[i])) if is_creators[i] else SimpleQueueSelectCallback(queueID=queueList[i], delete_message_id=r.message_id, queueName=names[i]))
        buttons = [5 for _ in range(lenq//5)]
        if lenq%5!=0:
            buttons.append(lenq%5)
        nav_button = 0
        if callback_data.offset != 0:
            builder.button(text=emojize(":left_arrow:"), callback_data=QueuePagination(offset = callback_data.offset - api.OFFSET, message_id=callback_data.message_id))
            nav_button += 1
        if has_next:
            builder.button(text=emojize(":right_arrow:"), callback_data=QueuePagination(offset = callback_data.offset + api.OFFSET, message_id=callback_data.message_id))
            nav_button += 1
        buttons.append(nav_button)
        builder.adjust(*buttons)
        await bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=r.message_id,
                                            reply_markup=builder.as_markup())
    await call.answer()




@router.callback_query(F.data.in_(['swap']))
async def swap(call: CallbackQuery, state: FSMContext):
    _dict = await api.get_all_queues(call.from_user.id, 0, True)
    status = _dict["status"]
    if status!="OK":
        await call.message.answer(_dict["message"])
    else:
        lenq = len(_dict["data"])
        has_next = _dict["has_next"]
        queueList = [queue["id"] for queue in _dict["data"]]
        names = [queue["name"] for queue in _dict["data"]]
        st = _dict["message"]
        r = await call.message.answer(st, parse_mode="MarkdownV2")
        builder = InlineKeyboardBuilder()
        for i in range(lenq):
            builder.button(text="{}".format(i + 1),
                           callback_data=QueueSelectForSwapCallback(queueID=queueList[i],
                                                                    queueName=names[i]))
        buttons = [5 for _ in range(lenq//5)]
        if lenq%5!=0:
            buttons.append(lenq%5)
        if has_next:
            builder.button(text=emojize(":right_arrow:"), callback_data=QueueSwapPagination(offset = api.OFFSET, message_id=r.message_id))
            buttons.append(1)
        builder.adjust(*buttons)
        await bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=r.message_id,
                                            reply_markup=builder.as_markup())
    await call.answer()


@router.callback_query(F.data.in_(['print_deadline']))
async def printDeadline(call: CallbackQuery, state: FSMContext):
    res = await api.get_deadlines(call.from_user.id, 0, False)
    builder = InlineKeyboardBuilder()
    if res["status"]!="OK":
        builder.button(text="Создать напоминание", callback_data="add_deadline")
        builder.button(text="Вывести существующие напоминания", callback_data="print_deadline")
        builder.button(text="Управление напоминаниями", callback_data="edit_deadline")
        builder.adjust(1)
        await call.message.answer(res["message"], reply_markup=builder.as_markup())
    else:
        has_next = res['has_next']
        mes = await call.message.answer(emojize(res["message"]))
        len_d = 0
        for dead_id, is_done in res["deadline_list"]:
            builder.button(text=("{}".format(len_d+1)), callback_data=CanbanDesk(deadline_status_id=dead_id, is_done=is_done, message_id=mes.message_id))
            len_d+=1
        buttons = [5 for _ in range(len_d//5)]
        if len_d%5!=0:
            buttons.append(len_d%5)
        if has_next:
            builder.button(text=emojize(":right_arrow:"), callback_data=DeadPagination(offset = api.OFFSET, message_id=mes.message_id))
            buttons.append(1)
        builder.adjust(*buttons)
        await bot.edit_message_reply_markup(chat_id=call.from_user.id, message_id=mes.message_id, reply_markup=builder.as_markup())
    await call.answer()



@router.callback_query(F.data.in_(['edit_deadline']))
async def editDeadline(call: CallbackQuery):
    res = await api.get_deadlines(call.from_user.id, 0, True)
    builder = InlineKeyboardBuilder()
    if res["status"]!="OK":
        builder.button(text="Создать напоминание", callback_data="add_deadline")
        builder.button(text="Вывести существующие напоминания", callback_data="print_deadline")
        builder.button(text="Управление напоминаниями", callback_data="edit_deadline")
        builder.adjust(1)
        await call.message.answer(res["message"], reply_markup=builder.as_markup())
    else:
        has_next = res['has_next']
        mes = await call.message.answer(res["message"])
        len_d = 0
        for dead_id, _ in res["deadline_list"]:
            builder.button(text=("{}".format(len_d+1)), callback_data=EditDeadline(deadline_id=dead_id, message_id=mes.message_id))
            len_d+=1
        buttons = [5 for _ in range(len_d//5)]
        if len_d%5!=0:
            buttons.append(len_d%5)
        if has_next:
            builder.button(text=emojize(":right_arrow:"), callback_data=EditDeadPagination(offset = api.OFFSET, message_id=mes.message_id))
            buttons.append(1)
        builder.adjust(*buttons)
        await bot.edit_message_reply_markup(chat_id=call.from_user.id, message_id=mes.message_id, reply_markup=builder.as_markup())
    await call.answer()

@router.callback_query(EditDeadline.filter(F.deadline_id != 0))
async def refactor_deadline(call: CallbackQuery, callback_data: EditDeadline):
    deadline_name, group_name = await api.get_deadline_name(callback_data.deadline_id)
    builder = InlineKeyboardBuilder()
    builder.button(text="Изменить название дедлайна", callback_data=RenameDeadlineCallback(deadline_id=callback_data.deadline_id))
    builder.button(text="Удалить дедлайн",
                   callback_data=DeleteDeadlineCallback(deadline_id=callback_data.deadline_id, messageID=call.message.message_id))
    builder.button(text="\u25C0", callback_data=ReturnToDeadlineList(messageID=call.message.message_id))
    builder.adjust(2)
    await bot.edit_message_text(text="Выбран дедлайн {} в группе {}".format(deadline_name, group_name), chat_id=call.message.chat.id,
                                message_id=callback_data.message_id)
    await bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                        reply_markup=builder.as_markup())



@router.callback_query(RenameDeadlineCallback.filter(F.deadline_id != 0))
async def rename_deadline(call: CallbackQuery, callback_data: RenameDeadlineCallback, state: FSMContext):
    mes = await call.message.answer("Напиши новое название")
    await state.update_data(renameDeadline={"message_id":mes.message_id, "dead_id":callback_data.deadline_id, "edit_message_id":call.message.message_id})
    await state.set_state(Deadline.renameDeadline)
    await call.answer()

@router.callback_query(DeleteDeadlineCallback.filter(F.deadline_id != 0))
async def delete_deadline(call: CallbackQuery, callback_data: DeleteDeadlineCallback):
    mes = await call.message.answer("Дедлайн был удалён")
    message_id, group_id = await api.delete_deadline_by_status(callback_data.deadline_id)
    try:
        await bot.delete_message(chat_id=group_id, message_id=message_id)
    except Exception:
        await bot.edit_message_text(chat_id=group_id, message_id=message_id, text='Дедлайн был удалён')
    await deadline_list_return(call.from_user.id, callback_data.messageID)
    await asyncio.sleep(5)
    await bot.delete_message(chat_id=call.from_user.id, message_id=mes.message_id)
    await call.answer()



@router.callback_query(ReturnToDeadlineList.filter(F.messageID != 0))
async def return_deadline_list(call: CallbackQuery, callback_data: ReturnToDeadlineList):
    await deadline_list_return(call.from_user.id, callback_data.messageID)
    await call.answer()


@router.callback_query(DeadPagination.filter(F.offset != -1))
async def dead_pagin(call: CallbackQuery, callback_data: DeadPagination):
    _dict = await api.get_deadlines(call.from_user.id, callback_data.offset, False)
    status = _dict["status"]
    if status!="OK":
        await call.message.answer(_dict["message"])
    else:
        builder = InlineKeyboardBuilder()
        await bot.edit_message_text(text=emojize(_dict["message"]),chat_id=call.from_user.id, message_id=callback_data.message_id)
        len_d = 0
        for dead_id, is_done in _dict["deadline_list"]:
            builder.button(text=("{}".format(len_d + callback_data.offset + 1)), callback_data=CanbanDesk(deadline_status_id=dead_id, is_done=is_done, message_id=callback_data.message_id))
            len_d+=1
        has_next = _dict["has_next"]
        buttons = [5 for _ in range(len_d//5)]
        if len_d%5!=0:
            buttons.append(len_d%5)
        nav_button = 0
        if callback_data.offset != 0:
            builder.button(text=emojize(":left_arrow:"), callback_data=DeadPagination(offset = callback_data.offset - api.OFFSET, message_id=callback_data.message_id))
            nav_button += 1
        if has_next:
            builder.button(text=emojize(":right_arrow:"), callback_data=DeadPagination(offset = callback_data.offset + api.OFFSET, message_id=callback_data.message_id))
            nav_button += 1
        buttons.append(nav_button)
        builder.adjust(*buttons)
        await bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=callback_data.message_id,
                                            reply_markup=builder.as_markup())
    await call.answer()


@router.callback_query(EditDeadPagination.filter(F.offset != -1))
async def edit_dead_pagin(call: CallbackQuery, callback_data: EditDeadPagination):
    _dict = await api.get_deadlines(call.from_user.id, callback_data.offset, True)
    status = _dict["status"]
    if status!="OK":
        await call.message.answer(_dict["message"])
    else:
        builder = InlineKeyboardBuilder()
        await bot.edit_message_text(text=emojize(_dict["message"]),chat_id=call.from_user.id, message_id=callback_data.message_id)
        len_d = 0
        for dead_id, _ in _dict["deadline_list"]:
            builder.button(text=("{}".format(len_d + callback_data.offset + 1)), callback_data=EditDeadline(deadline_id=dead_id, message_id=callback_data.message_id))
            len_d+=1
        has_next = _dict["has_next"]
        buttons = [5 for _ in range(len_d//5)]
        if len_d%5!=0:
            buttons.append(len_d%5)
        nav_button = 0
        if callback_data.offset != 0:
            builder.button(text=emojize(":left_arrow:"), callback_data=EditDeadPagination(offset = callback_data.offset - api.OFFSET, message_id=callback_data.message_id))
            nav_button += 1
        if has_next:
            builder.button(text=emojize(":right_arrow:"), callback_data=EditDeadPagination(offset = callback_data.offset + api.OFFSET, message_id=callback_data.message_id))
            nav_button += 1
        buttons.append(nav_button)
        builder.adjust(*buttons)
        await bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=callback_data.message_id,
                                            reply_markup=builder.as_markup())
    await call.answer()




@router.callback_query(F.data.in_(['add_deadline']))
async def add_deadline(call: CallbackQuery, state: FSMContext):
    if call.message.chat.type == "private":
        res = await api.check_event_count(call.from_user.id, EventType.DEADLINE)
        if res['status'] == 'ERROR':
            await call.answer(res['message'])
        else:
            groups = await api.get_user_groups(call.message.chat.id)
            if len(groups) == 0:
                await call.answer("Вы не состоите ни в одной группе")
            else:
                builder = InlineKeyboardBuilder()
                await state.update_data(event_type=EventType.DEADLINE)
                for group, is_admin in groups:
                    builder.button(text=group.name,
                                   callback_data=GroupSelectCallback(groupID=group.tg_id, is_admin=is_admin))
                builder.adjust(1)
                mes = await call.message.answer("У тебя есть доступ к этим группам", reply_markup=builder.as_markup())
                await state.update_data(event_message_id=mes.message_id)
            await call.answer()


@router.callback_query(CanbanDesk.filter(F.deadline_status_id != 0))
async def deadline_status_info(call: CallbackQuery, callback_data: CanbanDesk):
    is_done = callback_data.is_done
    check = await api.check_deadline_status(callback_data.deadline_status_id)
    if not check:
        await call.answer("Дедлайн уже удалён")
        res = await api.get_deadlines(call.from_user.id, 0, False)
        await update_deadline_info(res, call.from_user.id, callback_data.message_id)
    else:
        deadline_name, group_name = await api.get_deadline_name(callback_data.deadline_status_id)
        builder = InlineKeyboardBuilder()
        mes = await call.message.answer("Вы выбрали дедлайн {} в группе {}, вам доступны след. действия".format(deadline_name, group_name))
        if is_done:
            builder.button(text="Удалить дедлайн".format(deadline_name), callback_data=DeadStatus(deadline_status_id=callback_data.deadline_status_id, is_done=is_done, message_id=callback_data.message_id, d_type="delete", del_mes = mes.message_id))
            builder.button(text="Изменить статус".format(deadline_name), callback_data=DeadStatus(deadline_status_id=callback_data.deadline_status_id, is_done=is_done, message_id=callback_data.message_id, d_type="change", del_mes = mes.message_id))
            builder.button(text="Отмена".format(deadline_name), callback_data=DeadStatus(deadline_status_id=callback_data.deadline_status_id, is_done=is_done, message_id=callback_data.message_id, d_type="cansel", del_mes = mes.message_id))
            builder.adjust(2,1)
        else:
            builder.button(text="Изменить статус".format(deadline_name), callback_data=DeadStatus(deadline_status_id=callback_data.deadline_status_id, is_done=is_done, message_id=callback_data.message_id, d_type="change", del_mes = mes.message_id))
            builder.button(text="Отмена".format(deadline_name), callback_data=DeadStatus(deadline_status_id=callback_data.deadline_status_id, is_done=is_done, message_id=callback_data.message_id, d_type="cansel", del_mes = mes.message_id))
            builder.adjust(1,1)
        await bot.edit_message_reply_markup(chat_id=call.from_user.id, message_id=mes.message_id, reply_markup=builder.as_markup())
        await call.answer()


@router.callback_query(DeadStatus.filter(F.deadline_status_id != 0))
async def deadline_status_change(call: CallbackQuery, callback_data: DeadStatus):
    if callback_data.d_type=="delete":
        await api.delete_deadline_status(callback_data.deadline_status_id)
    elif callback_data.d_type=="change":
        await api.update_done_status(callback_data.deadline_status_id)
    await bot.delete_message(chat_id=call.from_user.id, message_id=callback_data.del_mes)
    res = await api.get_deadlines(call.from_user.id, 0, False)
    await update_deadline_info(res, call.from_user.id, callback_data.message_id)
    await call.answer()



@router.callback_query(QueueSelectForSwapCallback.filter(F.queueID != 0))
async def swap_print(call: CallbackQuery, callback_data: QueueSelectForSwapCallback, state: FSMContext):
    status = await api.check_requests(call.from_user.id, callback_data.queueID)
    if not status["in"] and not status["out"]:
        _, text, _ = await api.print_queue(callback_data.queueID, call.message.chat.type == "private", bot)
        queue_list_message = await call.message.answer(text, parse_mode="MarkdownV2")
        simple_message = await call.message.answer("Скопируйте id пользователя из очереди и отправьте в сообщении")
        await state.set_state(Event.swap)
        res = {"queueID": callback_data.queueID, "first_m": queue_list_message.message_id,
               "second_m": simple_message.message_id}
        await state.update_data(swap=res)
        await call.answer()
    elif status["in"]:
        await call.answer("У вас есть нерассмотренный входящий запрос")
    elif status["out"]:
        await call.answer("У вас уже есть отправленный запрос, если прошло достаточно времени, вы можете его удалить")
    else:
        await call.answer("Непредвиденная ошибка...")




@router.callback_query(ChristmasGroupSelectCallback.filter(F.groupID != 0))
async def christmasgroupSelected(call: CallbackQuery, callback_data: ChristmasGroupSelectCallback):
    await call.message.answer("Новый год будет")
    await call.answer()


@router.callback_query(GroupSelectCallback.filter(F.groupID != 0))
async def groupSelected(call: CallbackQuery, callback_data: GroupSelectCallback, state: FSMContext):
    data = await state.get_data()
    await bot.delete_message(chat_id=call.from_user.id, message_id=data['event_message_id'])
    await state.update_data(group_id=callback_data.groupID)
    await state.update_data(deadline_roots=callback_data.is_admin)
    await call.message.answer("Напишите название очереди")
    await state.set_state(Event.text)
    await call.answer()


@router.callback_query(F.data.in_(['add_queue']))
async def add_queue(call: CallbackQuery, state: FSMContext):
    if call.message.chat.type == "private":
        res = await api.check_event_count(call.from_user.id, EventType.QUEUE)
        if res['status'] == 'ERROR':
            await call.answer(res['message'])
        else:
            groups = await api.check_admin(call.message.chat.id)
            if len(groups) == 0:
                builder = InlineKeyboardBuilder()
                builder.button(text="Создать очередь", callback_data="add_queue")
                builder.button(text="Вывести существующие очереди", callback_data="print_queue")
                builder.button(text="Запросить перемещение в очереди", callback_data="swap")
                builder.adjust(1)
                await call.message.answer("У тебя нет групп, где ты админ", reply_markup=builder.as_markup())
            else:
                builder = InlineKeyboardBuilder()
                await state.update_data(event_type=EventType.QUEUE)
                for group in groups:
                    builder.button(text=group.name,
                                   callback_data=GroupSelectCallback(groupID=group.tg_id, is_admin = True))
                builder.adjust(1)
                mes = await call.message.answer("У тебя есть доступ к этим группам", reply_markup=builder.as_markup())
                await state.update_data(event_message_id=mes.message_id)
            await call.answer()


@router.callback_query(F.data.in_(['print_queue']))
async def printQueue(call: CallbackQuery, state: FSMContext):
    _dict = await api.get_all_queues(call.from_user.id, 0, False)
    status = _dict["status"]
    if status!="OK":
        await call.message.answer(_dict["message"])
    else:
        lenq = len(_dict["data"])
        queueList = [queue["id"] for queue in _dict["data"]]
        has_next = _dict["has_next"]
        names = [queue["name"] for queue in _dict["data"]]
        is_creators = [queue["is_creator"] for queue in _dict["data"]]
        st = _dict["message"]
        r = await call.message.answer(st, parse_mode='MarkdownV2')
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
        await bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=r.message_id,
                                            reply_markup=builder.as_markup())
    await call.answer()


@router.callback_query(ReturnToQueueList.filter(F.messageID != 0))
async def printQueue_returned(call: CallbackQuery, callback_data: ReturnToQueueList, state: FSMContext):
    await queue_return(call.from_user.id, callback_data.messageID)
    await call.answer()



@router.callback_query(SimpleQueueSelectCallback.filter(F.queueID != 0))
async def SimpleQueueChosen(call: CallbackQuery, callback_data: SimpleQueueSelectCallback):
    res = await api.check_user_in_queue(call.from_user.id, callback_data.queueID)
    if res["status"]=="OK":
        message_id = await api.get_message_id(callback_data.queueID, call.from_user.id)
        _,string,_ = await api.print_private_queue(callback_data.queueID, call.from_user.id, bot)
        if message_id is not None:
            try:
                await bot.edit_message_text(text=string, chat_id=call.from_user.id, message_id=message_id,
                                            parse_mode='MarkdownV2')
                await call.answer('Сообщение с этой очередью было изменено')
            except Exception:
                mes = await call.message.answer(string, parse_mode='MarkdownV2')
                await api.update_message_id(callback_data.queueID, mes.message_id, call.from_user.id)
                await call.answer()
        else:
            mes = await call.message.answer(string, parse_mode='MarkdownV2')
            await api.update_message_id(callback_data.queueID, mes.message_id, call.from_user.id)
            await call.answer()
    else:
        await call.answer(res["message"])
        await queue_return(call.from_user.id, call.message.message_id)



@router.callback_query(AdminQueueSelectCallback.filter(F.queueID != 0))
async def AdminQueueChosen(call: CallbackQuery, callback_data: AdminQueueSelectCallback):
    builder = InlineKeyboardBuilder()
    builder.button(text="Изменить название очереди", callback_data=RenameQueueCallback(queueID=callback_data.queueID, messageID=call.message.message_id))
    builder.button(text="Удалить участника очереди",
                   callback_data=DeleteQueueMemberCallback(queueID=callback_data.queueID,messageID=call.message.message_id))
    builder.button(text="Удалить очередь",
                   callback_data=DeleteQueueCallback(queueID=callback_data.queueID, messageID=call.message.message_id))
    builder.button(text="Удалить первого из очереди",
                   callback_data=DeleteFirstQueueCallback(queueID=callback_data.queueID))
    builder.button(text="\u25C0", callback_data=ReturnToQueueList(messageID=call.message.message_id))
    builder.adjust(2)
    await bot.edit_message_text(text="Выбрана очередь {}".format(callback_data.queueName), chat_id=call.message.chat.id,
                                message_id=callback_data.delete_message_id)
    await bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=callback_data.delete_message_id,
                                        reply_markup=builder.as_markup())

    # Удалить очередь, удалить участника, изменить название, кнопка назад

    await call.answer()


@router.callback_query(DeleteFirstQueueCallback.filter(F.queueID != 0))
async def remove_first(call: CallbackQuery, callback_data: DeleteFirstQueueCallback):
    res = await api.remove_first(callback_data.queueID)
    if not res:
        await call.answer("Данная очередь пуста")
    else:
        await call.answer("Первый удалён")
    await queue_return(call.from_user.id, call.message.message_id)
    # Здесь был render queue


@router.callback_query(DeleteQueueMemberCallback.filter(F.messageID != 0))
async def delete_queue_member(call: CallbackQuery, callback_data: DeleteQueueMemberCallback, state: FSMContext):
    _, message, _ = await api.print_queue(callback_data.queueID, call.message.chat.type == "private", bot)
    queue_message = await call.message.answer(text=message, parse_mode='MarkdownV2')
    please_message = await call.message.answer("Введите номер удаляемого участника")
    await state.set_state(Queue.deleteQueueMember)
    await state.update_data(deleteQueueMember={"messageID":callback_data.messageID, "queue_message":queue_message.message_id, "please_message":please_message.message_id})
    await call.answer()


@router.callback_query(RenameQueueCallback.filter(F.queueID != 0))
async def rename_queue(call: CallbackQuery, callback_data: RenameQueueCallback, state: FSMContext):
    r = await call.message.answer("Введите новое название очереди")
    await state.set_state(Queue.renameQueue)
    await state.update_data(renameQueue={"queueID":callback_data.queueID, "messageID":callback_data.messageID, "del_message":r.message_id})
    await call.answer()


@router.callback_query(DeleteQueueCallback.filter(F.queueID != 0))
async def deleted_queue(call: CallbackQuery, callback_data: DeleteQueueCallback):
    chat_list, message_list = await api.delete_queue(callback_data.queueID)
    for chat_id, message_id in zip(chat_list, message_list):
        try:
            await bot.delete_message(chat_id=chat_id, message_id=message_id)
        except Exception:
            await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text='Очередь больше не активна')
    await call.answer("Очередь удалена")
    await queue_return(call.from_user.id, callback_data.messageID)


@router.callback_query(DayCallback.filter(F.day != 0))
async def Day(call: CallbackQuery, callback_data: DayCallback, state: FSMContext):
    if call.message.chat.type == "private":
        await state.update_data(day=callback_data.day)
        await state.set_state(Event.hm)
        await call.message.answer("Введите время в формате ЧЧ:ММ")
        await call.answer()


@router.callback_query(MonthCallback.filter(F.month != 0))
async def Month(call: CallbackQuery, callback_data: MonthCallback, state: FSMContext):
    if call.message.chat.type == "private":
        await state.update_data(month=callback_data.month)
        await state.set_state(Calendar.day)
        builder = InlineKeyboardBuilder()
        a = 1
        remove = await state.get_data()
        if datetime.datetime.now().month == callback_data.month:
            a = datetime.datetime.now().day
        year = remove["year"]
        b = months[callback_data.month][1]
        if year % 4 == 0 and (year % 1000 == 0 or year % 100 != 0) and callback_data.month == 2:
            b += 1
        for i in range(a, b + 1):
            builder.button(text="{}".format(i), callback_data=DayCallback(day=int(i)))
        builder.adjust(6)
        # r = 0
        remove = remove["RemoveMessagemonth"] if "RemoveMessagemonth" in remove else None
        ok = True
        if remove is not None and len(remove.reply_markup.inline_keyboard) == len(
                builder.as_markup().inline_keyboard) and len(builder.as_markup().inline_keyboard[0]) == len(
            remove.reply_markup.inline_keyboard[0]):
            ok = False
            for i in range(len(remove.reply_markup.inline_keyboard)):
                for j in range(len(remove.reply_markup.inline_keyboard[i])):
                    if remove.reply_markup.inline_keyboard[i][j].text != builder.as_markup().inline_keyboard[i][j].text:
                        ok = True
                        break
        if ok:
            if remove is not None and remove.reply_markup != builder.as_markup():
                w = await bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=remove.message_id,
                                                        reply_markup=builder.as_markup())
                await state.update_data(RemoveMessagemonth=w)
            else:
                r = await call.message.answer("Выберите день", reply_markup=builder.as_markup())
                await state.update_data(RemoveMessagemonth=r)
    await call.answer()



@router.callback_query(DeadLineAcceptCallback.filter(F.deadline_id != 0))
async def DeadlineSolution(call: CallbackQuery, callback_data: DeadLineAcceptCallback):
    group_id, text, thread_id, date, notif_date = await api.get_deadline_info(callback_data.deadline_id)
    await api.delete_deadline_request(callback_data.user_id, group_id)
    if callback_data.solution:
        await bot.send_message(chat_id=callback_data.user_id, text="Ваш запрос выполнен")
        mes = await bot.send_message(chat_id=group_id, message_thread_id=thread_id,
                                     text="Дедлайн {} наступит через {}.".format(text, date,
                                                                                             notif_date) +
                                          (" За {} до этого будет отправлено напоминание, чтобы успели убежать".format(
                                              notif_date)
                                           if notif_date != "" else ""))
        await api.update_message_id(callback_data.deadline_id, mes.message_id, group_id)
        await api.create_queue_tasks(callback_data.deadline_id, group_id)
    else:
        await api.delete_deadline(callback_data.deadline_id)
        await bot.send_message(chat_id=callback_data.user_id, text="Ваш запрос не был выполнен, сожалею")
    await bot.delete_message(chat_id=call.from_user.id, message_id=callback_data.message_id)
    await call.answer()



@router.callback_query(YearCallback.filter(F.year != 0))
async def Year(call: CallbackQuery, callback_data: YearCallback, state: FSMContext):
    if call.message.chat.type == "private":
        await state.update_data(year=callback_data.year)
        await state.set_state(Calendar.month)
        builder = InlineKeyboardBuilder()
        a = 1
        if datetime.datetime.now().year == callback_data.year:
            a = datetime.datetime.now().month
        for i in range(a, 13):
            builder.button(text="{}".format(months[i][0]), callback_data=MonthCallback(month=int(i)))
        builder.adjust(3)
        remove = await state.get_data()
        remove = remove["RemoveMessageyear"] if "RemoveMessageyear" in remove else None
        ok = True
        if remove is not None and len(remove.reply_markup.inline_keyboard) == len(
                builder.as_markup().inline_keyboard) and len(builder.as_markup().inline_keyboard[0]) == len(
            remove.reply_markup.inline_keyboard[0]):
            ok = False
            for i in range(len(remove.reply_markup.inline_keyboard)):
                for j in range(len(remove.reply_markup.inline_keyboard[i])):
                    if remove.reply_markup.inline_keyboard[i][j].text != builder.as_markup().inline_keyboard[i][j].text:
                        ok = True
                        break
        if ok:
            if remove is not None:
                w = await bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=remove.message_id,
                                                        reply_markup=builder.as_markup())
                await state.update_data(RemoveMessageyear=w)
            else:
                r = await call.message.answer("Выберите месяц", reply_markup=builder.as_markup())
                await state.update_data(RemoveMessageyear=r)
    await call.answer()


@router.callback_query(F.data.in_(['custom']))
async def custom_time(call: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.button(text="{}".format(datetime.datetime.now().year),
                   callback_data=YearCallback(year=datetime.datetime.now().year))
    builder.button(text="{}".format(datetime.datetime.now().year + 1),
                   callback_data=YearCallback(year=datetime.datetime.now().year + 1))
    builder.button(text="{}".format(datetime.datetime.now().year + 2),
                   callback_data=YearCallback(year=datetime.datetime.now().year + 2))
    builder.adjust(1)
    await call.message.answer("Выберите год", reply_markup=builder.as_markup())
    await state.set_state(Calendar.year)
    await call.answer()


@router.callback_query(F.data.in_(['now']))
async def now_time(call: CallbackQuery, state: FSMContext):
    now = datetime.datetime.now()
    await state.update_data(year=now.year)
    await state.update_data(month=now.month)
    await state.update_data(day=now.day)
    await state.update_data(hm="{:02d}:{:02d}".format(now.hour, now.minute))
    await state.update_data(sec=now.second)
    await putInDb(call.message, state)
    await call.answer()


@router.callback_query(F.data.in_(['one_hour']))
async def next_hour(call: CallbackQuery, state: FSMContext):
    now = datetime.datetime.now() + datetime.timedelta(hours=1)
    await state.update_data(year=now.year)
    await state.update_data(month=now.month)
    await state.update_data(day=now.day)
    await state.update_data(hm="{:02d}:{:02d}".format(now.hour, now.minute))
    await putInDb(call.message, state)
    await call.answer()


@router.callback_query(F.data.in_(['today']))
async def today(call: CallbackQuery, state: FSMContext):
    now = datetime.datetime.now()
    await state.update_data(year=now.year)
    await state.update_data(month=now.month)
    await state.update_data(day=now.day)
    await state.set_state(Event.hm)
    await call.message.answer("Введите время в формате ЧЧ:ММ")
    await call.answer()


@router.callback_query(F.data.in_(['tomorrow']))
async def tomorrow(call: CallbackQuery, state: FSMContext):
    now = datetime.datetime.now() + datetime.timedelta(days=1)
    await state.update_data(year=now.year)
    await state.update_data(month=now.month)
    await state.update_data(day=now.day)
    await state.set_state(Event.hm)
    await call.message.answer("Введите время в формате ЧЧ:ММ")
    await call.answer()


@router.callback_query(F.data.in_(['week']))
async def week(call: CallbackQuery, state: FSMContext):
    now = datetime.datetime.now() + datetime.timedelta(days=7)
    await state.update_data(year=now.year)
    await state.update_data(month=now.month)
    await state.update_data(day=now.day)
    await state.set_state(Event.hm)
    await call.message.answer("Введите время в формате ЧЧ:ММ")
    await call.answer()


@router.callback_query(F.data.in_(['2week']))
async def two_week(call: CallbackQuery, state: FSMContext):
    now = datetime.datetime.now() + datetime.timedelta(days=14)
    await state.update_data(year=now.year)
    await state.update_data(month=now.month)
    await state.update_data(day=now.day)
    await state.set_state(Event.hm)
    await call.message.answer("Введите время в формате ЧЧ:ММ")
    await call.answer()


@router.callback_query(F.data.in_(['one_month']))
async def one_month(call: CallbackQuery, state: FSMContext):
    now = datetime.datetime.today() + relativedelta(months=1)
    await state.update_data(year=now.year)
    await state.update_data(month=now.month)
    await state.update_data(day=now.day)
    await state.set_state(Event.hm)
    await call.message.answer("Введите время в формате ЧЧ:ММ")
    await call.answer()


@router.callback_query(F.data.in_(['half_year']))
async def one_month(call: CallbackQuery, state: FSMContext):
    now = datetime.datetime.today() + relativedelta(months=6)
    await state.update_data(year=now.year)
    await state.update_data(month=now.month)
    await state.update_data(day=now.day)
    await state.set_state(Event.hm)
    await call.message.answer("Введите время в формате ЧЧ:ММ")
    await call.answer()


@router.message(F.forward_from)
async def print_mes(message: Message, state: FSMContext):
    st = await state.get_state()
    if message.chat.type=="supergroup":
        if st == Event.set_main_admin:
            data = await state.get_data()
            await bot.delete_message(chat_id=message.chat.id, message_id=data['set_main_admin']['bot_message_id'])
            new_main_admin_id = message.forward_from.id
            res_possible = await api.check_possible_main_admin(message.chat.id, new_main_admin_id)
            if res_possible['status'] == 'ERROR':
                mes = await message.answer(res_possible['message'])
                await state.clear()
                await asyncio.sleep(5)
                await bot.delete_message(chat_id=message.chat.id, message_id=mes.message_id)
                await bot.delete_message(chat_id=message.chat.id, message_id=data["set_main_admin"]["message_id"])
                await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
            elif data['set_main_admin']['status'] == 'ERROR':
                await state.clear()
                await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
            else:
                await api.set_main_admin(message.chat.id, new_main_admin_id,
                                         message.chat.title, message.message_thread_id)
                await message.answer('Главный админ был успешно сменён!')
                await state.clear()


@router.callback_query(QueueIDCallback.filter(F.queueID != 0))
async def voting(call: CallbackQuery, callback_data: QueueIDCallback):
    client = await api.add_user_to_queue(callback_data.queueID, call.from_user.id, call.from_user.full_name)
    if "error" in client:
        await call.answer(client["error"])
    else:
        is_started = client["started"]
        if is_started:
            is_queue_member = client["queue_member"]
            if is_queue_member:
                await call.answer("Вы уже добавлены в очередь")
            else:
                # Здесь был render_queue
                pass
            await call.answer()
        else:
            await call.answer(url=await api.get_queue_link(callback_data.queueID, bot))


@router.callback_query(RemoveMyself.filter(F.queueID != 0))
async def unvoting(call: CallbackQuery, callback_data: RemoveMyself):
    result = await api.delete_queue_member_by_id(callback_data.queueID, call.from_user.id)
    if result == 'Incorrect':
        await call.answer(emojize("Чтобы выйти из очереди, нужно в неё добавиться :nerd_face:"))
    # Здесь был render_queue


@router.callback_query(FindMyself.filter(F.queueID != 0))
async def get_number(call: CallbackQuery, callback_data: FindMyself):
    try:
        member_id = await api.get_queue_member_id(callback_data.queueID, call.from_user.id)
        result = await api.get_queue_position(member_id)
        await call.answer("Ваше место в очереди - {}".format(result))
    except Exception:
        await call.answer("Попробуйте встать в очередь, чтобы узнать свою позицию")


@router.message(F.new_chat_member)
async def bot_add_to_group(message: types.Message):
    if (await bot.get_me()).id == message.new_chat_member['id']:
        await api.set_main_admin(message.chat.id, message.from_user.id, message.chat.title, message.message_thread_id)
        await cmd_startgroup(message)
    elif not message.new_chat_member['is_bot']:
        full_name = message.new_chat_member['first_name'] + (" " + message.new_chat_member['last_name'] if 'last_name' in message.new_chat_member else '')
        await api.add_user_to_group(message.chat.id, message.new_chat_member['id'], full_name,
                                    False, message.chat.title, message.message_thread_id)
    else:
        await message.answer("Конкурент обнаружен")


@router.message(F.left_chat_participant)
async def bot_delete_from_group(message: types.Message):
    if (await bot.get_me()).id == message.left_chat_participant['id']:
        await api.delete_group(message.chat.id)
    elif not message.left_chat_participant['is_bot']:
        await api.delete_group_member(message.chat.id, message.left_chat_participant['id'])
    else:
        await message.answer("Конкурент уничтожен")


@router.message(Command('help'))
async def help_command(message: types.Message):
    if message.chat.type == 'private':
        await message.answer("Если вы являетесь админом какой-либо группы, то вы можете создавать в ней очереди и дедлайны.\n"
                             "Если вы таковым не являетесь, то вы всё равно можете просмотреть очереди, в которых вы есть,"
                             " а также все дедлайны, созданные в группах с вашим участием.\n"
                             "/queue - управление очередями\n/deadline - управление дедлайнами\n"
                             "/change_tz - сменить часовой пояс\n"
                             "/")
    else:
        await message.answer("/change_topic - сменить тему, в которую бот будеть отправлять очереди и дедлайны\n"
                             "/set_main_admin - сменить главного админа (доступно только главному админу)\n"
                             "Для начала игры <b>Стипендия</b> введите команду /rating\n"
                             "/top_stipa - вывести топ-10 с самой высокой стипендией\n"
                             "/top_rating - вывести топ-10 с самым высоким рейтингом\n"
                             "/my_place - вывести своё место в топах по стипендии и по рейтингу",
                             parse_mode='html')



@router.message(Command('donate'))
async def donate_command(message: types.Message):
    if message.chat.type == 'private':
        await message.answer('Если вы желаете помочь нуждающимся студентам из Африки, то можете отправить денежную помощь на эти карточки:\n'
                            '<code>2200700731711494</code> - Тинькофф\n'
                            '<code>2202205071855735</code> - Сбер',
                            parse_mode='html')
    
