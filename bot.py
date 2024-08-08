import asyncio
import logging
import aiogram
import datetime
from dateutil.relativedelta import relativedelta
from django.conf import settings

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
from config import config
from queue_api.api import EventType

from emoji import emojize

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
bot = Bot(token=config.bot_token.get_secret_value())


async def get_bot_name():
    return (await bot.get_me()).username

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
    sec = State()
    swap = State()
    tz = State()
    event_type = State()
    deadline_roots = State()
    set_main_admin = State()


class ReturnToQueueList(CallbackData, prefix="return"):
    messageID: int


class YearCallback(CallbackData, prefix="year"):
    year: int


class MonthCallback(CallbackData, prefix="month"):
    month: int


class DayCallback(CallbackData, prefix="day"):
    day: int


class DeleteFirstQueueCallback(CallbackData, prefix="delete_first"):
    queueID: int


class GroupSelectCallback(CallbackData, prefix="selectGroup"):
    groupID: int
    is_admin: bool


class QueueIDCallback(CallbackData, prefix="queueID"):
    queueID: int


class RemoveMyself(CallbackData, prefix="RemoveMyself"):
    queueID: int


class FindMyself(CallbackData, prefix="FindMyself"):
    queueID: int


class RemoveSwapRequest(CallbackData, prefix="Rsq"):
    first_user_id: int
    second_user_id: int
    first_m_id: int
    second_m_id: int
    queue_id: int


class AdminQueueSelectCallback(CallbackData, prefix="aqs"):
    queueID: int
    delete_message_id: int
    queueName: str

class SimpleQueueSelectCallback(CallbackData, prefix="sqs"):
    queueID: int
    delete_message_id: int
    queueName: str

class QueueSelectForSwapCallback(CallbackData, prefix="qss"):
    queueID: int
    queueName: str


class DeleteQueueCallback(CallbackData, prefix="DeleteQueue"):
    queueID: int
    messageID: int


class DeleteQueueMemberCallback(CallbackData, prefix="DeleteQueueMember"):
    queueID: int


class RenameQueueCallback(CallbackData, prefix="RenameQueue"):
    queueID: int


class SwapCallback(CallbackData, prefix="sp"):
    message_type: str
    first_user_id: int
    first_tg_user_id: int
    queueId: int
    second_user_id: int
    message2_id: int
    message1_id: int

class DeadLineAcceptCallback(CallbackData, prefix="da"):
    deadline_id: int
    user_id: int
    message_id: int
    solution: bool

class CanbanDesk(CallbackData, prefix="cd"):
    deadline_status_id: int
    is_done: bool
    message_id: int

class DeadStatus(CallbackData, prefix="ds"):
    deadline_status_id: int
    is_done: bool
    message_id: int
    d_type: str
    del_mes: int

class QueueSwapPagination(CallbackData, prefix="qsp"):
    offset: int
    message_id: int

class QueuePagination(CallbackData, prefix="qp"):
    offset: int
    message_id: int


class DeadPagination(CallbackData, prefix="dp"):
    offset: int
    message_id: int


@dp.message(Command("queue"))
async def print_info_queue(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="Создать очередь", callback_data="add_queue")
    builder.button(text="Вывести существующие очереди", callback_data="print_queue")
    builder.button(text="Запросить перемещение в очереди", callback_data="swap")
    builder.adjust(1)
    await message.answer("Здравствуйте, вам доступен следующий функционал\n", reply_markup=builder.as_markup())

@dp.message(Command("set_main_admin"))
async def set_main_admin(message: types.Message, state: FSMContext):
    if message.chat.type=="private":
        await message.answer("Данная команда доступна только в группе")
    elif message.chat.type == "supergroup":
        res = await api.check_main_admin(message.chat.id, message.from_user.id)
        if res['status'] == 'ERROR':
            mes = await message.answer(res['message'])
            await asyncio.sleep(5)
            await bot.delete_message(chat_id=message.chat.id, message_id=mes.message_id)
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
            await state.update_data(set_main_admin={"message_id":message.message_id, "status":"ERROR"})
            await state.set_state(States.set_main_admin)
        else:
            await state.update_data(set_main_admin={"message_id":message.message_id, "status":"OK"})
            await state.set_state(States.set_main_admin)


