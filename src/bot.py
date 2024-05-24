import asyncio
from datetime import date
from multiprocessing import Process,Manager, Value
import logging
import datetime
import logic
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.filters import Filter
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types.inline_keyboard_markup import InlineKeyboardMarkup
from aiogram.filters.callback_data import CallbackData



logging.basicConfig(level=logging.INFO)
API_TOKEN = "6733084480:AAECacPclPo0emdVottudh9o9yoSqJP7BGs"
bot = Bot(token=API_TOKEN)


dp = Dispatcher()

users = []



a = []


admins = {}

test = [datetime.datetime.strptime("23/05/2024 22:18", "%d/%m/%Y %H:%M"),
        datetime.datetime.strptime("20/05/2024 19:07", "%d/%m/%Y %H:%M"),
        datetime.datetime.strptime("20/05/2024 19:12", "%d/%m/%Y %H:%M")]

voted = {}





months = {
        1:["Январь", 31],
        2:["Февраль",28],
        3:["Март",31],
        4:["Апрель",30],
        5:["Май",31],
        6:["Июнь",30],
        7:["Июль",31],
        8:["Август", 31],
        9:["Сентябрь",30],
        10:["Октябрь", 31],
        11:["Ноябрь",30],
        12:["Декабрь", 31]
}







class States(StatesGroup):
    group_id = State()
    RemoveMessageyear = State()
    RemoveMessagemonth = State()
    RemoveMessageday = State()
    text = State()
    year = State()
    month = State()
    day = State()
    timezone = State()
    hm = State()


class YearCallback(CallbackData, prefix="year"):
    year: int


class MonthCallback(CallbackData, prefix="month"):
    month: int


class DayCallback(CallbackData, prefix="day"):
    day: int

class StopVoteCallback(CallbackData, prefix="stop"):
    ID: int
    message_id: int
    queueID : int


class GroupSelectCallback(CallbackData, prefix="selectGroup"):
    groupID : int


class QueueIDCallback(CallbackData, prefix="queueID"):
    queueID : int


@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext) -> None:
    global admins
    builder = InlineKeyboardBuilder()
    builder.button(text="Создать очередь", callback_data="add")
    builder.button(text="Вывести существующие очереди", callback_data="print")
    builder.button(text="Удалить очередь", callback_data="delete")
    builder.adjust(1)
    if message.chat.type=="group" or message.chat.type=="supergroup":
        chat_admins = await bot.get_chat_administrators(message.chat.id)
        admins[int(message.chat.id)] = ([], message.chat.title)
        d = []
        for admin in chat_admins:
            userId = admin.user.id
            admins[int(message.chat.id)][0].append(userId)
            d.append(userId)
        logic.add_admin(message.chat.id, d, message.chat.title)
        await message.answer(str(message.message_thread_id))
        await message.answer("Здарова пидарасы, для того, чтобы созжать очередь админ группы должен написать в личное сообщение боту")
    elif message.chat.type=="private":
        await message.answer("Здарова пидарас\n", reply_markup=builder.as_markup())
    users.append(message.chat.id)




@dp.callback_query(GroupSelectCallback.filter(F.groupID!=0))
async def groupSelected(call : CallbackQuery, callback_data : GroupSelectCallback, state: FSMContext):
    await state.update_data(group_id=callback_data.groupID)
    await call.message.answer("Напишите сообщение для добавления")
    await state.set_state(States.text)
    await call.answer()








@dp.callback_query(F.data.in_(['add']))
async def addNotification(call: CallbackQuery, state: FSMContext):
    if call.message.chat.type=="private":
        group = logic.check_admin(call.message.chat.id)
        if len(group)==0:
            builder = InlineKeyboardBuilder()
            builder.button(text="Создать очередь", callback_data="add")
            builder.button(text="Вывести существующие очереди", callback_data="print")
            builder.button(text="Удалить очередь", callback_data="delete")
            builder.adjust(1)
            await call.message.answer("У тебя нет групп, где ты админ", reply_markup=builder.as_markup())
        else:
            builder = InlineKeyboardBuilder()
            for gloss in group:
                builder.button(text=gloss["group_name"], callback_data=GroupSelectCallback(groupID=gloss["group_tg_id"]))
            builder.adjust(1)
            await call.message.answer("У тебя есть доступ к этим группам", reply_markup=builder.as_markup())
    await call.answer()



