from aiogram.dispatcher.router import Router
from aiogram.filters.command import Command
from aiogram import types
from queue_api import api


router = Router()


@router.message(Command('rating'))
async def rating_handler(message: types.Message):
    if message.chat.type == 'supergroup':
        await message.answer(await api.change_rating(message.from_user.id, message.chat.id))
    else:
        await message.answer('Ты дебила кусок, эта игра для групп предназначена!')
