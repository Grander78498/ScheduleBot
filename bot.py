import asyncio
import logging
import datetime

import aiogram

from queue_api import api
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram import F
from aiogram.filters import ChatMemberUpdatedFilter, KICKED, MEMBER
from aiogram.types import ChatMemberUpdated
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData
from config import API_TOKEN

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)


dp = Dispatcher()

voted = {}

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


class States(StatesGroup):
    group_id = State()
    RemoveMessageyear = State()
    RemoveMessagemonth = State()
    RemoveMessageday = State()
    renameQueue = State()
    deleteQueueMember = State()
    text = State()
    year = State()
    month = State()
    day = State()
    hm = State()
    swap = State()
    tz = State()



class ReturnToQueueList(CallbackData, prefix="return"):
    messageID: int

class YearCallback(CallbackData, prefix="year"):
    year: int


class MonthCallback(CallbackData, prefix="month"):
    month: int


class DayCallback(CallbackData, prefix="day"):
    day: int


class StopVoteCallback(CallbackData, prefix="stop"):
    ID: int
    message_id: int
    queueID: int
    thread_id: int | None


class DeleteFirstQueueCallback(CallbackData, prefix="delete_first"):
    queueID: int


class GroupSelectCallback(CallbackData, prefix="selectGroup"):
    groupID: int


class QueueIDCallback(CallbackData, prefix="queueID"):
    queueID: int


class RemoveMyself(CallbackData, prefix="RemoveMyself"):
    queueID: int


class RemoveSwapRequest(CallbackData, prefix="Removeswaprequest"):
    first_user_id: int
    second_user_id: int
    first_m_id: int
    second_m_id: int
    queue_id: int


class QueueSelectCallback(CallbackData, prefix="queueSelect"):
    queueID: int
    delete_message_id: int
    queueName: str

class QueueSelectForSwapCallback(CallbackData, prefix="SwapqueueSelect"):
    queueID: int
    queueName: str


class DeleteQueueCallback(CallbackData, prefix="DeleteQueue"):
    queueID: int
    messageID : int


class DeleteQueueMemberCallback(CallbackData, prefix="DeleteQueueMember"):
    queueID: int


class RenameQueueCallback(CallbackData, prefix="RenameQueue"):
    queueID: int


class SwapCallback(CallbackData, prefix="swap"):
    message_type: str
    first_user_id: int
    first_tg_user_id: int
    queueId: int
    second_user_id: int
    message2_id: int
    message1_id: int


@dp.message(Command("queue"))
async def print_info(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="Создать очередь", callback_data="add")
    builder.button(text="Вывести существующие очереди", callback_data="print")
    builder.button(text="Запросить перемещение в очереди", callback_data="swap")
    builder.adjust(1)
    await message.answer("Здравствуйте, вам доступен следующий функционал\n", reply_markup=builder.as_markup())


@dp.message(Command("change_topic"))
async def change_topic(message: types.Message):
    ok = True if message.from_user.id in [i.user.id for i in (await bot.get_chat_administrators(message.chat.id))] else False
    if ok:
        await api.change_topic(message.chat.id, message.message_thread_id)
        await message.answer(text="Тема изменена успешно")
    else:
        try:
            await bot.send_message(text="Пошёл нахуй пидорас уёбище блядское хули лезешь не туда???",
                                   chat_id=message.from_user.id)
        except aiogram.exceptions.TelegramForbiddenError:
            pass




