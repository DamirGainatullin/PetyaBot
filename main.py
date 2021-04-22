import requests
from telegram.ext import Updater, MessageHandler, Filters
from telegram.ext import CallbackContext, CommandHandler
from time import asctime, localtime
from telegram import ReplyKeyboardMarkup
from telegram import ReplyKeyboardRemove

bookmarks = {}
reply_keyboard = [['/search', '/location', '/bookmarks']]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
org_info = {}


def view_bookmarks(update, context):
    with open('bookmarks.txt', 'r') as f:
        f = f.read().split('   ')[:-1]
        if f == []:
            update.message.reply_text('Здесь пока пусто')
        else:
            for i in f:
                update.message.reply_text(i)


def add_bookmark(update, context):
    bookmarks[current_org] = org_info[current_org]
    with open('bookmarks.txt', 'a') as f:
        for i in bookmarks:
            f.write(
                f"{i}: {'Время работы' + bookmarks[i][0] + '; ' + 'Телефон' + bookmarks[i][1] + '; ' + 'Сайт' + bookmarks[i][2]}   ")
    markup = ReplyKeyboardMarkup(reply_keyboard_org, one_time_keyboard=True)
    update.message.reply_text('Организация добавлена в закладки', reply_markup=markup)


def close_keyboard(update, context):
    update.message.reply_text(
        "Для продолжения нажмите введите /start",
        reply_markup=ReplyKeyboardRemove()
    )


def start(update, context):
    update.message.reply_text(
        "Я бот-справочник. Я могу помочь вам найти нужную вам организацию и сохранить данные о ней в закладках",
        reply_markup=markup
    )


