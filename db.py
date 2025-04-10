import psycopg2
from typing import Any


class Table:
    """Класс для работы с таблицей в базе данных"""

    def __init__(self, name, dbname, user='postgres', password='', host='localhost', port=5432, columns=None):
        self.conn = {'dbname': dbname, 'user': user, 'password': password, 'host': host, 'port': port}
        self.name = name
        self.columns = columns

    # Метод для создания таблицы
    def create_table(self):
        with psycopg2.connect(**self.conn) as connection:
            col = ', '.join(k + ' ' + v for k, v in self.columns.items())
            # Создаём таблицу если отсутствует
            cursor = connection.cursor()
            cursor.execute(f"CREATE TABLE IF NOT EXISTS {self.name} ({col})")

    def record_exists(self, col: str, number: int):
        with psycopg2.connect(**self.conn) as connection:
            cursor = connection.cursor()
            cursor.execute(f"SELECT * FROM {self.name} WHERE {col} = {number}")
            return cursor.fetchone()

    # Добавляем запись в таблицу
    def add_value(self, col: list[str], values: tuple[Any, ...]):
        # Функция формирования запроса для добавления записи
        def generate_addition_request(name, columns):
            count = ', '.join(columns)
            empty_value = ', '.join(['%s' for _ in columns])
            return f"INSERT INTO {name} ({count}) VALUES ({empty_value})"

        # Добавление записи в таблицу
        request = generate_addition_request(self.name, col)
        connection = psycopg2.connect(**self.conn)
        cursor = connection.cursor()
        ret = 0

        if self.record_exists(col[0], values[0]) is None:
            try:
                cursor.execute(request, values)
                connection.commit()
                connection.close()
                ret = 1

            except psycopg2.OperationalError:
                self.add_value(col, values)

            except psycopg2.errors.NumericValueOutOfRange:
                print(col, values)

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
            count = ' = %s, '.join(columns[1:]) + ' = %s'
            return f"UPDATE {name} SET {count} WHERE {columns[0] + ' = %s'}"

        # Добавление записи в таблицу
        if self.record_exists(col[0], values[0]) is None:
            print('Записи нет в таблице.')

        else:
            try:
                request = generate_addition_request(self.name, col)
                with psycopg2.connect(**self.conn) as connection:
                    cursor = connection.cursor()
                    cursor.execute(request, (*values[1:], values[0]))
                    if 'long' in col:
                        cursor.execute(f"UPDATE {self.name} SET geom = ST_SetSRID(ST_MakePoint(long, lat), 4326)")

            except psycopg2.OperationalError:
                self.update_value(col, values)

        # Обновляем атрибуты
        for i in col:
            self.columns[i] = ''

    def get_all_rows(self, cond: str):
        with psycopg2.connect(**self.conn) as connection:
            cursor = connection.cursor()
            cursor.execute(f"SELECT * FROM {self.name}" + cond)
            return cursor.fetchall()

    def add_col(self, name_col, type_col):
        with psycopg2.connect(**self.conn) as connection:
            cursor = connection.cursor()
            cursor.execute(f"ALTER TABLE {self.name} ADD COLUMN {name_col} {type_col}")