@dp.message(Command("start"))
async def cmd_start(message: types.Message) -> None:
    if message.chat.type == "group" or message.chat.type == "supergroup":
        chat_admins = await bot.get_chat_administrators(message.chat.id)
        d = []
        names = []
        for admin in chat_admins:
            userId = admin.user.id
            name = admin.user.full_name
            d.append(userId)
            names.append(name)
        await api.add_admin(message.chat.id, d, names, message.chat.title, message.message_thread_id)
        await message.answer(
            "Здравствуйте уважаемые пользователи, для того, чтобы создать очередь админ группы должен написать в личное сообщение боту. Если хотите сменить тему, в которой будет писать бот, то нажмите \n /change_topic")
    elif message.chat.type == "private":
        if len(str(message.text).split())>1:
            queueID = int(str(message.text).split()[1])
            await api.save_user(message.chat.id, message.from_user.full_name)
            _,_ = await api.add_user_to_queue(queueID, message.chat.id, message.from_user.full_name)
            group_id, queue_message_id, queue = await api.print_queue(queueID, False)
            try:
                builder = InlineKeyboardBuilder()
                builder.button(text="Встать в очередь",
                                   callback_data=QueueIDCallback(queueID=queueID))
                builder.button(text="Выйти из очереди", callback_data=RemoveMyself(queueID=queueID))
                builder.adjust(1)
                await bot.edit_message_text(chat_id=group_id, message_id=queue_message_id, text=queue,
                                            reply_markup=builder.as_markup(), parse_mode='MarkdownV2')
            except Exception as _ex:
                print(_ex)
            link = await api.get_queue_link(queueID)
            return_builder = InlineKeyboardBuilder()
            return_builder.button(text="Вернуться в группу", url=link)
            await message.answer("Тебя добавили в очередь", reply_markup=return_builder.as_markup())
        elif len(str(message.text).split())==1:
            builder_add = InlineKeyboardBuilder()
            builder_add.button(text="Добавить бота в группу", url="https://t.me/{}?startgroup=L&admin=pin_messages".format(await api.get_bot_name(bot)))
            await api.save_user(message.chat.id, message.from_user.full_name)
        await message.answer("Изначально часовой пояс задан 0 по Москве и 3 по Гринвичу.\n  Для его замены наберите команду /change_tz \nФункционал бота \n /queue", reply_markup=builder_add.as_markup())


@dp.message(Command("change_tz"))
async def cmd_change_tz(message: types.Message,  state: FSMContext):
    await message.answer("Введите новый часовой пояс")
    await state.set_state(States.tz)



@dp.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=KICKED))
async def user_blocked_bot(event: ChatMemberUpdated):
    await api.update_started(event.from_user.id, event.from_user.full_name, False)


@dp.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=MEMBER))
async def user_unblocked_bot(event: ChatMemberUpdated):
    await api.update_started(event.from_user.id, event.from_user.full_name, True)



async def send_swap_request(message: types.Message, second_memberId: str,from_user_id ,state: FSMContext):
    res = (await state.get_data())["swap"]
    queueID = res["queueID"]
    await bot.delete_message(chat_id=from_user_id, message_id=res["first_m"])
    await bot.delete_message(chat_id=from_user_id, message_id=res["second_m"])
    await state.clear()
    result = await api.get_user_id(await api.get_queue_member_id(queueID,from_user_id), second_memberId)
    if result["status"]!="OK":
        await message.answer(result["message"])
    else:
        mess_lichka = await message.answer(result["message"])
        try:
            mes = await bot.send_message(chat_id=result["user_id"],
                                   text="{} (место - {}) отправил(-а) запрос на обмен местами в очереди {}. Ваше текущее место - {}".format(result['first_name'], result['first_position'], result['queue_name'], result['second_position']))
            builder = InlineKeyboardBuilder()
            builder.button(text="Отклонить", callback_data=SwapCallback(message_type="Deny", first_user_id=await api.get_queue_member_id(queueID,from_user_id), first_tg_user_id=from_user_id,queueId=queueID ,second_user_id=int(second_memberId), message2_id=mes.message_id, message1_id=mess_lichka.message_id))
            builder.button(text="Принять", callback_data=SwapCallback(message_type="Accept", first_user_id=await api.get_queue_member_id(queueID,from_user_id),first_tg_user_id=from_user_id,queueId=queueID ,second_user_id=int(second_memberId), message2_id=mes.message_id, message1_id=mess_lichka.message_id))
            await bot.edit_message_reply_markup(chat_id=result["user_id"], message_id=mes.message_id,
                                                reply_markup=builder.as_markup())
            await api.handle_request(await api.get_queue_member_id(queueID,from_user_id), second_memberId)
            await api.add_request_timer(from_user_id,result["user_id"], mess_lichka.message_id, mes.message_id, queueID)

        except aiogram.exceptions.TelegramForbiddenError:
            await message.answer("Не удалось отправить запрос - пользователь {} заблокировал бота".format(result['second_name']))



