import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.filters.command import Command
from work_to_db import *
from config import token
from location import get_addr

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)
# Объект бота
bot = Bot(token=token)
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
    await message.answer("Напишите ваше ФИО", reply_markup=types.ReplyKeyboardRemove())
    # Присвоение статуса для отделения ФИО от текста обращения
    stat[message.chat.id] = 'name'
    number = add_appeal(message.text, message.chat.id)
    stat[message.chat.id] = ['name', number]


# Хэндлер на любые текстовые сообщения
@dp.message(F.text)
async def getting_text(message: types.Message):
    user_id = message.chat.id
    if stat[user_id][0] == 'name':
        name = list(map(lambda x: x.capitalize(), message.text.split()))
        add_user(user_id, ' '.join(name))
        stat[message.chat.id][0] = 'phone_number'

        await message.answer("Напишите ваш номер телефона")

    elif stat[user_id][0] == "phone_number":
        stat[user_id][0] = "loc"
        add_phone_number(user_id, message.text)
        button = [[types.KeyboardButton(text="Отправить геолокацию", request_location=True)]]
        markup = types.ReplyKeyboardMarkup(keyboard=button)

        await message.answer("Напишите ваш адрес", reply_markup=markup)

    elif stat[user_id][0] == "loc":
        add_address(user_id, message.text)
        button = [[types.InlineKeyboardButton(text="Даю согласие", callback_data="approval")]]
        markup = types.InlineKeyboardMarkup(inline_keyboard=button)
        await message.answer(
            "Для того, чтобы мы могли с Вами связаться, по правилам РФ, нам нужно спросить Ваше согласие на обработку персональных данных и с правилами сайта",
            reply_markup=markup)


# Хэндлер на местоположение пользователя
@dp.message(F.location)
async def location_handler(message: types.Message):
    await message.answer("-", reply_markup=types.ReplyKeyboardRemove())
    await bot.delete_message(message.chat.id, message.message_id + 1)
    # Получение координат, обратное геокодирование и добавление в базу данных
    lat = message.location.latitude
    long = message.location.longitude
    user_id = message.chat.id
    add_address(user_id, get_addr([lat, long]))

    # Получение у пользователя согласия на обработку персональных данных
    button = [[types.InlineKeyboardButton(text="Даю согласие", callback_data="approval")]]
    markup = types.InlineKeyboardMarkup(inline_keyboard=button)
    await message.answer(
        "Для того, чтобы мы могли с Вами связаться, по правилам РФ, нам нужно спросить Ваше согласие на обработку персональных данных и с правилами сайте",
        reply_markup=markup)

# Получение согласия на обработку данных и капча
@dp.callback_query(F.data == "approval")
async def check_robot(callback: types.CallbackQuery):
    button = [[types.InlineKeyboardButton(text="Я робот", callback_data="robot"),
               types.InlineKeyboardButton(text="Я не робот", callback_data="not_robot")]]
    markup = types.InlineKeyboardMarkup(inline_keyboard=button)
    await callback.message.answer("Подтвердите, что вы не робот", reply_markup=markup)

# После прохождения капчи выбор раздела обращения
@dp.callback_query(F.data == "not_robot")
async def check_robot(callback: types.CallbackQuery):
    # stat[callback.message.chat.id][0] = "choose_chapter"
    menu = ["ЖКХ", "Транспорт", "Спорт", "Правопорядок", "Культура",
            "Здравоохранение", "Бытовое обслуживание", "Образование"]

    markup = ReplyKeyboardBuilder()
    for i in menu:
        markup.add(types.KeyboardButton(text=i))
    markup.adjust(2)
    await callback.message.answer("Выберете раздел для обращения:",
                                  reply_markup=markup.as_markup(resize_keyboard=True))


# Запуск процесса поллинга новых апдейтов
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
