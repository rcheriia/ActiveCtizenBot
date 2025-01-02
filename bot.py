import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F, utils
from aiogram.filters.command import Command
from work_to_db import *

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)
# Объект бота
bot = Bot(token="7502571533:AAHNldxkyTdsbWK9USgo6txboCgA-QPvzLU")
# Диспетчер
dp = Dispatcher()


# Хэндлер на команду /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    buttons = [[types.KeyboardButton(text="Жалоба"),
         types.KeyboardButton(text="Благодарность"),
         types.KeyboardButton(text="Предложение")]]
    markup = types.ReplyKeyboardMarkup(keyboard=buttons)
    text = 'Здравствуйте. Это бот "Активный гражданин" где вы можете оставить жалобу, благодарность или предложение.'
    text1 = 'Что хотите оставить?'
    await message.answer(text)
    await message.answer(text1, reply_markup=markup)


stat = {}


# Хэндлер на сообщения(выбор варианта обращения) от пользователя
@dp.message(F.text == "Жалоба")
@dp.message(F.text == "Благодарность")
@dp.message(F.text == "Предложение")
async def choose_treatment(message: types.Message):
    await message.answer("Напишите ваше ФИО")
    # Присвоение статуса для отделения ФИО от текста обращения
    stat[message.chat.id] = 'name'
    number = add_appeal(message.text, message.chat.id)
    stat[message.chat.id] = ('name', number)

# Хэндлер на любые текстовые сообщения
@dp.message(F.text)
async def getting_text(message: types.Message):
    user_id = message.chat.id
    if stat[user_id][0] == 'name':
        button = [[types.KeyboardButton(text="Отправить геолокацию", request_location=True)]]
        markup = types.ReplyKeyboardMarkup(keyboard=button)

        await message.answer("Напишите свой адрес, для получения на него ответа.", reply_markup=markup)

        add_user(user_id, message.text.capitalize())

# Запуск процесса поллинга новых апдейтов
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