@dp.message(Command("deadline"))
async def print_info_deadline(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="Создать напоминание", callback_data="add_deadline")
    builder.button(text="Вывести существующие напоминания", callback_data="print_deadline")
    builder.adjust(1)
    await message.answer("Здравствуйте, вам доступен следующий функционал\n", reply_markup=builder.as_markup())


@dp.message(Command("change_topic"))
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
        await api.add_admin(message.chat.id, d, names, message.chat.title, message.message_thread_id)
        if not settings.DEBUG:
            from queue_api.tasks import task_get_users
            result = task_get_users.delay(message.chat.id, (await bot.get_me()).id)
            await message.answer(
                "Здравствуйте, уважаемые пользователи! Для того, чтобы создать очередь, админ группы должен написать в личное сообщение боту. Если хотите сменить тему, в которой будет писать бот, то нажмите \n /change_topic")
            users = result.get()
            for user in users:
                await api.add_user_to_group(message.chat.id, user['id'], user['full_name'],
                                            False, message.chat.title, message.message_thread_id)
        else:
            await message.answer(
                "Здравствуйте, уважаемые пользователи! Для того, чтобы создать очередь, админ группы должен написать в личное сообщение боту. Если хотите сменить тему, в которой будет писать бот, то нажмите \n /change_topic")


@dp.message(Command("start"))
async def cmd_start(message: types.Message) -> None:
    if message.chat.type == "private":
        if len(str(message.text).split()) > 1:
            if str(message.text).split()[1].startswith("queue_add"):
                queueID = int(str(message.text).split()[1][9:])
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
                "Изначально часовой пояс задан 0 по Москве и 3 по Гринвичу.\n  Для его замены наберите команду /change_tz \nФункционал бота \n Создание и управление очередями /queue \n СОздание и управление дедлайнами /deadline",
                reply_markup=builder_add.as_markup())
    elif message.chat.type == "supergroup":
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)


@dp.message(Command("change_tz"))
async def cmd_change_tz(message: types.Message, state: FSMContext):
    await message.answer("Введите новый часовой пояс")
    await state.set_state(States.tz)


@dp.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=KICKED))
async def user_blocked_bot(event: ChatMemberUpdated):
    await api.update_started(event.from_user.id, event.from_user.full_name, False)


@dp.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=MEMBER))
async def user_unblocked_bot(event: ChatMemberUpdated):
    if event.chat.type == "group" or event.chat.type == "supergroup":
        await api.update_started(event.from_user.id, event.from_user.full_name, True)


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


@dp.callback_query(RemoveSwapRequest.filter(F.first_m_id != 0))
async def remove_swap(call: CallbackQuery, callback_data: RemoveSwapRequest):
    await api.remove_request(callback_data.first_user_id, callback_data.second_user_id, callback_data.queue_id)
    await delete_request_messages(callback_data.first_m_id, callback_data.second_m_id, callback_data.first_user_id,
                                  callback_data.second_user_id)


async def delete_request_messages(first_message_id: int, second_message_id: int, chat1_id, chat2_id):
    try:
        await bot.delete_message(chat_id=chat1_id, message_id=first_message_id)
        await bot.delete_message(chat_id=chat2_id, message_id=second_message_id)
    except:
        await bot.send_message(chat_id=chat1_id, text="You are gay")
        await bot.send_message(chat_id=chat2_id, text="You are gay")


@dp.callback_query(SwapCallback.filter(F.queueId != 0))
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


@dp.callback_query(QueueSwapPagination.filter(F.offset != -1))
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



@dp.callback_query(QueuePagination.filter(F.offset != -1))
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




@dp.callback_query(F.data.in_(['swap']))
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


