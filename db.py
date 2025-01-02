import sqlite3
from typing import Any


class Table():
    'Класс для работы с таблицей в базе данных'

    def __init__(self, name, db, columns=None):
        self.name = name
        self.db = db
        self.columns = columns

    # Метод для создания таблицы
    def create_table(self):
        col = ', '.join(k + ' ' + v for k, v in self.columns.items())

        # Создаём таблицу если отсутствует
        connection = sqlite3.connect(self.db, timeout=10.0)
        cursor = connection.cursor()
        cursor.execute(f"CREATE TABLE IF NOT EXISTS {self.name} ({col})")
        connection.commit()
        connection.close()

    # Добавляем запись в таблицу
    def add_value(self, col: list[str], values: tuple[Any, ...]):
        # Функция формирования запроса для добавления записи
        def generate_addition_request(name, columns):
            count = ', '.join(columns)
            empty_value = ', '.join(['?' for _ in columns])
            return f"INSERT INTO {name} ({count}) VALUES ({empty_value})"

        # Добавление записи в таблицу
        request = generate_addition_request(self.name, col)
        connection = sqlite3.connect(self.db, timeout=10.0)
        cursor = connection.cursor()

        try:
            cursor.execute(request, values)
            connection.commit()
            connection.close()
            ret = 1
        except sqlite3.IntegrityError:
            print('Запись уже есть в таблице.')
            ret = 0
        except sqlite3.OperationalError:
            print('Что-то не то')

        # Обновляем атрибуты
        for i in col:
            self.columns[i] = ''

        return ret

    # Обновляем запись в таблице
    def update_value(self, col: list[str], values: tuple[Any, ...]):
        # Функция формирования запроса для добавления записи
        def generate_addition_request(name, columns):
            count = ' = ?, '.join(columns[:-1]) + ' = ?'
            return f"UPDATE {name} SET {count} WHERE {columns[-1] + ' = ?'}"

        # Добавление записи в таблицу
        request = generate_addition_request(self.name, col)
        connection = sqlite3.connect(self.db, timeout=10.0)
        cursor = connection.cursor()

        cursor.execute(request, values)
        connection.commit()
        connection.close()

        # Обновляем атрибуты
        for i in col:
            self.columns[i] = ''
