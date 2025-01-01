from datetime import date
from db import Table

number_hits = {}

# Создание таблицы пользователей
col = {"user_id": "INTEGER PRIMARY KEY", "name": "TEXT NOT NULL", "address": "TEXT NOT NULL", "email": "TEXT"}
users = Table("users", "ActiveCtizen.db", columns=col)
users.create_table()

# Создание таблицы обращений
col = {"appeal_id": "INTEGER PRIMARY KEY", "user_id": "INTEGER NOT NULL", "text": "TEXT NOT NULL",
       "media_id": "INTEGER"}
appeals = Table("appeals", "ActiveCtizen.db", columns=col)
appeals.create_table()


# Добавление пользователя в таблицу user
def add_user(user_id, name, address):
    users.add_value(["user_id", "name", "address"], (user_id, name, address))


# Добавление обращения в таблицу appeal
def add_appeal(user_id, text, media_id=None):
    # Формирование номера обращения
    data = str(date.today()).replace('-', '')
    col = number_hits.setdefault(data, 1)
    number_hits[data] += 1
    n = str(col) if col > 9 else '0' + str(col)
    id = data[2:] + n

    appeals.add_value(["appeal_id", "user_id", "text", "media_id"], (id, user_id, text, media_id))