@dp.callback_query(F.data.in_(['print_deadline']))
async def printDeadline(call: CallbackQuery, state: FSMContext):
    res = await api.get_deadlines(call.from_user.id, 0)
    builder = InlineKeyboardBuilder()
    if res["status"]!="OK":
        builder.button(text="Создать напоминание", callback_data="add_deadline")
        builder.button(text="Вывести существующие напоминания", callback_data="print_deadline")
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



@dp.callback_query(DeadPagination.filter(F.offset != -1))
async def dead_pagin(call: CallbackQuery, callback_data: DeadPagination):
    _dict = await api.get_deadlines(call.from_user.id, callback_data.offset)
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






@dp.callback_query(F.data.in_(['add_deadline']))
async def add_deadline(call: CallbackQuery, state: FSMContext):
    if call.message.chat.type == "private":
        res = await api.check_event_count(call.from_user.id, EventType.DEADLINE)
        if res['status'] == 'ERROR':
            await call.answer(res['message'])
        else:
            groups = await api.get_user_groups(call.message.chat.id)
            if len(groups) == 0:
                await call.answer("Вы не состоите ни в одной группе, лох")
            else:
                builder = InlineKeyboardBuilder()
                await state.update_data(event_type=EventType.DEADLINE)
                for group, is_admin in groups:
                    builder.button(text=group.name,
                                   callback_data=GroupSelectCallback(groupID=group.tg_id, is_admin=is_admin))
                builder.adjust(1)
                await call.message.answer("У тебя есть доступ к этим группам", reply_markup=builder.as_markup())
            await call.answer()


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

@dp.callback_query(CanbanDesk.filter(F.deadline_status_id != 0))
async def deadline_status_info(call: CallbackQuery, callback_data: CanbanDesk):
    is_done = callback_data.is_done
    check = await api.check_deadline_status(callback_data.deadline_status_id)
    if not check:
        await call.answer("О нет, дедлайн был магическим образом удалён, как же так")
        res = await api.get_deadlines(call.from_user.id, 0)
        await update_deadline_info(res, call.from_user.id, callback_data.message_id)
    else:
        deadline_name = await api.get_deadline_name(callback_data.deadline_status_id)
        builder = InlineKeyboardBuilder()
        mes = await call.message.answer("Вы выбрали дедлайн {}, вам доступны след. действия".format(deadline_name))
        if is_done:
            builder.button(text="Удалить дедлайн".format(deadline_name), callback_data=DeadStatus(deadline_status_id=callback_data.deadline_status_id, is_done=is_done, message_id=callback_data.message_id, d_type="delete", del_mes = mes.message_id))
            builder.button(text="Изменить статус".format(deadline_name), callback_data=DeadStatus(deadline_status_id=callback_data.deadline_status_id, is_done=is_done, message_id=callback_data.message_id, d_type="change", del_mes = mes.message_id))
        else:
            builder.button(text="Изменить статус".format(deadline_name), callback_data=DeadStatus(deadline_status_id=callback_data.deadline_status_id, is_done=is_done, message_id=callback_data.message_id, d_type="change", del_mes = mes.message_id))
        await bot.edit_message_reply_markup(chat_id=call.from_user.id, message_id=mes.message_id, reply_markup=builder.as_markup())
        await call.answer()


@dp.callback_query(DeadStatus.filter(F.deadline_status_id != 0))
async def deadline_status_change(call: CallbackQuery, callback_data: DeadStatus):
    if callback_data.d_type=="delete":
        await api.delete_deadline_status(callback_data.deadline_status_id)
        await bot.delete_message(chat_id=call.from_user.id, message_id=callback_data.del_mes)
    else:
        await api.update_done_status(callback_data.deadline_status_id)
        await bot.delete_message(chat_id=call.from_user.id, message_id=callback_data.del_mes)
    res = await api.get_deadlines(call.from_user.id, 0)
    await update_deadline_info(res, call.from_user.id, callback_data.message_id)
    await call.answer()        

    

