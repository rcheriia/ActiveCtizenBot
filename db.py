import sqlite3


class Table():
    'Класс для создания таблиц и внесения записей'

    def __init__(self, name, db):
        self.name = name
        self.db = db
        self._columns = []

    def create_table(self, key, columns):
        self._columns = columns.keys()
        col = ', '.join(k + ' ' + v for k, v in columns.items())

        connection = sqlite3.connect(self.db)
        cursor = connection.cursor()
        cursor.execute(f"CREATE TABLE IF NOT EXISTS {self.name} ({col})")
        connection.commit()
        connection.close()

    def add_value(self, values):
        connection = sqlite3.connect(self.db)
        cursor = connection.cursor()

        def generate_addition_request(col):
            col = ', '.join(col)
            empty_value = ', '.join(['?' for _ in col])
            return f"INSERT INTO Users ({col}) VALUES ({empty_value})"

        request = generate_addition_request(self._columns)
        cursor.execute(request, (values))
        connection.commit()
        connection.close()


users = Table("users", "activectizen.db")
col = {"user_id": "INTEGER PRIMARY KEY", "name": "TEXT NOT NULL", "address": "TEXT NOT NULL", "email": "TEXT"}
users.create_table("user_id", col)