@dp.callback_query(DayCallback.filter(F.day!=0))
async def Day(call : CallbackQuery, callback_data : DayCallback, state: FSMContext):
    if (call.message.chat.type=="group" and call.from_user.id in admins[call.message.chat.id]) or call.message.chat.type=="private":
        await state.update_data(day=callback_data.day)
        await state.set_state(States.timezone)
        await call.message.answer("Введите разницу времени с Москвой")




@dp.callback_query(MonthCallback.filter(F.month!=0))
async def Month(call : CallbackQuery, callback_data : MonthCallback, state: FSMContext):
    if (call.message.chat.type=="group" and call.from_user.id in admins[call.message.chat.id]) or call.message.chat.type=="private":
        await state.update_data(month=callback_data.month)
        await state.set_state(States.day)
        builder = InlineKeyboardBuilder()
        a = 1
        remove = await state.get_data()
        if datetime.datetime.now().month==callback_data.month:
            a = datetime.datetime.now().day
        year = remove["year"]
        b = months[callback_data.month][1]
        if year%4==0 and (year%1000==0 or year%100!=0) and callback_data.month==2:
            b+=1
        for i in range(a,b+1):
            builder.button(text="{}".format(i), callback_data=DayCallback(day=int(i)))
        builder.adjust(6)
        r = 0
        remove = remove["RemoveMessagemonth"] if "RemoveMessagemonth" in remove else None
        r = 0
        ok = True
        if remove is not None and len(remove.reply_markup.inline_keyboard)==len(builder.as_markup().inline_keyboard) and len(builder.as_markup().inline_keyboard[0])==len(remove.reply_markup.inline_keyboard[0]):
            ok = False
            for i in range(len(remove.reply_markup.inline_keyboard)):
                for j in range(len(remove.reply_markup.inline_keyboard[i])):
                    if remove.reply_markup.inline_keyboard[i][j].text!=builder.as_markup().inline_keyboard[i][j].text:
                        ok = True
                        break
        if ok:
            if remove is not None and remove.reply_markup!=builder.as_markup():
                w = await bot.edit_message_reply_markup(chat_id=call.message.chat.id,message_id=remove.message_id, reply_markup= builder.as_markup())
                await state.update_data(RemoveMessagemonth=w)
            else:
                r = await call.message.answer("Выберите день", reply_markup=builder.as_markup())
                await state.update_data(RemoveMessagemonth=r)
    await call.answer()



@dp.callback_query(YearCallback.filter(F.year!=0))
async def Year(call : CallbackQuery, callback_data : YearCallback, state: FSMContext):
    if (call.message.chat.type=="group" and call.from_user.id in admins[call.message.chat.id]) or call.message.chat.type=="private":
        await state.update_data(year=callback_data.year)
        await state.set_state(States.month)
        builder = InlineKeyboardBuilder()
        a = 1
        if datetime.datetime.now().year==callback_data.year:
            a = datetime.datetime.now().month
        for i in range(a, 13):
            builder.button(text="{}".format(months[i][0]), callback_data=MonthCallback(month=int(i)))
        builder.adjust(3)
        remove = await state.get_data()
        remove = remove["RemoveMessageyear"] if "RemoveMessageyear" in remove else None
        r = 0
        ok = True
        if remove is not None and len(remove.reply_markup.inline_keyboard)==len(builder.as_markup().inline_keyboard) and len(builder.as_markup().inline_keyboard[0])==len(remove.reply_markup.inline_keyboard[0]):
            ok = False
            for i in range(len(remove.reply_markup.inline_keyboard)):
                for j in range(len(remove.reply_markup.inline_keyboard[i])):
                    if remove.reply_markup.inline_keyboard[i][j].text!=builder.as_markup().inline_keyboard[i][j].text:
                        ok = True
                        break
        if ok:
            if remove is not None:
                w = await bot.edit_message_reply_markup(chat_id=call.message.chat.id,message_id=remove.message_id, reply_markup= builder.as_markup())
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
        data["creator_id"] = message.chat.id
        print(data)
    except:
        print("Error")
    logic.add_queue(data)
    builder = InlineKeyboardBuilder()
    builder.button(text="Создать очередь", callback_data="add")
    builder.button(text="Вывести существующие очереди", callback_data="print")
    builder.button(text="Удалить очередь", callback_data="delete")
    builder.adjust(1)
    await message.answer("Очередь была создана", reply_markup=builder.as_markup())