@dp.callback_query(QueueSelectForSwapCallback.filter(F.queueID != 0))
async def swap_print(call: CallbackQuery, callback_data: QueueSelectForSwapCallback, state: FSMContext):
    status = await api.check_requests(call.from_user.id, callback_data.queueID)
    if not status["in"] and not status["out"]:
        _, text, _ = await api.print_queue(callback_data.queueID, call.message.chat.type == "private", await get_bot_name())
        queue_list_message = await call.message.answer(text, parse_mode="MarkdownV2")
        simple_message = await call.message.answer("Скопируйте id пользователя из очереди и отправьте в сообщении")
        await state.set_state(States.swap)
        res = {"queueID": callback_data.queueID, "first_m": queue_list_message.message_id,
               "second_m": simple_message.message_id}
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
    await state.update_data(deadline_roots=callback_data.is_admin)
    await call.message.answer("Напишите сообщение для добавления")
    await state.set_state(States.text)
    await call.answer()


@dp.callback_query(F.data.in_(['add_queue']))
async def add_queue(call: CallbackQuery, state: FSMContext):
    if call.message.chat.type == "private":
        res = await api.check_event_count(call.from_user.id, EventType.DEADLINE)
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
                await call.message.answer("У тебя есть доступ к этим группам", reply_markup=builder.as_markup())
            await call.answer()


@dp.callback_query(F.data.in_(['print_queue']))
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


@dp.callback_query(ReturnToQueueList.filter(F.messageID != 0))
async def printQueue_returned(call: CallbackQuery, callback_data: ReturnToQueueList, state: FSMContext):
    _dict = await api.get_all_queues(call.from_user.id, 0, False)
    status = _dict["status"]
    r = await bot.edit_message_text(text=_dict["message"], chat_id=call.message.chat.id,
                                    message_id=callback_data.messageID, parse_mode='MarkdownV2')
    if status!="OK":
        await call.message.answer(_dict["message"])
        uilder = InlineKeyboardBuilder()
        await bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=callback_data.messageID,
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
        await bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=r.message_id,
                                            reply_markup=builder.as_markup())
    await call.answer()



@dp.callback_query(SimpleQueueSelectCallback.filter(F.queueID != 0))
async def SimpleQueueChosen(call: CallbackQuery, callback_data: SimpleQueueSelectCallback):
    message_id = await api.get_message_id(callback_data.queueID, call.from_user.id)
    _,string,_ = await api.print_private_queue(callback_data.queueID, call.from_user.id,  await get_bot_name())
    if message_id is not None:
        try:
            await bot.edit_message_text(text=string, chat_id=call.from_user.id, message_id=message_id,
                                        parse_mode='MarkdownV2')
        except Exception:
            pass
        await call.answer('Сообщение с этой очередью было изменено')
    else:
        mes = await call.message.answer(string, parse_mode='MarkdownV2')
        await api.update_message_id(callback_data.queueID, mes.message_id, call.from_user.id)
        await call.answer()



@dp.callback_query(AdminQueueSelectCallback.filter(F.queueID != 0))
async def AdminQueueChosen(call: CallbackQuery, callback_data: AdminQueueSelectCallback):
    builder = InlineKeyboardBuilder()
    builder.button(text="Изменить название очереди", callback_data=RenameQueueCallback(queueID=callback_data.queueID))
    builder.button(text="Удалить участника очереди",
                   callback_data=DeleteQueueMemberCallback(queueID=callback_data.queueID))
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


@dp.callback_query(DeleteFirstQueueCallback.filter(F.queueID != 0))
async def remove_first(call: CallbackQuery, callback_data: DeleteFirstQueueCallback):
    res = await api.remove_first(callback_data.queueID)
    if not res:
        await call.answer("Данная очередь пуста")
    # Здесь был render queue
    await call.answer()


@dp.callback_query(DeleteQueueMemberCallback.filter(F.queueID != 0))
async def delete_queue_member(call: CallbackQuery, callback_data: DeleteQueueMemberCallback, state: FSMContext):
    _, _, message = await api.print_queue(callback_data.queueID, call.message.chat.type == "private", await get_bot_name())
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
    await bot.delete_message(chat_id=call.message.chat.id, message_id=callback_data.messageID)
    chat_list, message_list = await api.delete_queue(callback_data.queueID)
    for chat_id, message_id in zip(chat_list, message_list):
        try:
            await bot.delete_message(chat_id=chat_id, message_id=message_id)
        except Exception:
            await call.answer("Очередь перестала быть активной, но удалить сообщение не удалось")
    await call.answer("Очередь удалена")


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



