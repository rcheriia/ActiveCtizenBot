import asyncio
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.filters.command import Command
from work_to_db import *
from config import token, admin
from location import *
from aiogram.types.input_file import FSInputFile
from excel import get_file

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)
# Объект бота
bot = Bot(token=token)
# Диспетчер
dp = Dispatcher()

stat = {}
user_chat = set()


# Хэндлер на команду /start
@dp.message(Command("start"))
async def start(message: types.Message):
    if message.chat.id == admin:
        text = 'Здравствуйте. Это бот "Активный гражданин". Здесь вы можете сделать выгрузку всех обращений и посмотреть карту обращений.'
        but_1 = "Выгрузить все обращения"
        but_2 = "Посмотреть карту обращений"
    else:
        text = 'Здравствуйте. Это бот "Активный гражданин". Здесь вы можете оставить жалобу, благодарность или предложение или запрос на онлайн общение с представителем администрации'
        but_1 = "Запрос на общение с представителем администрации"
        but_2 = "Оставить обращение"

    buttons = [[types.KeyboardButton(text=but_1),
                types.KeyboardButton(text=but_2)]]
    markup = types.ReplyKeyboardMarkup(keyboard=buttons)
    await message.answer(text)
    await message.answer("Что хотите сделать?", reply_markup=markup)


# Хэндлер на запрос общения с администрацией
@dp.message(F.text == "Запрос на общение с представителем администрации")
async def choose_treatment(message: types.Message):
    data = datetime.now()
    day_week = data.date().today().weekday()
    if day_week in [0, 1, 2, 3, 4] and 10 <= data.hour <= 15:
        button = [[types.InlineKeyboardButton(text="Начать чат", callback_data=str(message.chat.id))]]
        markup = types.InlineKeyboardMarkup(inline_keyboard=button)
        await message.answer("Когда представитель будет свободен, мы дадим вам знать",
                             reply_markup=types.ReplyKeyboardRemove())
        await bot.send_message(admin, "Пришёл запрос на общение с администрацией.", reply_markup=markup)

    else:
        button = [[types.KeyboardButton(text="Оставить обращение")]]
        markup = types.ReplyKeyboardMarkup(keyboard=button)
        await message.answer(
            "Время работы онлайн сотрудника: ПН-ПТ с 10:00 до 16:00. Запрос можно оставить в рабочее время, а пока можете отправить обращение.",
            reply_markup=markup)

# Запрос админа на выгрузку всех обращений
@dp.message(F.text == "Выгрузить все обращения")
async def send_appends(message: types.Message):
    if get_file():
        file = FSInputFile('All_appeals.xlsx')
        await bot.send_document(message.chat.id, file)

# Начало чата с представителем
@dp.callback_query(F.data, F.func(lambda msg: msg.data not in ["approval", "not_robot", "email", "address"]))
async def start_chat(callback: types.CallbackQuery):
    button = [[types.KeyboardButton(text="Завершить чат")]]
    markup = types.ReplyKeyboardMarkup(keyboard=button)
    user_id = callback.data
    stat[user_id] = [admin]
    stat[admin] = [user_id]
    user_chat.add(admin)
    user_chat.add(user_id)
    await bot.delete_message(callback.message.chat.id, callback.message.message_id)
    await bot.send_message(user_id, "Представитель начал чат", reply_markup=markup)
    await callback.message.answer("Вы начали чат", reply_markup=markup)


# Завершение чата представителем или пользователем
@dp.message(F.text == "Завершить чат")
async def end_chat(message: types.Message):
    user_id = message.chat.id
    await bot.send_message(stat[user_id][0], "Чат завершён", reply_markup=types.ReplyKeyboardRemove())
    await message.answer("Чат завершён", reply_markup=types.ReplyKeyboardRemove())
    user_chat.discard(user_id)
    user_chat.discard(stat[user_id][0])

    def delet(user):
        if len(stat[user]) == 1:
            del stat[user]
        else:
            del stat[user][0]

    delet(stat[user_id][0])
    delet(user_id)


