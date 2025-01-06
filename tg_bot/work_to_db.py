from datetime import date
from db import Table

number_hits = {}

'''Пометка по работе с классом:
При добавлении или обновлении уже существующего первыми прописывается ключ и его значение, потом уже остальное.
'''
# Создание таблицы пользователей
col = {"user_id": "INTEGER PRIMARY KEY", "name": "TEXT NOT NULL", "phone_number": "TEXT", "address": "TEXT",
       "email": "TEXT"}
users = Table("users", "ActiveBot.db", columns=col)
users.create_table()

# Создание таблицы обращений
col = {"appeal_id": "INTEGER PRIMARY KEY", "user_id": "INTEGER NOT NULL", "category": "TEXT NOT NULL",
       "chapter": "TEXT", "text": "TEXT", "media_id": "INTEGER"}
appeals = Table("appeals", "ActiveBot.db", columns=col)
appeals.create_table()


# Добавление пользователя в таблицу user
def add_user(user_id: int, name: str):
    users.add_value(["user_id", "name"], (user_id, name))


def add_phone_number(user_id: int, phone_number: str):
    users.update_value(["user_id", "phone_number"], (user_id, phone_number))


# Добавляем адрес уже к существующему пользователю
def add_address(user_id: int, address: str):
    users.update_value(["user_id", "address"], (user_id, address))


# Если ответ нужно доставить по электронной почте
def add_email(user_id: int, email: str):
    users.update_value(["user_id", "email"], (user_id, email))


# Добавление обращения в таблицу appeals
def add_appeal(category: str, user_id: int):
    # Формирование номера обращения
    data = str(date.today()).replace('-', '')
    count = number_hits.setdefault(data, 1)
    n = str(count) if count > 9 else '0' + str(count)
    ap_id = int(data[2:] + n)

    number_hits[data] += appeals.add_value(["appeal_id", "user_id", "category"], (ap_id, user_id, category))

    return ap_id


# Добавление текста и фотографии, если есть
def add_content_appeal(number: int, text: str, media_id=None):
    appeals.update_value(["appeal_id", "text", "media_id"], (number, text, media_id))


def add_chapter(number: int, chapter: str):
    appeals.update_value(["appeal_id", "chapter"], (number, chapter))