@dp.callback_query(DeadLineAcceptCallback.filter(F.deadline_id != 0))
async def DeadlineSolution(call: CallbackQuery, callback_data: DeadLineAcceptCallback):
    group_id, text, thread_id, date, notif_date = await api.get_deadline_info(callback_data.deadline_id)
    await api.delete_deadline_request(callback_data.user_id, group_id)
    if callback_data.solution:
        await bot.send_message(chat_id=callback_data.user_id, text="Ваш запрос выполнен")
        mes = await bot.send_message(chat_id=group_id, message_thread_id=thread_id,
                                         text="Ваша смертная линия {} наступит через {}.".format(text, date,
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
    builder = InlineKeyboardBuilder()
    if data["event_type"] == EventType.QUEUE:
        thread_id, date, queue_id, notif_date = await api.create_queue_or_deadline(data)
        builder.button(text="Создать очередь", callback_data="add_queue")
        builder.button(text="Вывести существующие очереди", callback_data="print_queue")
        builder.button(text="Запросить перемещение в очереди", callback_data="swap")
        builder.adjust(1)
        await message.answer("Очередь была создана", reply_markup=builder.as_markup())
        mes = await bot.send_message(chat_id=data['group_id'], message_thread_id=thread_id,
                                     text="Очередь {} будет создана через {}.".format(data['text'], date, notif_date) +
                                          (" За {} до этого будет отправлено напоминание".format(notif_date)
                                           if notif_date != "" else ""))
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
                                         text="Ваша смертная линия {} наступит через {}.".format(data['text'], date,
                                                                                                 notif_date) +
                                              (" За {} до этого будет отправлено напоминание, чтобы успели убежать".format(
                                                  notif_date)
                                               if notif_date != "" else ""))
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
    await call.answer()


@dp.callback_query(F.data.in_(['now']))
async def now_time(call: CallbackQuery, state: FSMContext):
    now = datetime.datetime.now()
    await state.update_data(year=now.year)
    await state.update_data(month=now.month)
    await state.update_data(day=now.day)
    await state.update_data(hm="{:02d}:{:02d}".format(now.hour, now.minute))
    await state.update_data(sec=now.second)
    await putInDb(call.message, state)
    await call.answer()


@dp.callback_query(F.data.in_(['one_hour']))
async def next_hour(call: CallbackQuery, state: FSMContext):
    now = datetime.datetime.now() + datetime.timedelta(hours=1)
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
    now = datetime.datetime.now() + datetime.timedelta(days=1)
    await state.update_data(year=now.year)
    await state.update_data(month=now.month)
    await state.update_data(day=now.day)
    await state.set_state(States.hm)
    await call.message.answer("Введите время в формате ЧЧ:ММ")
    await call.answer()


@dp.callback_query(F.data.in_(['week']))
async def week(call: CallbackQuery, state: FSMContext):
    now = datetime.datetime.now() + datetime.timedelta(days=7)
    await state.update_data(year=now.year)
    await state.update_data(month=now.month)
    await state.update_data(day=now.day)
    await state.set_state(States.hm)
    await call.message.answer("Введите время в формате ЧЧ:ММ")
    await call.answer()


@dp.callback_query(F.data.in_(['2week']))
async def two_week(call: CallbackQuery, state: FSMContext):
    now = datetime.datetime.now() + datetime.timedelta(days=14)
    await state.update_data(year=now.year)
    await state.update_data(month=now.month)
    await state.update_data(day=now.day)
    await state.set_state(States.hm)
    await call.message.answer("Введите время в формате ЧЧ:ММ")
    await call.answer()


@dp.callback_query(F.data.in_(['one_month']))
async def one_month(call: CallbackQuery, state: FSMContext):
    now = datetime.datetime.today() + relativedelta(months=1)
    await state.update_data(year=now.year)
    await state.update_data(month=now.month)
    await state.update_data(day=now.day)
    await state.set_state(States.hm)
    await call.message.answer("Введите время в формате ЧЧ:ММ")
    await call.answer()


@dp.callback_query(F.data.in_(['half_year']))
async def one_month(call: CallbackQuery, state: FSMContext):
    now = datetime.datetime.today() + relativedelta(months=6)
    await state.update_data(year=now.year)
    await state.update_data(month=now.month)
    await state.update_data(day=now.day)
    await state.set_state(States.hm)
    await call.message.answer("Введите время в формате ЧЧ:ММ")
    await call.answer()


async def short_cut(message: Message, state: FSMContext):
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



@dp.message(F.forward_from)
async def print_mes(message: Message, state: FSMContext):
    st = await state.get_state()
    if message.chat.type=="supergroup":
        if st == States.set_main_admin:
            data = await state.get_data()
            new_main_admin_id = message.forward_from.id
            res_possible = await api.check_possible_main_admin(message.chat.id, new_main_admin_id)
            if res_possible['status'] == 'ERROR':
                mes = await message.answer(res_possible['message'])
                await state.clear()
                await asyncio.sleep(5)
                await bot.delete_message(chat_id=message.chat.id, message_id=mes.message_id)
                await bot.delete_message(chat_id=message.chat.id, message_id=data["set_main_admin"]["message_id"])
                await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
            elif data['status'] == 'ERROR':
                await state.clear()
                await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
            else:
                await api.set_main_admin(message.chat.id, new_main_admin_id,
                                         message.chat.title, message.message_thread_id)
                await state.clear()
    



@dp.message(F.text)
async def echo(message: Message, state: FSMContext) -> None:
    st = await state.get_state()
    if message.chat.type == "private":
        if st == States.text:
            res = api.check_text(message.text, 47)
            if res['status'] == 'OK':
                await state.update_data(text=message.text)
                await short_cut(message, state)
            else:
                a = await message.answer(res['message'])
                await asyncio.sleep(10)
                await bot.delete_message(chat_id=message.chat.id, message_id=a.message_id)
                await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        elif st == States.swap:
            await send_swap_request(message, message.text, message.chat.id, state)
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        elif st == States.hm:
            data = await state.get_data()
            t = await api.check_time(message.text, data["year"], data["month"], data["day"], message.from_user.id)
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
            if res["status"] == "OK":
                await state.clear()
            await message.answer(res["message"])
        elif st == States.renameQueue:
            res = api.check_text(message.text, 47)
            if res['status'] == 'OK':
                data = await state.get_data()
                await api.rename_queue(data["renameQueue"], message.text)
                # Здесь был render queue
                builder = InlineKeyboardBuilder()
                builder.button(text="Создать очередь", callback_data="add")
                builder.button(text="Вывести существующие очереди", callback_data="print")
                builder.button(text="Запросить перемещение в очереди", callback_data="swap")
                builder.adjust(1)
                await message.answer("Название очереди было успешно изменено", reply_markup=builder.as_markup())
            else:
                a = await message.answer(res['message'])
                await asyncio.sleep(10)
                await bot.delete_message(chat_id=message.chat.id, message_id=a.message_id)
                await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)

        
        elif st == States.deleteQueueMember:
            data = await state.get_data()
            result = await api.delete_queue_member(message.text)
            match result:
                case "Incorrect":
                    await message.answer("Введён некорректный номер, попробуйте ещё раз")
                case "Doesn't exist":
                    await message.answer('Введённой позиции в очереди нет')
                case _:
                    # Здесь был render queue
                    builder = InlineKeyboardBuilder()
                    builder.button(text="Создать очередь", callback_data="add")
                    builder.button(text="Вывести существующие очереди", callback_data="print")
                    builder.button(text="Запросить перемещение в очереди", callback_data="swap")
                    builder.adjust(1)
                    await message.answer("Участник был успешно удалён", reply_markup=builder.as_markup())
        else:
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)


