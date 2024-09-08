import asyncio

from aiogram import F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.utils import short_cut, send_swap_request, putInDb, deadline_list_return, queue_return
from queue_api import api
from aiogram.dispatcher.router import Router
from .states import *


router = Router()

@router.message(F.text)
async def echo(message: Message, state: FSMContext, bot: Bot) -> None:
    st = await state.get_state()
    if message.chat.type == "private":
        if st == Event.text:
            res = api.check_text(message.text, 47)
            if res['status'] == 'OK':
                await state.update_data(text=message.text)
                await short_cut(message, state)
            else:
                a = await message.answer(res['message'])
                await asyncio.sleep(10)
                await bot.delete_message(chat_id=message.chat.id, message_id=a.message_id)
                await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        elif st == Event.swap:
            await send_swap_request(message, message.text, message.chat.id, state)
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        elif st == Event.hm:
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
        elif st == Event.tz:
            res = await api.change_tz(message.chat.id, message.text)
            # if res["status"] == "OK":
            #     await state.clear()
            await message.answer("Часовой пояс введён неверно, введите ещё раз")
        elif st == Deadline.renameDeadline:
            res = api.check_text(message.text, 47)
            if res['status'] == 'OK':
                data = await state.get_data()
                res = await api.update_deadline_text(data['renameDeadline']["dead_id"], message.text)
                if res['status'] == 'ERROR':
                    q = await message.answer(res['message'])
                    try:
                        await bot.edit_message_text(text='Повторите ввод названия', chat_id=message.chat.id,
                                                    message_id=data['renameDeadline']["message_id"])
                    except Exception:
                        pass
                else:
                    await state.clear()
                    q = await message.answer("Название было изменено")
                    message_id, text, chat_id = res['data']
                    await deadline_list_return(message.chat.id, data['renameDeadline']["edit_message_id"])
                    await bot.delete_message(chat_id=message.chat.id, message_id=data['renameDeadline']["message_id"])
                    await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text)
                await asyncio.sleep(5)
                await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
                await bot.delete_message(chat_id=message.chat.id, message_id=q.message_id)
            else:
                a = await message.answer(res['message'])
                await asyncio.sleep(5)
                await bot.delete_message(chat_id=message.chat.id, message_id=a.message_id)
                await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        elif st == Queue.renameQueue:
            res = api.check_text(message.text, 47)
            if res['status'] == 'OK':
                data = await state.get_data()
                await state.clear()
                await api.rename_queue(data["renameQueue"]["queueID"], message.text)
                await queue_return(message.chat.id, data["renameQueue"]["messageID"])
                await bot.delete_message(chat_id=message.chat.id, message_id=data["renameQueue"]["del_message"])
                # Здесь был render queue
                #                builder = InlineKeyboardBuilder()
                #                builder.button(text="Создать очередь", callback_data="add")
                #                builder.button(text="Вывести существующие очереди", callback_data="print")
                #                builder.button(text="Запросить перемещение в очереди", callback_data="swap")
                #                builder.adjust(1)
                a = await message.answer("Название очереди было успешно изменено")
                await asyncio.sleep(5)
                await bot.delete_message(chat_id=message.chat.id, message_id=a.message_id)
                await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
                await state.clear()
            else:
                a = await message.answer(res['message'])
                await asyncio.sleep(5)
                await bot.delete_message(chat_id=message.chat.id, message_id=a.message_id)
                await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)


        elif st == Queue.deleteQueueMember:
            data = await state.get_data()
            result = await api.delete_queue_member(message.text)
            match result:
                case "Incorrect":
                    q = await message.answer("Введён некорректный номер, попробуйте ещё раз")
                    await asyncio.sleep(5)
                    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
                    await bot.delete_message(chat_id=message.chat.id, message_id=q.message_id)
                case "Doesn't exist":
                    q = await message.answer('Введённой позиции в очереди нет')
                    await asyncio.sleep(5)
                    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
                    await bot.delete_message(chat_id=message.chat.id, message_id=q.message_id)
                case _:
                    await state.clear()
                    # Здесь был render queue
                    await bot.delete_message(chat_id=message.chat.id,
                                             message_id=data["deleteQueueMember"]["queue_message"])
                    await bot.delete_message(chat_id=message.chat.id,
                                             message_id=data["deleteQueueMember"]["please_message"])
                    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
                    await queue_return(message.chat.id, data["deleteQueueMember"]["messageID"])
                    q = await message.answer("Участник был успешно удалён")
                    await asyncio.sleep(5)
                    await bot.delete_message(chat_id=message.chat.id, message_id=q.message_id)
        else:
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