async def edit_request_message(first_id: int, second_id: int, message1_id: int, message2_id: int, queue_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(text="Удалить запрос", callback_data=RemoveSwapRequest(first_m_id=message1_id,second_m_id=message2_id, first_user_id=first_id, second_user_id=second_id, queue_id=queue_id))
    try:
        await bot.edit_message_reply_markup(chat_id=first_id, message_id=message1_id,
                                            reply_markup=builder.as_markup())
    except:
        print("FFFFFFFFFFFFFFFFFFFFFFFFFFFFFF")


@dp.callback_query(RemoveSwapRequest.filter(F.first_m_id != 0))
async def remove_swap(call: CallbackQuery, callback_data: RemoveSwapRequest):
    await api.remove_request(callback_data.first_user_id, callback_data.second_user_id, callback_data.queue_id)
    await delete_request_messages(callback_data.first_m_id, callback_data.second_m_id, callback_data.first_user_id, callback_data.second_user_id)



async def delete_request_messages(first_message_id: int, second_message_id: int, chat1_id, chat2_id):
    try:
        await bot.delete_message(chat_id=chat1_id, message_id=first_message_id)
        await bot.delete_message(chat_id=chat2_id, message_id=second_message_id)
    except:
        await bot.send_message(chat_id=chat1_id, text="You are gay")
        await bot.send_message(chat_id=chat2_id, text="You are gay")


@dp.callback_query(SwapCallback.filter(F.queueId != 0))
async def swap_result(call: CallbackQuery, callback_data: SwapCallback, state: FSMContext):
    if callback_data.message_type=="Deny":
        await bot.send_message(chat_id=callback_data.first_tg_user_id,text="Ваш запрос был отклонён")
    else:
        await api.swap_places(callback_data.first_user_id, callback_data.second_user_id)
        group_id, queue_message_id, queue = await api.print_queue(callback_data.queueId, False)
        try:
            builder = InlineKeyboardBuilder()
            builder.button(text="Встать в очередь",
                           callback_data=QueueIDCallback(queueID=callback_data.queueId))
            builder.button(text="Выйти из очереди", callback_data=RemoveMyself(queueID=callback_data.queueId))
            builder.adjust(1)
            await bot.edit_message_text(chat_id=group_id, message_id=queue_message_id, text=queue,
                                        reply_markup=builder.as_markup(), parse_mode='MarkdownV2')
        except Exception as _ex:
            print(_ex)
        await bot.send_message(chat_id=callback_data.first_tg_user_id,text="Ваш запрос был удовлетворён. Вы поменяны в очереди")
    await api.remove_request(callback_data.first_tg_user_id, call.from_user.id, callback_data.queueId)
    await delete_request_messages(callback_data.message1_id, callback_data.message2_id,callback_data.first_tg_user_id ,call.from_user.id)
    await call.answer()



@dp.callback_query(F.data.in_(['swap']))
async def swap(call: CallbackQuery, state: FSMContext):
    queueList, lenq, st, names = await api.get_user_queues(call.from_user.id)
    if lenq==0:
        await call.message.answer(st)
    if lenq > 0:
        r = await call.message.answer(st)
        builder = InlineKeyboardBuilder()
        for i in range(lenq):
            builder.button(text="{}".format(i + 1),
                           callback_data=QueueSelectForSwapCallback(queueID=queueList[i],
                                                             queueName=names[i]))
        builder.adjust(4)
        await bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=r.message_id,
                                            reply_markup=builder.as_markup())
    await call.answer()