async def send_ready(event_id, thread_id, group_id):
    builder = InlineKeyboardBuilder()
    queue_message_id = await api.get_message_id(event_id, group_id)
    print(group_id, queue_message_id, 'AAAAAAAAAAAAAAAAAAAAAA')
    await bot.delete_message(chat_id=group_id, message_id=queue_message_id)
    event_type = await api.get_event_type_by_id(event_id)
    if event_type == EventType.QUEUE:
        builder.button(text="Встать в очередь", callback_data=QueueIDCallback(queueID=event_id))
        builder.button(text="Выйти из очереди", callback_data=RemoveMyself(queueID=event_id))
        builder.button(text="Узнать свою позицию в очереди", callback_data=FindMyself(queueID=event_id))
        builder.adjust(1)
        _, message, _ = await api.print_queue(event_id, False, await get_bot_name())
    else:
        message = await api.print_deadline(event_id)
        await api.delete_deadline(event_id)
    mess = await bot.send_message(text=message, chat_id=group_id, message_thread_id=thread_id,
                                  reply_markup=builder.as_markup(), parse_mode='MarkdownV2')
    await api.update_message_id(event_id, mess.message_id, group_id)


async def send_notification(queue_id, thread_id, group_id, message):
    mess_id = await api.get_message_id(queue_id, group_id)
    await bot.delete_message(chat_id=group_id, message_id=mess_id)
    a = await bot.send_message(chat_id=group_id, text=message, message_thread_id=thread_id)
    await api.update_message_id(queue_id, a.message_id, group_id)


