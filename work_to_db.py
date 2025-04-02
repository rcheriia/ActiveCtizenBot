from datetime import date
from db_sqlite import Table
from location import types_appeals

number_hits = ''
cnt = 1

'''Пометка по работе с классом:
При добавлении или обновлении уже существующего первыми прописывается ключ и его значение, потом уже остальное.
'''

# Создание таблицы пользователей
col = {"user_id": "BIGINT PRIMARY KEY", "name": "TEXT NOT NULL", "phone_number": "TEXT", "address": "TEXT",
       "email": "TEXT"}
users = Table("users", "ActiveBot.db", columns=col)
users.create_table()

# Создание таблицы обращений
col = {"appeal_id": "BIGINT PRIMARY KEY", "user_id": "BIGINT NOT NULL", "category": "TEXT NOT NULL",
       "chapter": "TEXT", "text": "TEXT", "media_id": "TEXT", "status": "TEXT", 'lat': 'FLOAT', 'long': 'FLOAT'}
appeals = Table("appeals", "ActiveBot.db", columns=col)
appeals.create_table()


# Добавление пользователя в таблицу user
def add_user(user_id: int, name: str):
    users.add_value(["user_id", "name"], (user_id, name))


def add_phone_number(user_id: int, phone_number: str):
    users.update_value(["user_id", "phone_number"], (user_id, phone_number))


# Добавляем адрес уже к существующему пользователю
def add_address(ap_id: int, user_id: int, address: str, lat: float, long: float):
    users.update_value(["user_id", "address"], (user_id, address))
    appeals.update_value(['appeal_id', 'lat', 'long'], (ap_id, lat, long))


# Если ответ нужно доставить по электронной почте
def add_email(user_id: int, email: str):
    users.update_value(["user_id", "email"], (user_id, email))


# Добавление обращения в таблицу appeals
def add_appeal(category: str, user_id: int):
    global number_hits, cnt
    # Формирование номера обращения
    data = str(date.today()).replace('-', '')
    if data[2:] == number_hits:
        cnt += 1
    else:
        number_hits, cnt = data[2:], 2
    count = cnt
    n = str(count) if count > 9 else '0' + str(count)
    ap_id = int(data[2:] + n)

    st = types_appeals.get(category, [''])

    appeals.add_value(["appeal_id", "user_id", "category", "status"], (ap_id, user_id, category, st[0]))

    return ap_id


# Добавление текста и фотографии, если есть
def add_content_appeal(number: int, text: str, media_id=None):
    appeals.update_value(["appeal_id", "text", "media_id"], (number, text, media_id))


def add_chapter(number: int, chapter: str):
    appeals.update_value(["appeal_id", "chapter"], (number, chapter))


def check_request(number: int):
    return appeals.record_exists("appeal_id", number)


def change_stat(number: int, status: str):
    appeals.update_value(["appeal_id", "status"], (number, status))


def all_is_st():
    return appeals.get_all_rows(
        " WHERE NOT status = 'Ответ направлен на Вашу электронную почту' AND NOT status = 'Ответ направлен по адресу заявителя' AND NOT status = 'Предложение реализовано'")
