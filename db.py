import sqlite3


class Table():
    'Класс для работы с таблицой в базе данных'

    def __init__(self, name, db, columns=None):
        self.name = name
        self.db = db
        self.columns = columns

    # Метод для создания таблицы
    def create_table(self):
        col = ', '.join(k + ' ' + v for k, v in self.columns.items())

        # Создаём таблицу если отсутствует
        connection = sqlite3.connect(self.db)
        cursor = connection.cursor()
        cursor.execute(f"CREATE TABLE IF NOT EXISTS {self.name} ({col})")
        connection.commit()
        connection.close()

    # Добавляем запись в таблицу
    def add_value(self, col: list[str], values: tuple[None, ...]):
        connection = sqlite3.connect(self.db)
        cursor = connection.cursor()

        # Функция формирования запроса для добавления записи
        def generate_addition_request(name, columns):
            col = ', '.join(columns)
            empty_value = ', '.join(['?' for _ in columns])
            return f"INSERT INTO {name} ({col}) VALUES ({empty_value})"

        # Добавление записи в таблицу
        request = generate_addition_request(self.name, col)
        try:
            cursor.execute(request, values)
            connection.commit()
            connection.close()
        except sqlite3.IntegrityError:
            print('Запись о пользователе уже есть в таблице.')

        # Обновляем атрибуты
        for i in col:
            self.columns[i] = ''

    # Обновляем запись в таблице
    def update_value(self, col: list[str], values: tuple[None, ...]):
        connection = sqlite3.connect(self.db)
        cursor = connection.cursor()

        # Функция формирования запроса для добавления записи
        def generate_addition_request(name, columns):
            col = '= ?'.join(columns[:-1]) + ' = ?'
            return f"UPDATE {name} SET {col} WHERE {columns[-1] + ' = ?'}"

        # Добавление записи в таблицу
        request = generate_addition_request(self.name, col)
        cursor.execute(request, values)
        connection.commit()
        connection.close()

        # Обновляем атрибуты
        for i in col:
            self.columns[i] = ''
