import xlsxwriter
from db_sqlite import Table
import telebot
from config import token, token_ya
import yadisk

client = yadisk.Client(token=token_ya)
bot = telebot.TeleBot(token)


def load_photo_in_disk(name):
    with open(name, "rb") as f:
        if not client.is_file(name):
            client.upload(f, name)
            client.publish(name)

    return client.get_meta(name).public_url


def download_photo(photo_id, ap_id):
    file = bot.get_file(photo_id)
    dow_file = bot.download_file(file.file_path)
    with open(f'{ap_id}.jpg', 'wb') as f:
        f.write(dow_file)
    return load_photo_in_disk(f'{ap_id}.jpg')


def get_file():
    workbook = xlsxwriter.Workbook('All_appeals.xlsx')
    worksheet = workbook.add_worksheet()
    bold = workbook.add_format({'bold': True})
    italic = workbook.add_format({'italic': True, 'bold': True})

    appeals = Table("appeals", "ActiveBot.db")
    ap = appeals.get_all_rows('')

    users = Table("users", "ActiveBot.db")
    user = {x[0]: x[1:] for x in users.get_all_rows('')}

    rows = ["Номер обращения", "Категория", "Раздел", "Текст", "Фото", "Статус", "ФИО", "Телефон", "Адрес", "Эл. почта"]
    for i in range(len(rows)):
        worksheet.write(0, i, rows[i], italic)

    for i in range(len(ap)):
        appeal = list(ap[i])
        ap_id = appeal.pop(0)
        user_id = appeal.pop(0)
        appeal[-4] = download_photo(appeal[-4], ap_id) if appeal[-4] else ''
        worksheet.write(i + 1, 0, ap_id, bold)
        for row in range(len(appeal))[:-2]:
            worksheet.write(i + 1, row + 1, appeal[row])

        info_user = user[user_id]
        for row in range(len(info_user)):
            worksheet.write(i + 1, row + len(appeal) - 1, info_user[row])

    workbook.close()

    return True

