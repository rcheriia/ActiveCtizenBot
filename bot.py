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
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext


class AppForm(StatesGroup):
    count = State()


class StatForm(StatesGroup):
    count = State()


# Включаем логирование, чтобы не пропустить важные сообщения
storage = MemoryStorage()
logging.basicConfig(level=logging.INFO)
bot = Bot(token=token)
dp = Dispatcher(storage=storage)

stat = {}
user_chat = set()


def get_menu(id):
    if id == admin:
        buttons = [[types.KeyboardButton(text="Выгрузить все обращения"),
                    types.KeyboardButton(text="Посмотреть карту обращений"),
                    types.KeyboardButton(text="Изменить статус обращения")]]
    else:
        buttons = [[types.KeyboardButton(text="Запрос на общение с представителем администрации"),
                    types.KeyboardButton(text="Оставить обращение"),
                    types.KeyboardButton(text="Посмотреть карту обращений")]]

    markup = types.ReplyKeyboardMarkup(keyboard=buttons)
    return markup

def get_status(status):
    markup = ReplyKeyboardBuilder()
    for i in status:
        markup.add(types.KeyboardButton(text=i))
    markup.adjust(2)
    return markup

# Хэндлер на команду /start
@dp.message(Command("start"))
async def start(message: types.Message):
    if message.chat.id == admin:
        text = 'Здравствуйте. Это бот "Активный гражданин". Здесь вы можете оставить жалобу, благодарность, предложение или запрос на онлайн общение с представителем администрации'
    else:
        text = 'Здравствуйте. Это бот "Активный гражданин". Здесь вы можете сделать выгрузку всех обращений и посмотреть карту обращений.'
    markup = get_menu(message.chat.id)
    await message.answer(text)
    await message.answer("Что хотите сделать?", reply_markup=markup)


# Запрос админа на выгрузку всех обращений
@dp.message(F.text == "Выгрузить все обращения")
async def send_appends(message: types.Message):
    if get_file():
        markup = get_menu(message.chat.id)
        file = FSInputFile('All_appeals.xlsx')
        await bot.send_document(message.chat.id, file, reply_markup=markup)


@dp.message(F.text == "Изменить статус обращения")
async def change_status(message: types.Message, state: FSMContext):
    await message.answer("Напишите номер обращения")
    await state.set_state(AppForm.count)


@dp.message(AppForm.count)
async def get_number_appeal(message: types.Message, state: FSMContext):
    await state.clear()
    check = check_request(int(message.text))
    if check is not None:
        if check[2] in types_appeals:
            markup = get_status(types_appeals[check[2]])
            await message.answer("На что изменить статус?", reply_markup=markup.as_markup(resize_keyboard=True))
            stat[message.chat.id] = [int(message.text)]
            await state.set_state(StatForm.count)
        else:
            await message.answer("У благодарностей нет статуса")
            await change_status(message, state)
    else:
        await message.answer("Обращения с таким номером не существует")


@dp.message(StatForm.count)
async def get_new_stat(message: types.Message):
    check = check_request(stat[message.chat.id][0])
    await bot.send_message(check[1], f'Ваше обращение {check[0]} изменило статус на "{message.text}"')
    await message.answer("Статус изменён", reply_markup=get_menu(message.chat.id))


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
        stat[message.chat.id] = [admin]
        stat[admin] = [message.chat.id]
        if admin not in user_chat:
            await bot.send_message(admin, "Пришёл запрос на общение с администрацией.", reply_markup=markup)

    else:
        button = [[types.KeyboardButton(text="Оставить обращение")]]
        markup = types.ReplyKeyboardMarkup(keyboard=button)
        await message.answer(
            "Время работы онлайн сотрудника: ПН-ПТ с 10:00 до 16:00. Запрос можно оставить в рабочее время, а пока можете отправить обращение.",
            reply_markup=markup)


# Начало чата с представителем
@dp.callback_query(F.data, F.func(lambda msg: msg.data not in ["approval", "not_robot", "email", "address"]))
async def start_chat(callback: types.CallbackQuery):
    button = [[types.KeyboardButton(text="Завершить чат")]]
    markup = types.ReplyKeyboardMarkup(keyboard=button)
    user_chat.add(admin)
    user_chat.add(int(callback.data))
    await bot.delete_message(callback.message.chat.id, callback.message.message_id)
    await bot.send_message(int(callback.data), "Представитель начал чат", reply_markup=markup)
    await callback.message.answer("Вы начали чат", reply_markup=markup)


