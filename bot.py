import asyncio
import logging
import datetime
from queue_api import api
import aiogram
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram import F
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
    timezone = State()
    hm = State()



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


class QueueSelectCallback(CallbackData, prefix="queueSelect"):
    queueID: int
    delete_message_id: int
    queueName: str


class DeleteQueueCallback(CallbackData, prefix="DeleteQueue"):
    queueID: int
    messageID : int


class DeleteQueueMemberCallback(CallbackData, prefix="DeleteQueueMember"):
    queueID: int


class RenameQueueCallback(CallbackData, prefix="RenameQueue"):
    queueID: int


@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext) -> None:
    builder = InlineKeyboardBuilder()
    builder.button(text="Создать очередь", callback_data="add")
    builder.button(text="Вывести существующие очереди", callback_data="print")
    builder.adjust(1)
    if message.chat.type == "group" or message.chat.type == "supergroup":
        chat_admins = await bot.get_chat_administrators(message.chat.id)
        d = []
        for admin in chat_admins:
            userId = admin.user.id
            d.append(userId)
        await api.add_admin(message.chat.id, d, message.chat.title, message.message_thread_id)
        await message.answer(
            "Здравствуйте уважаемые пользователи, для того, чтобы создать очередь админ группы должен написать в личное сообщение боту")
    elif message.chat.type == "private":
        await message.answer("Здравствуйте, вам доступен следующий функционал\n", reply_markup=builder.as_markup())


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
    r = await call.message.answer(st)
    if lenq > 0:
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
        group_id, queue_message_id, queue = await api.print_queue(callback_data.queueID)
        builder = InlineKeyboardBuilder()
        builder.button(text="Встать в очередь", callback_data=QueueIDCallback(queueID=callback_data.queueID))
        builder.button(text="Выйти из очереди", callback_data=RemoveMyself(queueID=callback_data.queueID))
        builder.adjust(1)
        await bot.edit_message_text(text=queue, chat_id=group_id, message_id=queue_message_id,
                                    reply_markup=builder.as_markup(), parse_mode='MarkdownV2')
        await call.answer()



@dp.callback_query(DeleteQueueMemberCallback.filter(F.queueID != 0))
async def delete_queue_member(call: CallbackQuery, callback_data: DeleteQueueMemberCallback, state: FSMContext):
    _, _, message = await api.print_queue(callback_data.queueID)
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
        await bot.delete_message(chat_id=group_id, message_id=message_id)
        await bot.delete_message(chat_id=call.message.chat.id, message_id=callback_data.messageID)
    builder = InlineKeyboardBuilder()
    builder.button(text="Создать очередь", callback_data="add")
    builder.button(text="Вывести существующие очереди", callback_data="print")
    builder.adjust(1)
    await call.message.answer("Очередь удалена", reply_markup=builder.as_markup())
    await call.answer()


@dp.callback_query(DayCallback.filter(F.day != 0))
async def Day(call: CallbackQuery, callback_data: DayCallback, state: FSMContext):
    if call.message.chat.type == "private":
        await state.update_data(day=callback_data.day)
        await state.set_state(States.timezone)
        await call.message.answer("Введите разницу времени с Москвой")
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
        print(data)
    except Exception:
        print("Error")
    thread_id, date = await api.add_queue(data)
    builder = InlineKeyboardBuilder()
    builder.button(text="Создать очередь", callback_data="add")
    builder.button(text="Вывести существующие очереди", callback_data="print")
    builder.adjust(1)
    await message.answer("Очередь была создана", reply_markup=builder.as_markup())
    await bot.send_message(chat_id=data['group_id'], message_thread_id=thread_id,
                           text="Очередь {} будет создана {}. За час до этого будет отправлено напоминание".format(
                               data['text'], date))