# Хэндлер для выбора варианта обращения
@dp.message(F.text == "Оставить обращение")
async def choose_treatment(message: types.Message):
    buttons = [[types.KeyboardButton(text="Жалоба"),
                types.KeyboardButton(text="Благодарность"),
                types.KeyboardButton(text="Предложение")]]
    markup = types.ReplyKeyboardMarkup(keyboard=buttons)
    text1 = 'Что хотите оставить?'
    await message.answer(text1, reply_markup=markup)


# Хэндлер на сообщение(выбор варианта обращения) от пользователя
@dp.message(F.text == "Жалоба")
@dp.message(F.text == "Благодарность")
@dp.message(F.text == "Предложение")
async def send_name(message: types.Message):
    await message.answer("Напишите ваше ФИО", reply_markup=types.ReplyKeyboardRemove())
    # Присвоение статуса для отделения ФИО от текста обращения
    number = add_appeal(message.text, message.chat.id)
    stat[message.chat.id] = ['name', number, message.text, '']


# Хэндлер на любые текстовые сообщения
@dp.message(F.text, F.func(lambda msg: msg.text not in al))
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

    elif stat[user_id][0] in user_chat:
        await bot.send_message(stat[user_id][0], message.text)


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
    stat[message.chat.id][3] = message.text

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
@dp.message(F.text, F.func(lambda msg: msg.text in al))
async def selecting_subsection(message: types.Message):
    stat[message.chat.id][0] = "text_appeal"
    add_chapter(stat[message.chat.id][1], f"{stat[message.chat.id][3]} | {message.text}")
    await message.answer("Напишите текст обращения. Если необходимо, прикрепите фото.",
                         reply_markup=types.ReplyKeyboardRemove())


# При отправке фото
@dp.message(F.photo)
async def add_content_app(message: types.Message):
    user_id = message.chat.id
    # При отправке обращения с фото
    if stat[user_id][0] == "text_appeal":
        # Добавляем текст и фото в базу данных
        stat[user_id][0] = "email"
        id_photo = message.photo[-1].file_id
        add_content_appeal(stat[user_id][1], message.caption, id_photo)

        buttons = [[types.InlineKeyboardButton(text="По электронной почте", callback_data="email"),
                    types.InlineKeyboardButton(text="По адресу заявителя", callback_data="address")]]
        markup = types.InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer("Как вы хотите получить ответ?", reply_markup=markup)

    # Подразумевается чат с представителем
    elif stat[user_id][0] in user_chat:
        media, text = message.photo[-1].file_id, message.caption
        await bot.send_photo(stat[user_id][0], media, caption=text)


# При отправке видео
@dp.message(F.video)
async def add_content_app(message: types.Message):
    # Подразумевается чат с представителем
    if stat[message.chat.id][0] in user_chat:
        media, text = message.video.file_id, message.caption
        await bot.send_document(stat[message.chat.id][0], media, caption=text)


# При отправке документа
@dp.message(F.document)
async def send_document(message: types.Message):
    # Подразумевается чат с представителем
    if stat[message.chat.id][0] in user_chat:
        media, text = message.document.file_id, message.caption
        await bot.send_document(stat[message.chat.id][0], media, caption=text)


# Добавление email для получения на него ответа
@dp.callback_query(F.data == "email")
async def getting_main_menu(callback: types.CallbackQuery):
    await bot.delete_message(callback.message.chat.id, callback.message.message_id)
    await callback.message.answer("Напишите вашу электронную почту")


# Получение ответа на дом
@dp.callback_query(F.data == "address")
async def getting_main_menu(callback: types.CallbackQuery):
    user_id = callback.message.chat.id
    dop = reply[stat[user_id][2]]
    text = f"Номер вашего обращения {stat[user_id][1]}.\n{dop}"
    del stat[user_id]
    await bot.delete_message(callback.message.chat.id, callback.message.message_id)
    await callback.message.answer(text)


# Запуск процесса поллинга новых апдейтов
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