@dp.callback_query(QueueSelectForSwapCallback.filter(F.queueID != 0))
async def swap_print(call: CallbackQuery, callback_data: QueueSelectForSwapCallback, state: FSMContext):
    status = await api.check_requests(call.from_user.id, callback_data.queueID)
    if not status["in"] and not status["out"]:
        _,_, text = await api.print_queue(callback_data.queueID, call.message.chat.type=="private")
        queue_list_message = await call.message.answer(text, parse_mode="MarkdownV2")
        simple_message = await call.message.answer("Скопируйте id пользователя из очереди и отправьте в сообщении")
        await state.set_state(States.swap)
        res = {"queueID":callback_data.queueID, "first_m":queue_list_message.message_id, "second_m":simple_message.message_id}
        await state.update_data(swap=res)
        await call.answer()
    elif status["in"]:
        await call.answer("У вас есть нерассмотренный входящий запрос")
    elif status["out"]:
        await call.answer("У вас уже есть отправленный запрос, если прошло достаточно времени, вы можете его удалить")
    else:
        await call.answer("Долбоёб, как ты это вообще сделал, админам бота пиши тварь")




@dp.callback_query(GroupSelectCallback.filter(F.groupID != 0))
async def groupSelected(call: CallbackQuery, callback_data: GroupSelectCallback, state: FSMContext):
    await state.update_data(group_id=callback_data.groupID)
    await call.message.answer("Напишите сообщение для добавления")
    await state.set_state(States.text)
    await call.answer()


@dp.callback_query(F.data.in_(['add']))
async def addNotification(call: CallbackQuery, state: FSMContext):
    if call.message.chat.type == "private":
        groups = await api.check_admin(call.message.chat.id)
        if len(groups) == 0:
            builder = InlineKeyboardBuilder()
            builder.button(text="Создать очередь", callback_data="add")
            builder.button(text="Вывести существующие очереди", callback_data="print")
            builder.button(text="Запросить перемещение в очереди", callback_data="swap")
            builder.adjust(1)
            await call.message.answer("У тебя нет групп, где ты админ", reply_markup=builder.as_markup())
        else:
            builder = InlineKeyboardBuilder()
            for group in groups:
                builder.button(text=group.name,
                               callback_data=GroupSelectCallback(groupID=group.tg_id))
            builder.adjust(1)
            await call.message.answer("У тебя есть доступ к этим группам", reply_markup=builder.as_markup())
    await call.answer()


@dp.callback_query(F.data.in_(['print']))
async def printQueue(call: CallbackQuery, state: FSMContext):
    queueList, lenq, st, names = await api.get_creator_queues(call.from_user.id)
    if lenq==0:
        await call.message.answer(st)
    if lenq > 0:
        r = await call.message.answer(st)
        builder = InlineKeyboardBuilder()
        for i in range(lenq):
            builder.button(text="{}".format(i + 1),
                           callback_data=QueueSelectCallback(queueID=queueList[i], delete_message_id=r.message_id,
                                                             queueName=names[i]))
        builder.adjust(4)
        await bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=r.message_id,
                                            reply_markup=builder.as_markup())
    await call.answer()


@dp.callback_query(ReturnToQueueList.filter(F.messageID!=0))
async def printQueue_returned(call: CallbackQuery, callback_data : ReturnToQueueList, state: FSMContext):
    queueList,lenq,st, names = await api.get_creator_queues(call.from_user.id)
    r = await bot.edit_message_text(text=st, chat_id=call.message.chat.id, message_id=callback_data.messageID)
    if lenq==0:
        uilder = InlineKeyboardBuilder()
        await bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=callback_data.messageID,
                                            reply_markup=uilder.as_markup())
    if lenq>0:
        builder = InlineKeyboardBuilder()
        for i in range(lenq):
            builder.button(text="{}".format(i+1), callback_data=QueueSelectCallback(queueID=queueList[i], delete_message_id = r.message_id, queueName=names[i]))
        builder.adjust(4)
        await bot.edit_message_reply_markup(chat_id=call.message.chat.id,message_id=r.message_id, reply_markup= builder.as_markup())
    await call.answer()

