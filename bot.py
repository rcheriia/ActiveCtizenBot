import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command

# from work_to_db import *

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)
# Объект бота
bot = Bot(token="7502571533:AAHNldxkyTdsbWK9USgo6txboCgA-QPvzLU")
# Диспетчер
dp = Dispatcher()


# Хэндлер на команду /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    buttons = [
        [types.KeyboardButton(text="Жалоба"),
         types.KeyboardButton(text="Благодарность"),
         types.KeyboardButton(text="Предложение")]
    ]
    markup = types.ReplyKeyboardMarkup(keyboard=buttons)
    text = 'Здравствуйте. Это бот "Активный гражданин" где вы можете оставить жалобу, благодарность или предложение.'
    text1 = 'Что хотите оставить?'
    await message.answer(text)
    await message.answer(text1, reply_markup=markup)


# Нужно дописать. Хэндлер на сообщения(выбор варианта обращения) от пользователя
@dp.message(F.text.lower() in ["жалоба", "благодарность", "предложение"])
async def cmd_start(message: types.Message):
    await message.answer(message.text)


# Запуск процесса поллинга новых апдейтов
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
