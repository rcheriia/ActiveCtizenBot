from datetime import date
from db import Table

number_hits = {}

# Создание таблицы пользователей
col = {"user_id": "INTEGER PRIMARY KEY", "name": "TEXT NOT NULL", "phone_number": "TEXT", "address": "TEXT",
       "email": "TEXT"}
users = Table("users", "ActiveBot.db", columns=col)
users.create_table()

# Создание таблицы обращений
col = {"appeal_id": "INTEGER PRIMARY KEY", "user_id": "INTEGER NOT NULL", "text": "TEXT",
       "media_id": "INTEGER", "category": "TEXT NOT NULL"}
appeals = Table("appeals", "ActiveBot.db", columns=col)
appeals.create_table()


# Добавление пользователя в таблицу user
def add_user(user_id: int, name: str):
    users.add_value(["user_id", "name"], (user_id, name))

def add_phone_number(user_id: int, phone_number: str):
    users.update_value(["phone_number", "user_id"], (phone_number, user_id))

# Добавляем адрес уже к существующему пользователю
def add_address(user_id: int, address: str):
    users.update_value(["address", "user_id"], (address, user_id))


# Если ответ нужно доставить по электронной почте
def add_email(user_id: int, email: str):
    users.update_value(["email", "user_id"], (email, user_id))


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
    appeals.update_value(["text", "media_id", "appeal_id"], (text, media_id, number))