@dp.message(F.text)
async def echo(message: Message, state: FSMContext) -> None:
    st = await state.get_state()
    if (message.chat.type=="group" and message.from_user.id in admins[message.chat.id]) or message.chat.type=="private":
        if st==States.text:
            builder = InlineKeyboardBuilder()
            builder.button(text="{}".format(datetime.datetime.now().year), callback_data=YearCallback(year=datetime.datetime.now().year))
            builder.button(text="{}".format(datetime.datetime.now().year+1), callback_data=YearCallback(year=datetime.datetime.now().year+1))
            builder.button(text="{}".format(datetime.datetime.now().year+2), callback_data=YearCallback(year=datetime.datetime.now().year+2))
            builder.adjust(1)
            await message.answer("Текст сообщения получен, выберите год", reply_markup = builder.as_markup())
            await state.update_data(text=message.text)
            await state.set_state(States.year)
        if st==States.timezone:
            if logic.check_timezone(message.text):
                await message.answer("Часовой пояс сохранён, теперь введите время для напоминания в формате ЧЧ:ММ")
                await state.update_data(timezone=message.text)
                await state.set_state(States.hm)
            else:
                await message.answer("Неправильно, попробуй ещё раз")
        if st==States.hm:
            if logic.check_time(message.text):
                await state.update_data(hm=message.text)
                await putInDb(message, state)
            else:
                await message.answer("Неправильно, попробуй ещё раз")
    else:
        await message.answer("Составлять напоминания в группе могут только администраторы")


@dp.callback_query(StopVoteCallback.filter(F.ID!=0))
async def stopvoting(call : CallbackQuery, callback_data : StopVoteCallback):
    votes = list(voted[callback_data.ID].items())
    s = ""
    for i in votes:
        s+= str(i[1][1])+ "  " + str(i[1][0])+ "\n"
    await bot.send_message(chat_id=callback_data.ID, text="Голосование завершено \n {}".format(s[:-1]))
    await bot.delete_message(chat_id=callback_data.ID, message_id=callback_data.message_id)
    await call.answer()


@dp.message() 
async def choose_your_dinner(): 
    for i in users:
        voted[i] = {}
        builder = InlineKeyboardBuilder()
        queue_id = 123454321
        builder.button(text="Голосуй, Анасуй", callback_data=QueueIDCallback(queueID=queue_id))
        builder1 = InlineKeyboardBuilder()
        a = await bot.send_message(chat_id=i, text='Привет!!!', reply_markup=builder.as_markup())
        builder1.button(text="Stop IT", callback_data=StopVoteCallback(ID=i, message_id=a.message_id, queueID=queue_id))
        await bot.send_message(chat_id=399319082, text="Вы вправе нажать", reply_markup=builder1.as_markup())

 
async def scheduler():
    while True:
        for i in test:
            print(i, (i-datetime.datetime.now()).seconds)
            if (i-datetime.datetime.now()).seconds<60:
                await choose_your_dinner()
        await asyncio.sleep(60) 
         
@dp.callback_query(QueueIDCallback.filter(F.queueID!=0))
async def voting(call: CallbackQuery,callback_data : QueueIDCallback):
    if call.from_user.id not in voted[call.message.chat.id]:
        lenv = len(voted[call.message.chat.id])
        voted[call.message.chat.id][call.from_user.id] = [lenv+1, call.from_user.full_name]
        await bot.send_message(chat_id=call.from_user.id, text="{} с id {} отметился в {} \n Место в очереди {} \n ID очереди {}".format(call.from_user.full_name, call.from_user.id, datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"), lenv+1, callback_data.queueID))
    else:
        await bot.send_message(chat_id=call.from_user.id, text="{} с id {} отметился в {} \n Место в очереди {} \n ID очереди {}".format(call.from_user.full_name, call.from_user.id, datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"), voted[call.message.chat.id][call.from_user.id][0], callback_data.queueID))
    await call.answer()


 
 
async def main():
    logging.basicConfig(level=logging.INFO) 
    asyncio.create_task(scheduler())
    await dp.start_polling(bot) 





if __name__ == "__main__":
    asyncio.run(main())