@dp.callback_query(QueueSelectCallback.filter(F.queueID != 0))
async def QueueChosen(call: CallbackQuery, callback_data: QueueSelectCallback):
    builder = InlineKeyboardBuilder()
    builder.button(text="Изменить название очереди", callback_data=RenameQueueCallback(queueID=callback_data.queueID))
    builder.button(text="Удалить участника очереди",
                   callback_data=DeleteQueueMemberCallback(queueID=callback_data.queueID))
    builder.button(text="Удалить очередь", callback_data=DeleteQueueCallback(queueID=callback_data.queueID, messageID=call.message.message_id))
    builder.button(text="Удалить первого из очереди", callback_data=DeleteFirstQueueCallback(queueID=callback_data.queueID))
    builder.button(text="\u25C0", callback_data=ReturnToQueueList(messageID=call.message.message_id))
    builder.adjust(2)
    await bot.edit_message_text(text="Выбрана очередь {}".format(callback_data.queueName), chat_id=call.message.chat.id,
                                message_id=callback_data.delete_message_id)
    await bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=callback_data.delete_message_id,
                                        reply_markup=builder.as_markup())

    # Удалить очередь, удалить участника, изменить название, кнопка назад

    await call.answer()


@dp.callback_query(DeleteFirstQueueCallback.filter(F.queueID != 0))
async def remove_first(call: CallbackQuery, callback_data: DeleteFirstQueueCallback):
    res = await api.remove_first(callback_data.queueID)
    if not res:
        await call.answer("Данная очередь пуста")
    else:
        group_id, queue_message_id, queue = await api.print_queue(callback_data.queueID, call.message.chat.type == "private")
        builder = InlineKeyboardBuilder()
        builder.button(text="Встать в очередь", callback_data=QueueIDCallback(queueID=callback_data.queueID))
        builder.button(text="Выйти из очереди", callback_data=RemoveMyself(queueID=callback_data.queueID))
        builder.adjust(1)
        await bot.edit_message_text(text=queue, chat_id=group_id, message_id=queue_message_id,
                                    reply_markup=builder.as_markup(), parse_mode='MarkdownV2')
        await call.answer()



@dp.callback_query(DeleteQueueMemberCallback.filter(F.queueID != 0))
async def delete_queue_member(call: CallbackQuery, callback_data: DeleteQueueMemberCallback, state: FSMContext):
    _, _, message = await api.print_queue(callback_data.queueID, call.message.chat.type == "private")
    await call.message.answer(text=message, parse_mode='MarkdownV2')
    await call.message.answer("Введите номер удаляемого участника")
    await state.set_state(States.deleteQueueMember)
    await state.update_data(deleteQueueMember=callback_data.queueID)
    await call.answer()


@dp.callback_query(RenameQueueCallback.filter(F.queueID != 0))
async def rename_queue(call: CallbackQuery, callback_data: RenameQueueCallback, state: FSMContext):
    await call.message.answer("Введите новое название очереди")
    await state.set_state(States.renameQueue)
    await state.update_data(renameQueue=callback_data.queueID)
    await call.answer()


@dp.callback_query(DeleteQueueCallback.filter(F.queueID != 0))
async def deleted_queue(call: CallbackQuery, callback_data: DeleteQueueCallback):
    group_id, message_id = await api.delete_queue(callback_data.queueID)
    if message_id is not None:
        try:
            await bot.delete_message(chat_id=group_id, message_id=message_id)
            await bot.delete_message(chat_id=call.message.chat.id, message_id=callback_data.messageID)
        except:
            await call.answer("Очередь перестала быть активной, но удалить сообщение не удалось так как оно старое")
    builder = InlineKeyboardBuilder()
    builder.button(text="Создать очередь", callback_data="add")
    builder.button(text="Вывести существующие очереди", callback_data="print")
    builder.button(text="Запросить перемещение в очереди", callback_data="swap")
    builder.adjust(1)
    await call.message.answer("Очередь удалена", reply_markup=builder.as_markup())
    await call.answer()