async def render_queue(queue_id: int, private: bool):
    try:
        group_id, queue, message_list = await api.print_queue(queue_id, private, await get_bot_name())
        builder = InlineKeyboardBuilder()
        builder.button(text="Встать в очередь", callback_data=QueueIDCallback(queueID=queue_id))
        builder.button(text="Выйти из очереди", callback_data=RemoveMyself(queueID=queue_id))
        builder.button(text="Узнать свою позицию в очереди", callback_data=FindMyself(queueID=queue_id))
        builder.adjust(1)
        for queue_message_id in message_list:
            await bot.edit_message_text(text=queue, chat_id=group_id, message_id=queue_message_id,
                                        reply_markup=builder.as_markup(), parse_mode='MarkdownV2')
    except Exception as ex:
        print(ex)


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
                # Здесь был render_queue
                pass
            await call.answer()
        else:
            await call.answer(url=await api.get_queue_link(callback_data.queueID, await get_bot_name()))


@dp.callback_query(RemoveMyself.filter(F.queueID != 0))
async def unvoting(call: CallbackQuery, callback_data: RemoveMyself):
    result = await api.delete_queue_member_by_id(callback_data.queueID, call.from_user.id)
    if result == 'Incorrect':
        await call.answer("Вы мертвы")
    # Здесь был render_queue


@dp.callback_query(FindMyself.filter(F.queueID != 0))
async def get_number(call: CallbackQuery, callback_data: FindMyself):
    try:
        member_id = await api.get_queue_member_id(callback_data.queueID, call.from_user.id)
        result = await api.get_queue_position(member_id)
        await call.answer("Ваше место в очереди - {}".format(result))
    except Exception as e:
        await call.answer("Еблан, а в очередь встать не судьба??????")


@dp.message(F.new_chat_member)
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


@dp.message(F.left_chat_participant)
async def bot_delete_from_group(message: types.Message):
    if (await bot.get_me()).id == message.left_chat_participant['id']:
        print("Хуй")
        await api.delete_group(message.chat.id)
    elif not message.left_chat_participant['is_bot']:
        await api.delete_group_member(message.chat.id, message.left_chat_participant['id'])
    else:
        await message.answer("Конкурент уничтожен")


async def main():
    logging.basicConfig(level=logging.INFO)
    logger.info(f"DEBUG = {settings.DEBUG}")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