# Завершение чата представителем или пользователем
@dp.message(F.text == "Завершить чат")
async def end_chat(message: types.Message):
    user_id = message.chat.id
    await bot.send_message(admin, "Чат завершён", reply_markup=admin)
    await message.answer("Чат завершён", reply_markup=get_menu(user_id))
    user_chat.discard(user_id)
    user_chat.discard(stat[user_id][0])

    def delet(user):
        if user == admin:
            del stat[user][0]
            if stat[user] >= 1:
                button = [[types.InlineKeyboardButton(text="Начать чат", callback_data=str(stat[user_id][0]))]]
                markup = types.InlineKeyboardMarkup(inline_keyboard=button)
                return True, markup
        else:
            del stat[user]
            return False, ''

    bol, markup = delet(stat[user_id][0])
    if bol:
        await bot.send_message(admin, "Пришёл запрос на общение с администрацией.", reply_markup=markup)

    bol, markup = delet(user_id)
    if bol:
        await bot.send_message(user_id, "Пришёл запрос на общение с администрацией.", reply_markup=markup)


# Посмотреть карту обращений
@dp.message(F.text == "Посмотреть карту обращений")
async def look_kart(message: types.Message):
    user_id = message.chat.id
    text = "Предлагаем вам посмотреть карту обращений. На ней отражена актуальная информация. Если вашего обращения ещё нет, значит оно на рассмотрении."
    link = "https://yandex.ru/maps/?um=constructor%3A5b85c707df5feba269aa8f20aa4773b24af0ea9d09d80d2c14e9e025e0eeafd0&source=constructorLink"
    if user_id == admin:
        text = "Помимо просмотра, вы также можете редактировать карту. За данными для входа, обратитесь к администратору."
    buttons = [[types.InlineKeyboardButton(text="Посмотреть карту", url=link)]]
    markup = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(text, reply_markup=markup)


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
        await look_kart(message)

    elif user_id in user_chat:
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
    elif user_id in user_chat:
        media, text = message.photo[-1].file_id, message.caption
        await bot.send_photo(stat[user_id][0], media, caption=text)


# При отправке видео
@dp.message(F.video)
async def add_content_app(message: types.Message):
    # Подразумевается чат с представителем
    if message.chat.id in user_chat:
        media, text = message.video.file_id, message.caption
        await bot.send_document(stat[message.chat.id][0], media, caption=text)
    else:
        await start(message)


# При отправке документа
@dp.message(F.document)
async def send_document(message: types.Message):
    # Подразумевается чат с представителем
    if message.chat.id in user_chat:
        media, text = message.document.file_id, message.caption
        await bot.send_document(stat[message.chat.id][0], media, caption=text)
    else:
        await start(message)


# Добавление email для получения на него ответа
@dp.callback_query(F.data == "email")
async def getting_main_menu(callback: types.CallbackQuery):
    await bot.delete_message(callback.message.chat.id, callback.message.message_id)
    await callback.message.answer("Напишите вашу электронную почту")


# Получение ответа на дом
@dp.callback_query(F.data == "address")
async def getting_main_menu(callback: types.CallbackQuery):
    markup = get_menu(callback.message.chat.id)
    user_id = callback.message.chat.id
    dop = reply[stat[user_id][2]]
    text = f"Номер вашего обращения {stat[user_id][1]}.\n{dop}"
    del stat[user_id]
    await bot.delete_message(callback.message.chat.id, callback.message.message_id)
    await callback.message.answer(text, reply_markup=markup)
    text = "Предлагаем вам посмотреть карту обращений. На ней отражена актуальная информация. Если вашего обращения ещё нет, значит оно на рассмотрении."
    link = "https://yandex.ru/maps/?um=constructor%3A5b85c707df5feba269aa8f20aa4773b24af0ea9d09d80d2c14e9e025e0eeafd0&source=constructorLink"
    buttons = [[types.InlineKeyboardButton(text="Посмотреть карту", url=link)]]
    markup = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.answer(text, reply_markup=markup)


# Запуск процесса поллинга новых апдейтов
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