@dp.callback_query(DayCallback.filter(F.day != 0))
async def Day(call: CallbackQuery, callback_data: DayCallback, state: FSMContext):
    if call.message.chat.type == "private":
        await state.update_data(day=callback_data.day)
        await state.set_state(States.hm)
        await call.message.answer("Введите время в формате ЧЧ:ММ")
        await call.answer()


@dp.callback_query(MonthCallback.filter(F.month != 0))
async def Month(call: CallbackQuery, callback_data: MonthCallback, state: FSMContext):
    if call.message.chat.type == "private":
        await state.update_data(month=callback_data.month)
        await state.set_state(States.day)
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


@dp.callback_query(YearCallback.filter(F.year != 0))
async def Year(call: CallbackQuery, callback_data: YearCallback, state: FSMContext):
    if call.message.chat.type == "private":
        await state.update_data(year=callback_data.year)
        await state.set_state(States.month)
        builder = InlineKeyboardBuilder()
        a = 1
        if datetime.datetime.now().year == callback_data.year:
            a = datetime.datetime.now().month
        for i in range(a, 13):
            builder.button(text="{}".format(months[i][0]), callback_data=MonthCallback(month=int(i)))
        builder.adjust(3)
        remove = await state.get_data()
        remove = remove["RemoveMessageyear"] if "RemoveMessageyear" in remove else None
        # r = 0
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


async def putInDb(message: Message, state: FSMContext) -> None:
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
    thread_id, date, queue_id = await api.add_queue(data)
    builder = InlineKeyboardBuilder()
    builder.button(text="Создать очередь", callback_data="add")
    builder.button(text="Вывести существующие очереди", callback_data="print")
    builder.button(text="Запросить перемещение в очереди", callback_data="swap")
    builder.adjust(1)
    await message.answer("Очередь была создана", reply_markup=builder.as_markup())
    mes = await bot.send_message(chat_id=data['group_id'], message_thread_id=thread_id,
                           text="Очередь {} будет создана {}. За час до этого будет отправлено напоминание".format(
                               data['text'], date))
    await api.update_message_id(queue_id, mes.message_id)
    await api.create_queue_tasks(queue_id, data["group_id"])





@dp.callback_query(F.data.in_(['custom']))
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
    await state.set_state(States.year)


@dp.callback_query(F.data.in_(['now']))
async def now_time(call: CallbackQuery, state: FSMContext):
    now = datetime.datetime.now()
    await state.update_data(year=now.year)
    await state.update_data(month=now.month)
    await state.update_data(day=now.day)
    await state.update_data(hm="{:02d}:{:02d}".format(now.hour, now.minute))
    await putInDb(call.message, state)
    await call.answer()



@dp.callback_query(F.data.in_(['one_hour']))
async def next_hour(call: CallbackQuery, state: FSMContext):
    now = datetime.datetime.now()+datetime.timedelta(hours=1)
    await state.update_data(year=now.year)
    await state.update_data(month=now.month)
    await state.update_data(day=now.day)
    await state.update_data(hm="{:02d}:{:02d}".format(now.hour, now.minute))
    await putInDb(call.message, state)
    await call.answer()


@dp.callback_query(F.data.in_(['today']))
async def tomorrow(call: CallbackQuery, state: FSMContext):
    now = datetime.datetime.now()
    await state.update_data(year=now.year)
    await state.update_data(month=now.month)
    await state.update_data(day=now.day)
    await state.set_state(States.hm)
    await call.message.answer("Введите время в формате ЧЧ:ММ")
    await call.answer()
@dp.callback_query(F.data.in_(['tomorrow']))
async def tomorrow(call: CallbackQuery, state: FSMContext):
    now = datetime.datetime.now()+datetime.timedelta(days=1)
    await state.update_data(year=now.year)
    await state.update_data(month=now.month)
    await state.update_data(day=now.day)
    await state.set_state(States.hm)
    await call.message.answer("Введите время в формате ЧЧ:ММ")
    await call.answer()

