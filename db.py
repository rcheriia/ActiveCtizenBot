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
        connection = sqlite3.connect(self.db, timeout=2)
        cursor = connection.cursor()
        cursor.execute(f"CREATE TABLE IF NOT EXISTS {self.name} ({col})")
        connection.commit()
        connection.close()

    def record_exists(self, col, id):
        with sqlite3.connect(self.db) as connection:
            cursor = connection.cursor()
            cursor.execute(f"SELECT 1 FROM {self.name} WHERE {col} = ?", (id,))
            return cursor.fetchone() is not None

    # Добавляем запись в таблицу
    def add_value(self, col: list[str], values: tuple[Any, ...]):
        # Функция формирования запроса для добавления записи
        def generate_addition_request(name, columns):
            count = ', '.join(columns)
            empty_value = ', '.join(['?' for _ in columns])
            return f"INSERT INTO {name} ({count}) VALUES ({empty_value})"

        # Добавление записи в таблицу
        request = generate_addition_request(self.name, col)
        connection = sqlite3.connect(self.db)
        cursor = connection.cursor()
        ret = 0

        if not self.record_exists(col[0], values[0]):
            try:
                cursor.execute(request, values)
                connection.commit()
                connection.close()
                ret = 1

            except sqlite3.OperationalError:
                self.add_value(col, values)

        else:
            print('Запись уже есть в таблице.')

            # Обновляем атрибуты
            for i in col:
                self.columns[i] = ''

        return ret

    # Обновляем запись в таблице
    def update_value(self, col: list[str], values: tuple[Any, ...]):
        # Функция формирования запроса для добавления записи
        def generate_addition_request(name, columns):
            count = ' = ?, '.join(columns[1:]) + ' = ?'
            return f"UPDATE {name} SET {count} WHERE {columns[0] + ' = ?'}"

        # Добавление записи в таблицу
        if not self.record_exists(col[0], values[0]):
            print('Записи нет в таблице.')

        else:
            try:
                request = generate_addition_request(self.name, col)
                connection = sqlite3.connect(self.db)
                cursor = connection.cursor()

                cursor.execute(request, (*values[1:], values[0]))
                connection.commit()
                connection.close()

            except sqlite3.OperationalError:
                self.update_value(col, values)

        # Обновляем атрибуты
        for i in col:
            self.columns[i] = ''

    def get_all_rows(self):
        with sqlite3.connect(self.db) as connection:
            cursor = connection.cursor()
            cursor.execute(f"SELECT * FROM {self.name}")
            return cursor.fetchall()