def echo(update, context):
    global current_org
    user_text = update.message.text
    if user_text[:6] == 'Покажи':
        adres = user_text[7:]
        geocoder1(update, context, adres)
    elif user_text in org_info:
        current_org = user_text
        reply_keyboard = [['/add', 'Выйти']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        update.message.reply_text(f'Время работы: {org_info[user_text][0]}')
        update.message.reply_text(f'Контактный телефон: {org_info[user_text][1]}')
        update.message.reply_text(f'Сайт: {org_info[user_text][2]}', reply_markup=markup)
    elif user_text == 'Выйти':
        close_keyboard(update, context)
    elif user_text[:7] == 'Рядом с':
        adres = ' '.join(user_text.split()[2:-1])
        org_type = user_text.split()[-1]
        answ = geocoder2(update, context, adres, org_type)
        if answ == ('', ''):
            update.message.reply_text('Не удается распознать адрес')
        else:
            update.message.reply_text(f'Ближайшая к вам {org_type} это {answ[0]}. Адрес:{answ[1]}')


def geocoder1(update, context, adres):
    global org_info
    global reply_keyboard_org
    text = update.message.text
    geocoder_uri = geocoder_request_template = "http://geocode-maps.yandex.ru/1.x/"
    response = requests.get(geocoder_uri, params={
        "apikey": "40d1649f-0493-4b70-98ba-98533de7710b",
        "format": "json",
        "geocode": adres
    })
    if response.json()["response"]["GeoObjectCollection"]["featureMember"] == []:
        update.message.reply_text('Не удается распознать адрес')
    else:
        toponym = response.json()["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]
        toponym_coodrinates = toponym["Point"]["pos"]

        # Долгота и широта:
        toponym_longitude, toponym_lattitude = toponym_coodrinates.split(" ")

        delta = "0.005"

        ll = ",".join([toponym_longitude, toponym_lattitude])
        spn = ",".join([delta, delta])

        static_api_request = f"http://static-maps.yandex.ru/1.x/?ll={ll}&spn={spn}&l=map"

        context.bot.send_photo(
            update.message.chat_id,  # Идентификатор чата. Куда посылать картинку.
            # Ссылка на static API, по сути, ссылка на картинку.
            # Телеграму можно передать прямо её, не скачивая предварительно карту.
            static_api_request,
        )
        # update.message.reply_text("Показать организации находящиеся в этом здании?")

        search_api_server = "https://search-maps.yandex.ru/v1/"
        api_key = "dda3ddba-c9ea-4ead-9010-f43fbc15c6e3"

        toponym = response.json()["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]
        toponym_coodrinates = toponym["Point"]["pos"]
        toponym_longitude, toponym_lattitude = toponym_coodrinates.split(" ")
        ll = ",".join([toponym_longitude, toponym_lattitude])

        search_params = {
            "apikey": api_key,
            "text": adres,
            "lang": "ru_RU",
            "ll": ll,
            "type": "biz"
        }

        response = requests.get(search_api_server, params=search_params)

        json_response = response.json()
        if "features" in json_response:
            organization = json_response["features"]
            reply_keyboard_org = []
            org_info = {}
            for i in organization:
                # Название организации.
                org_name = i["properties"]["CompanyMetaData"]["name"]
                if "Hours" in i["properties"]["CompanyMetaData"]:
                    org_hours = i["properties"]["CompanyMetaData"]["Hours"]["text"]
                else:
                    org_hours = 'не указано'
                if "Phones" in i["properties"]["CompanyMetaData"]:
                    org_phones = i["properties"]["CompanyMetaData"]["Phones"][0]["formatted"]
                else:
                    org_phones = 'не указано'
                if "url" in i["properties"]["CompanyMetaData"]:
                    org_site = i["properties"]["CompanyMetaData"]["url"]
                else:
                    org_site = 'не указано'
                reply_keyboard_org.append([org_name])
                org_info[org_name] = [org_hours, org_phones, org_site]
            reply_keyboard_org.append(['Выйти'])
            markup = ReplyKeyboardMarkup(reply_keyboard_org, one_time_keyboard=True)
            update.message.reply_text(f'В данном здании находится {len(organization)} организаций', reply_markup=markup)
        else:
            update.message.reply_text('В данном здании нет ни одной организации')

def location(update, context):
    update.message.reply_text("Чтобы получить информацию о запрашиваемом месте напишите 'Покажи', затем введите адрес")


def search(update, context):
    update.message.reply_text(
        "Чтобы получить информацию о организациях находящихся радом с вами напишите 'Рядом с', затем введите адрес и тип нужной вам организации")


def geocoder2(update, context, adres, org_type):
    geocoder_uri = geocoder_request_template = "http://geocode-maps.yandex.ru/1.x/"
    response = requests.get(geocoder_uri, params={
        "apikey": "40d1649f-0493-4b70-98ba-98533de7710b",
        "format": "json",
        "geocode": adres
    })
    search_api_server = "https://search-maps.yandex.ru/v1/"
    api_key = "dda3ddba-c9ea-4ead-9010-f43fbc15c6e3"
    response_json = response.json()
    if response_json["response"]["GeoObjectCollection"]["featureMember"] == []:
        return ('', '')
    else:
        toponym = response_json["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]
        toponym_coodrinates = toponym["Point"]["pos"]
        toponym_longitude, toponym_lattitude = toponym_coodrinates.split(" ")
        ll = ",".join([toponym_longitude, toponym_lattitude])

        search_params = {
            "apikey": api_key,
            "text": org_type,
            "lang": "ru_RU",
            "ll": ll,
            "type": "biz"
        }

        response = requests.get(search_api_server, params=search_params)
        json_response = response.json()
        organization = json_response["features"][0]
        # Название организации.
        org_name = organization["properties"]["CompanyMetaData"]["name"]
        # Адрес организации.
        org_address = organization["properties"]["CompanyMetaData"]["address"]
        return (org_name, org_address)


def main():
    updater = Updater('1606712089:AAGxH6jPxJPF_UHdoWxsSsUojucK30Exh_Y', use_context=True)

    dp = updater.dispatcher

    text_handler = MessageHandler(Filters.text, echo)
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("location", location))
    dp.add_handler(CommandHandler("add", add_bookmark))
    dp.add_handler(CommandHandler("bookmarks", view_bookmarks))
    dp.add_handler(CommandHandler("search", search))
    dp.add_handler(text_handler)
    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