async def short_cut(message: Message, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.button(text="Сейчас",callback_data="now")
    builder.button(text="Через час",callback_data="one_hour")
    builder.button(text="Сегодня",callback_data="today")
    builder.button(text="Завтра",callback_data="tomorrow")
    builder.button(text="Задать самостоятельно",callback_data="custom")
    builder.adjust(2)
    await message.answer("Выберите время", reply_markup=builder.as_markup())


@dp.message(F.text)
async def echo(message: Message, state: FSMContext) -> None:
    st = await state.get_state()
    if message.chat.type == "private":
        if st == States.text:
            await state.update_data(text=message.text)
            await short_cut(message, state)
        elif st == States.swap:
            await send_swap_request(message, message.text, message.chat.id, state)
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        elif st == States.hm:
            data = await state.get_data()
            t = api.check_time(message.text, data["year"], data["month"], data["day"])
            match t:
                case "TimeError":
                    await message.answer("Неправильно, попробуйте ещё раз")
                case "EarlyQueueError":
                    await message.answer("Очередь задана слишком рано, можно задавать минимум через 2 часа")
                case _:
                    await state.update_data(hm=message.text)
                    await putInDb(message, state)
        elif st == States.tz:
            res = await api.change_tz(message.chat.id, message.text)
            if res["status"]=="OK":
                await state.clear()
            await message.answer(res["message"])
        elif st == States.renameQueue:
            data = await state.get_data()
            await api.rename_queue(data["renameQueue"], message.text)
            group_id, queue_message_id, queue = await api.print_queue(data["renameQueue"], message.chat.type == "private")
            try:
                builder = InlineKeyboardBuilder()
                builder.button(text="Встать в очередь", callback_data=QueueIDCallback(queueID=data["renameQueue"]))
                builder.button(text="Выйти из очереди", callback_data=RemoveMyself(queueID=data["renameQueue"]))
                builder.adjust(1)
                await bot.edit_message_text(chat_id=group_id, message_id=queue_message_id, text=queue,
                                            reply_markup=builder.as_markup(), parse_mode='MarkdownV2')
            except Exception as _ex:
                print(_ex)
            builder = InlineKeyboardBuilder()
            builder.button(text="Создать очередь", callback_data="add")
            builder.button(text="Вывести существующие очереди", callback_data="print")
            builder.button(text="Запросить перемещение в очереди", callback_data="swap")
            builder.adjust(1)
            await message.answer("Название очереди было успешно изменено", reply_markup=builder.as_markup())

        elif st == States.deleteQueueMember:
            data = await state.get_data()
            result = await api.delete_queue_member(message.text)
            match result:
                case "Incorrect":
                    await message.answer("Введён некорректный номер, попробуйте ещё раз")
                case "Doesn't exist":
                    await message.answer('Введённой позиции в очереди нет')
                case _:

                    group_id, queue_message_id, queue = await api.print_queue(data["deleteQueueMember"], message.chat.type == "private")
                    try:
                        builder = InlineKeyboardBuilder()
                        builder.button(text="Встать в очередь",
                                       callback_data=QueueIDCallback(queueID=data["deleteQueueMember"]))
                        builder.button(text="Выйти из очереди", callback_data=RemoveMyself(queueID=data["deleteQueueMember"]))
                        builder.adjust(1)
                        await bot.edit_message_text(chat_id=group_id, message_id=queue_message_id, text=queue,
                                                    reply_markup=builder.as_markup(), parse_mode='MarkdownV2')
                    except Exception as _ex:
                        print(_ex)
                    builder = InlineKeyboardBuilder()
                    builder.button(text="Создать очередь", callback_data="add")
                    builder.button(text="Вывести существующие очереди", callback_data="print")
                    builder.button(text="Запросить перемещение в очереди", callback_data="swap")
                    builder.adjust(1)
                    await message.answer("Участник был успешно удалён", reply_markup=builder.as_markup())
        else:
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)


