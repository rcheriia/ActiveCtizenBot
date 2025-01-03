import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.filters.command import Command
from work_to_db import *
from config import token
from location import get_addr, sl, menu, all, reply

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
    stat[message.chat.id] = ['name', number, message.text]


# Хэндлер на любые текстовые сообщения
@dp.message(F.text, F.func(lambda msg: msg.text not in all))
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

    elif stat[user_id][0] == "text_appeal":
        stat[user_id][0] = "email"
        add_content_appeal(stat[user_id][1], message.text)

        add_address(user_id, message.text)
        buttons = [[types.InlineKeyboardButton(text="По электронной почте", callback_data="email"),
                    types.InlineKeyboardButton(text="По адресу заявителя", callback_data="address")]]
        markup = types.InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer("Как вы хотите получить ответ?", reply_markup=markup)

    elif stat[user_id][0] == "email":
        add_email(user_id, message.text)
        dop = reply[stat[user_id][2]]
        text = f"Номер вашего обращения {stat[user_id][1]}.\n{dop}"
        del stat[user_id]
        await message.answer(text)


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
    await bot.delete_message(callback.message.chat.id, callback.message.message_id)
    await callback.message.answer("Подтвердите, что вы не робот", reply_markup=markup)


# После прохождения капчи выбор раздела обращения
@dp.callback_query(F.data == "not_robot")
async def getting_main_menu(callback: types.CallbackQuery):
    markup = ReplyKeyboardBuilder()
    for i in menu:
        markup.add(types.KeyboardButton(text=i))
    markup.adjust(2)
    await callback.message.answer("Выберете раздел для обращения:",
                                  reply_markup=markup.as_markup(resize_keyboard=True))
    await bot.delete_message(callback.message.chat.id, callback.message.message_id)


# Выбор подраздела обращения
@dp.message(F.text, F.func(lambda msg: msg.text in menu))
async def selecting_subsection(message: types.Message):
    markup = ReplyKeyboardBuilder()
    for i in [*sl[message.text], "Другое", "Назад"]:
        markup.add(types.KeyboardButton(text=i))
    markup.adjust(2)
    await message.answer("Выберете раздел для обращения:",
                         reply_markup=markup.as_markup(resize_keyboard=True))
    await bot.delete_message(message.chat.id, message.message_id - 1)
    await bot.delete_message(message.chat.id, message.message_id)


# Вернуться к выбору основного раздела обращения
@dp.message(F.text == "Назад")
async def return_main_menu(message: types.Message):
    markup = ReplyKeyboardBuilder()
    for i in menu:
        markup.add(types.KeyboardButton(text=i))
    markup.adjust(2)
    await message.answer("Выберете раздел для обращения:",
                         reply_markup=markup.as_markup(resize_keyboard=True))
    await bot.delete_message(message.chat.id, message.message_id - 1)
    await bot.delete_message(message.chat.id, message.message_id)


# Выбор раздела обращения
@dp.message(F.text, F.func(lambda msg: msg.text in all))
async def selecting_subsection(message: types.Message):
    stat[message.chat.id][0] = "text_appeal"
    add_chapter(stat[message.chat.id][1], message.text)
    await message.answer("Напишите текст обращения. Если необходимо, прикрепите фото.",
                         reply_markup=types.ReplyKeyboardRemove())


# При отправке обращения с фото
@dp.message(content_types=['photo'])
async def check_robot(message: types.Message):
    # Добавляем текст и фото в базу данных
    user_id = message.chat.id
    stat[user_id][0] = "email"
    id_photo = message.photo[-1].file_id
    add_content_appeal(stat[user_id][1], message.caption, id_photo)

    buttons = [[types.InlineKeyboardButton(text="По электронной почте", callback_data="email"),
                types.InlineKeyboardButton(text="По адресу заявителя", callback_data="address")]]
    markup = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("Как вы хотите получить ответ?", reply_markup=markup)


# Получение ответа на дом
@dp.callback_query(F.data == "address")
async def getting_main_menu(callback: types.CallbackQuery):
    user_id = callback.message.chat.id
    dop = reply[stat[user_id][2]]
    text = f"Номер вашего обращения {stat[user_id][1]}.\n{dop}"
    del stat[user_id]
    await callback.message.answer(text)


# Запуск процесса поллинга новых апдейтов
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