@dp.message(F.text)
async def echo(message: Message, state: FSMContext) -> None:
    st = await state.get_state()
    if message.chat.type == "private":
        if st == States.text:
            builder = InlineKeyboardBuilder()
            builder.button(text="{}".format(datetime.datetime.now().year),
                           callback_data=YearCallback(year=datetime.datetime.now().year))
            builder.button(text="{}".format(datetime.datetime.now().year + 1),
                           callback_data=YearCallback(year=datetime.datetime.now().year + 1))
            builder.button(text="{}".format(datetime.datetime.now().year + 2),
                           callback_data=YearCallback(year=datetime.datetime.now().year + 2))
            builder.adjust(1)
            await message.answer("Текст сообщения получен, выберите год", reply_markup=builder.as_markup())
            await state.update_data(text=message.text)
            await state.set_state(States.year)
        if st == States.timezone:
            if api.check_timezone(message.text):
                await message.answer("Часовой пояс сохранён, теперь введите время для напоминания в формате ЧЧ:ММ")
                await state.update_data(timezone=message.text)
                await state.set_state(States.hm)
            else:
                await message.answer("Неправильно, попробуйте ещё раз")
        if st == States.hm:
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
        if st == States.renameQueue:
            data = await state.get_data()
            await api.rename_queue(data["renameQueue"], message.text)
            group_id, queue_message_id, queue = await api.print_queue(data["renameQueue"])
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
            builder.adjust(1)
            await message.answer("Название очереди было успешно изменено", reply_markup=builder.as_markup())

        if st == States.deleteQueueMember:
            data = await state.get_data()
            result = await api.delete_queue_member(message.text)
            match result:
                case "Incorrect":
                    await message.answer("Введён некорректный номер, попробуйте ещё раз")
                case "Doesn't exist":
                    await message.answer('Введённой позиции в очереди нет')
                case _:

                    group_id, queue_message_id, queue = await api.print_queue(data["deleteQueueMember"])
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
                    builder.adjust(1)
                    await message.answer("Участник был успешно удалён", reply_markup=builder.as_markup())


@dp.callback_query(StopVoteCallback.filter(F.ID != 0))
async def stopvoting(call: CallbackQuery, callback_data: StopVoteCallback):
    st = await api.print_queue(callback_data.queueID)
    await bot.send_message(chat_id=callback_data.ID, text=st, message_thread_id=callback_data.thread_id,
                           parse_mode='MarkdownV2')
    await bot.delete_message(chat_id=callback_data.ID, message_id=callback_data.message_id)
    await call.answer()


async def queue_send(queue_id, thread_id, group_id, message):
    builder = InlineKeyboardBuilder()
    queue_message_id = await api.get_message_id(queue_id)
    builder.button(text="Встать в очередь", callback_data=QueueIDCallback(queueID=queue_id))
    builder.button(text="Выйти из очереди", callback_data=RemoveMyself(queueID=queue_id))
    builder.adjust(1)
    await bot.edit_message_text(text=message, chat_id=group_id, message_id=queue_message_id,
                                reply_markup=builder.as_markup(), parse_mode='MarkdownV2')


async def queue_notif_send(queue_id, thread_id, group_id, message):
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
    is_queue_member = await api.add_user_to_queue(callback_data.queueID, call.from_user.id, call.from_user.full_name)
    if is_queue_member:
        await call.answer("Вы уже добавлены в очередь")
    else:
        group_id, queue_message_id, queue = await api.print_queue(callback_data.queueID)
        builder = InlineKeyboardBuilder()
        builder.button(text="Встать в очередь", callback_data=QueueIDCallback(queueID=callback_data.queueID))
        builder.button(text="Выйти из очереди", callback_data=RemoveMyself(queueID=callback_data.queueID))
        builder.adjust(1)
        await bot.edit_message_text(text=queue, chat_id=group_id, message_id=queue_message_id,
                                    reply_markup=builder.as_markup(), parse_mode='MarkdownV2')
        await call.answer()


@dp.callback_query(RemoveMyself.filter(F.queueID != 0))
async def unvoting(call: CallbackQuery, callback_data: RemoveMyself):
    result = await api.delete_queue_member_by_id(callback_data.queueID, call.from_user.id)
    if result == 'Incorrect':
        await call.answer("Вы мертвы")
    else:
        group_id, queue_message_id, queue = await api.print_queue(callback_data.queueID)
        builder = InlineKeyboardBuilder()
        builder.button(text="Встать в очередь", callback_data=QueueIDCallback(queueID=callback_data.queueID))
        builder.button(text="Выйти из очереди", callback_data=RemoveMyself(queueID=callback_data.queueID))
        builder.adjust(1)
        await bot.edit_message_text(text=queue, chat_id=group_id, message_id=queue_message_id,
                                    reply_markup=builder.as_markup(), parse_mode='MarkdownV2')
        await call.answer()
    # передаётся callback_data.queueID, call.from_user.id Это id очереди и id нажавшего

async def main():
    logging.basicConfig(level=logging.INFO)
    # asyncio.create_task(scheduler())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