@dp.callback_query(StopVoteCallback.filter(F.ID != 0))
async def stopvoting(call: CallbackQuery, callback_data: StopVoteCallback):
    st = await api.print_queue(callback_data.queueID, call.message.chat.type == "private")
    await bot.send_message(chat_id=callback_data.ID, text=st, message_thread_id=callback_data.thread_id,
                           parse_mode='MarkdownV2')
    await bot.delete_message(chat_id=callback_data.ID, message_id=callback_data.message_id)
    await call.answer()


async def queue_send(queue_id, thread_id, group_id, message):
    builder = InlineKeyboardBuilder()
    queue_message_id = await api.get_message_id(queue_id)
    await bot.delete_message(chat_id=group_id, message_id=queue_message_id)
    builder.button(text="Встать в очередь", callback_data=QueueIDCallback(queueID=queue_id))
    builder.button(text="Выйти из очереди", callback_data=RemoveMyself(queueID=queue_id))
    builder.adjust(1)
    mess = await bot.send_message(text=message, chat_id=group_id, message_thread_id=thread_id,
                                reply_markup=builder.as_markup(), parse_mode='MarkdownV2')
    await api.update_message_id(queue_id, mess.message_id)


async def queue_notif_send(queue_id, thread_id, group_id, message):
    mess_id = await api.get_message_id(queue_id)
    await bot.delete_message(chat_id=group_id, message_id=mess_id)
    a = await bot.send_message(chat_id=group_id, text=message, message_thread_id=thread_id)
    await api.update_message_id(queue_id, a.message_id)


# async def scheduler():
#     while True:
#         already_queue = logic.already_queue()
#         hour_not = logic.get_queue_notif()
#         for i in already_queue:
#             await queue_send(i["queue_id"], i["thread_id"], i["group_id"], i["message"])
#         for i in hour_not:
#             await queue_notif_send(i["queue_id"], i["thread_id"], i["group_id"], i["message"])
#         await asyncio.sleep(20)


@dp.callback_query(QueueIDCallback.filter(F.queueID != 0))
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
                try:
                    group_id, queue_message_id, queue = await api.print_queue(callback_data.queueID, call.message.chat.type == "private")
                    builder = InlineKeyboardBuilder()
                    builder.button(text="Встать в очередь", callback_data=QueueIDCallback(queueID=callback_data.queueID))
                    builder.button(text="Выйти из очереди", callback_data=RemoveMyself(queueID=callback_data.queueID))
                    builder.adjust(1)
                    await bot.edit_message_text(text=queue, chat_id=group_id, message_id=queue_message_id,
                                                reply_markup=builder.as_markup(), parse_mode='MarkdownV2')
                except Exception as ex:
                    print("Пришли решалы сдавать работы")
                await call.answer()
        else:
            await call.answer(url="https://t.me/{}?start={}".format(await api.get_bot_name(bot), callback_data.queueID))


@dp.callback_query(RemoveMyself.filter(F.queueID != 0))
async def unvoting(call: CallbackQuery, callback_data: RemoveMyself):
    result = await api.delete_queue_member_by_id(callback_data.queueID, call.from_user.id)
    if result == 'Incorrect':
        await call.answer("Вы мертвы")
    else:
        try:
            group_id, queue_message_id, queue = await api.print_queue(callback_data.queueID, call.message.chat.type == "private")
            builder = InlineKeyboardBuilder()
            builder.button(text="Встать в очередь", callback_data=QueueIDCallback(queueID=callback_data.queueID))
            builder.button(text="Выйти из очереди", callback_data=RemoveMyself(queueID=callback_data.queueID))
            builder.adjust(1)
            await bot.edit_message_text(text=queue, chat_id=group_id, message_id=queue_message_id,
                                        reply_markup=builder.as_markup(), parse_mode='MarkdownV2')
        except Exception as ex:
            print("Скорочстрелы")
    # передаётся callback_data.queueID, call.from_user.id Это id очереди и id нажавшего

async def main():
    logging.basicConfig(level=logging.INFO)
    # asyncio.create_task(scheduler())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
