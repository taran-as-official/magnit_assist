from flask import Flask
from flask import request
from flask import jsonify
import requests
from flask_sslify import SSLify
from mysqldb import MySQL
import os, time
import config
import telebot
from parser import ParserRequestFromTelegram, ParserRequestFromYandex
import logging
import json
import re
from datetime import datetime,timedelta


logging.basicConfig(level=logging.DEBUG)

os.environ['TZ'] = config.TIME_ZONE
time.tzset()

app = Flask(__name__)
sslify = SSLify(app)
db = MySQL()


API_TOKEN = config.TELEGRAM_TOKEN_MAGNIT

# tekegram settings
host = config.TELEGRAM_HOST
path_to_api = '/bot' + API_TOKEN + '/'
URL = f"{host}{path_to_api}"
bot = telebot.TeleBot(API_TOKEN)
#dp = telebot.dispatcher(bot)


LINK_TO_TELEGRAM = "https://t.me/magnit_assist_bot"
def send_message(chat_id, text='default text'):
    url = URL + 'sendMessage'
    answer = {'chat_id': chat_id, 'text': text }
    r = requests.post(url, json = answer)
    return r.json()



@app.route('/login',methods=['POST'])
def login():

    logging.info("LOGIN: " + str(request.json))

    r = ParserRequestFromYandex(request.json)



    response = {
        "response": {
            "text": 'Какой то результат'
        }

    }



    return json.dumps(response)

#логига для Алисы списка покупок
@app.route('/get-list',methods=['POST'])
def getlist():

    logging.info("GETLIST: " + str(request.json))

    r = ParserRequestFromYandex(request.json)



    response = {
        "session": r.session,
        "response": {
            "end_session": False,
            "text": 'Дальше функционал не придуман, пишите что хотите',
            "list": {
                "items":[]
        },
        "session_state": {
        },
        "version": r.version,


        }
    }

    prod_list = db.get_yandex_list(phone_num = r.text)


    if list:
        response["response"]["list"]["items"] = prod_list


    return json.dumps(response)

@app.route('/get-list',methods=['POST'])
def getorder():

    logging.info("GETORDER: " + str(request.json))

    r = ParserRequestFromYandex(request.json)

    response = {
        "session": r.session,
        "response": {
            "end_session": False,
            "text": 'Дальше функционал не придуман, пишите что хотите',
            "list": {
                "items":[]
        },
        "session_state": {
        },
        "version": r.version,


        }
    }

    prod_list = db.get_yandex_list(phone_num = r.text,is_order = 1)


    if list:
        response["response"]["list"]["items"] = prod_list


    return json.dumps(response)


#логига для Алисы списка покупок
@app.route('/list-product',methods=['POST'])
def list():


    r = ParserRequestFromYandex(request.json)
    #logging.info("JSON: " + str(request.json))

    prod_list = db.get_yandex_list(phone_num = r.original_utterance)

    logging.info("СПИСОК: " + str(prod_list))

    response = {
        "session": r.session,
        "response": {
            "end_session": False,
            "text": 'Дальше функционал не придуман, пишите что хотите'
        },
        "session_state": {
        },
        "version": r.version


    }

    #ищем пользователя в нашей базе, результат возвращается кортежем: (('id','имя','фамилия'),)
    user = db.yandex_user_exists(r.user_id, r.application_id)
    logging.info("пользователь: " + str(user))

    mess = ""

    #если текущая стадия пользователя '1' - знакомство, то заходим в эту ветку пока не узнаем его имя
    if user["id_stage"] == 0:


        #если новая сессия, то здороваемся и спрашиваем имя
        if r.new_session:
            mess = "Привет, как тебя зовут?"

            #отправляем приветственную картинку
            #img = {
            #      "type": "BigImage",
            #      "image_id": "213044/74c83c1a5365983fa045",
            #      "title": "Акция! Хлеб в магните всего за 10 рублей",
            #      "description": "Список покупок: \nхелб\nколбаса\n\nОтправить почтой?"
            #     }
            #response["response"]["card"] = img
        else:
            #если сообщение не первое, значит ждем пока пользователь представится

            db.update_yandex_user(r.user_id,  r.first_name,r.last_name,r.patronymic_name)
            #ищем имя, если не находим то просим сказать
            if r.first_name:
                mess = "Приятно познакомиться, " + r.first_name.title() + ", могу помочь вам осуществить покупку, я умею составлять список покупок и делать онлайн заказ, что из этого вы бы хотели?"

                #если пользователь наконец представился проставим ему стадию 10 - СТАРТ
                db.update_yandex_user(r.user_id, stage_code = 10)

            elif r.last_name:
                mess = "Спасибо, что поделились Вашей фамилией, но мне нужно только имя"
            elif r.patronymic_name:
                mess = "Отличное отчество, интересно узнать какое же у вас имя?"
            else:
                mess = "Я не знаю такого имени, скажи своё земное имя"



    #если текущая стадия пользователя 10 (Старт) - то ждем от пользователя пока он не выберет что-нибудь
    if user["id_stage"] == 10:

        #из этой стадии мы должны попасть на стадию "Формирование списка"
        new_st_code = 20


        #ищем команду
        if re.search(r'список', r.original_utterance.lower()):

            mess = "Окей, записываю"

            #создадим список
            db.add_yandex_list(user["id_user_local"])
            #присвоим стадию формирование списка
            db.update_yandex_user(r.user_id, stage_code = new_st_code)

        elif re.search(r'заказ', r.original_utterance.lower()):

            mess = "Хорошо, записываю"

            #создадим список, с признаком заказ , передаем 1 в параметр
            db.add_yandex_list(user["id_user_local"], 1)
            #присвоим стадию формирование списка
            db.update_yandex_user(r.user_id, stage_code = new_st_code)

        elif re.search(r'ничего|выход|выкл|отмена', r.original_utterance.lower()):
            mess = "Окей, для выхода из навыка скажите \"Хватит\""

        else:
            if r.new_session:
                mess = "Привет, " + user["first_name"] + ". Что будем создавать? список покупок или онлайн заказ?"

            else:
                mess = "Пока я умею только формировать список и заказ, что из этого вы бы хотели?"
                #отправляем приветственную картинку



    #если текущая стадия пользователя 20 (Формирование списка), то добавляем данные в список, до тех пор пока он не скажет готово
    if user["id_stage"] == 20:



        finish = False

        if r.new_session:
            mess = "Привет, " + user["first_name"] + ", вы не завершили заполнение списка, продолжайте перечислять товары для добавления"
        else:

            #добавляем по одному все товары, что пользователь указал в запросе, пока не скажет готово
            for item in r.tokens:
                if re.search(r'вс(е|ё)|достаточно|готово|завершить|записать|сохран|подтверж|хватит|запиши|конец|выйти|выход|стоп|останов|дальше|далее', item):
                    finish = True
                    break
                else:
                    db.add_yandex_list_product(user["active_list"], item)
                    mess = "Записала"

            if finish:
                #проверяем, чтобы список был не пустой
                list_products = db.get_yandex_list(user["active_list"])

                #если пустой, то отслыаем в самое начало
                if not(list_products):
                    mess = "Список пуст, как будете готовы, попросите меня сделать список или заказ"
                    db.update_yandex_user(r.user_id, stage_code = 10) # переходим на СТАРТ
                else:
                    #ищем рецепт и предлагаем добавить товар в список
                    recipe = db.find_yandex_product_recipe(user["active_list"])


                    if recipe:
                        recipe_list = ""
                        for item in recipe["products"]:
                            recipe_list = recipe_list + item + "\n"
                        mess = "Нашла подходящий рецепт для вашего списка, чтобы приготовить " + recipe["name"] + " вам не хватает:\n\n" + recipe_list + "\n\nДобавить в список?"

                        img = {
                          "type": "BigImage",
                          "image_id": "1652229/bdbc730d9af3bfe5d76d",
                          "title": "↓↓↓",
                          "description": recipe_list
                        }
                        response["response"]["card"] = img

                        db.update_yandex_user(r.user_id, stage_code = 21) # переходим на стадию ожидания подтверждения добавления

                    else:
                        if user["is_list_order"] == 1:

                            user["id_stage"] = 30 #отправляем на стадию 30, проверки данных для заказа

                        #если просто список
                        elif user["is_list_order"] == 0:

                            user["id_stage"] = 40 #отправляем на стадию 40, отправки обычных списков

                        db.update_yandex_user(r.user_id, stage_code = user["id_stage"])

    #если текущая стадия пользователя 21 (Добавление рецепта), то добавляем данные в список из рецепта
    if user["id_stage"] == 21:

        def next_stage():
            if user["is_list_order"] == 1:
                user["id_stage"] = 30 #отправляем на стадию 30, проверки данных для заказа
            #если просто список
            elif user["is_list_order"] == 0:
                user["id_stage"] = 40 #отправляем на стадию 40, отправки обычных списков
            db.update_yandex_user(r.user_id, stage_code = user["id_stage"])


        recipe = db.find_yandex_product_recipe(user["active_list"])

        if r.new_session:

            recipe_list = ""
            for item in recipe["products"]:
                recipe_list = recipe_list + item + "\n"

            mess = "Привет, " + user["first_name"] + ", вы не завершили заполнение списка, нашла рецепт " + recipe["name"] + " для вашего списка, не хватает:\n\n" + recipe_list + "\n\nДобавить?"

            img = {
                      "type": "BigImage",
                      "image_id": "1652229/bdbc730d9af3bfe5d76d",
                      "title": "↓↓↓",
                      "description": recipe_list
                    }
            response["response"]["card"] = img

        else:
            if re.search(r'lf|да|ага|угу|хор|ок|подтверж',r.original_utterance.lower()):

                #если да, то добавляем в список товары из рецепта
                for item in recipe["products"]:
                    db.add_yandex_list_product(user["active_list"], item)

                next_stage()

            elif re.search(r'yt|не|отмена|отбой',r.original_utterance.lower()):

                next_stage()

            else:
                mess = "Не совсем поняла, добавляем в список недостающие продукты, чтобы приготовить "+ recipe["name"] +" ?"



    #если стадия 3.0, значит на нужно выяснить номер телефона пользователя и адрес
    if user["id_stage"] == 30:


        #если уже город и улица заполнены, а номер дома нет, то ждем от пользователя эту информацию
        if user["city"] and user["street"] and not(user["house_number"]):
            if re.search(r'[\d -\/.]|(д|эт|к|кор|под|пер|пр)', r.command):
                r.house_number = r.command

        #ждем что пользователь прислал нужную нам инфу и сразу добавляем данные в БД
        db.update_yandex_user(r.user_id, city = r.city,street = r.street, house_number = r.house_number, user_phone = r.user_phone)

        #обновим информацию о пользователе
        user = db.yandex_user_exists(r.user_id)

        #теперь недостающую инфу дозапрашиваем
        if not(user["city"]):
            mess = "Укажите, пожалуйста, адрес доставки, например: Кранодар, улица Солнечная дом 15 квартира 50 этаж 1"  #если даже города нет, то считаем, что ранее информацию не запрашивали
        elif not(user["street"]):
            mess = "Укажите улицу"
        elif not(user["house_number"]) and not(r.street):
            mess = "Укажите номер дома, квартиру и этаж"
        elif not(user["phone"]):
            mess = "Укажите, контактный телефон для связи с вами"
        else:
            user["id_stage"] = 31
            #если все данные есть переводим пользователя далее, на стадию 31 (Расчет времени доставки)
            db.update_yandex_user(r.user_id, stage_code = user["id_stage"])



    if user["id_stage"] == 31:

        #вспомогательная функция для округления времени
        def rounder(t):
            if t.minute >= 30:
                return t.replace(second=0, microsecond=0, minute=0, hour=t.hour+1)
            else:
                return t.replace(second=0, microsecond=0, minute=0)

        mess = "Доставим сегодня примерно в " + str(rounder((datetime.now() + timedelta(hours=3))).strftime('%H:%M')) + ". Подтверждаете заказ?"

        #если есть экран выведем список на экран
        if r.has_screen == 1:
            #получаем наш список продуктов
            list_products = db.get_yandex_list(user["active_list"])
            mess =  list_products + "\n\n\n" + mess
            #присвоим стадию 4 - выбор стадии

        #переходим на стадию 32 (Подтверждение доставки)
        db.update_yandex_user(r.user_id, stage_code = 32)



    #если стадия 3.1, значит на нужно выяснить номер телефона пользователя и адрес
    if user["id_stage"] == 32:

        #вспомогательная функция в рамках этой стадии
        def next_stage():
            db.update_yandex_user(r.user_id, stage_code = 10) #присвоим стадию 10 - как будто все сначала
            db.update_yandex_list(user["active_list"], 0) #активный список делаем неактивным
            #response["response"]["end_session"] = True #закрываем соединение, чтобы при следующем обращении оно было как новое


        if re.search(r'lf|да|ага|угу|хор|ок|подтверж',r.original_utterance.lower()):
            mess = "Заказ подтвержден, ожидайте доставку."
            next_stage()


        elif re.search(r'yt|не|отмена|уу|отбой',r.original_utterance.lower()):
            mess = "Заказ отменен"
            next_stage()

        else:
            mess = "Не совсем поняла, подтверждаем заказ?"



    #все стадии, что начинаются на 4 - относятся отлько к списку
    if user["id_stage"] == 40:

        #logging.info("Список: " + str(list_products))

        #если есть экран, то выведем получившийся список на экран
        if r.has_screen == 1:
            list_products = db.get_yandex_list(user["active_list"]) #получаем наш список продуктов
            mess = "Продублировать список вам по СМС, Телеграм или вацап?"
            img = {
                      "type": "BigImage",
                      "image_id": "213044/74c83c1a5365983fa045",
                      "title": "список:",
                      "description": list_products
                    }
            response["response"]["card"] = img
        elif r.has_screen == 0:
            mess = "Список готов отправить его вам по СМС, в Телеграм или в Вацап?"


        #переходим на стадию 32 (Подтверждение доставки)
        db.update_yandex_user(r.user_id, stage_code = 41)



    if user["id_stage"] == 41:

        def set_button():
            button = [
                    {
                        "title": "Отправить в телеграм",
                        "payload": {},
                        "url": LINK_TO_TELEGRAM + "?iduserlocal="+ str(user["id_user_local"]),
                        "hide": True
                    }
                ]
            response["response"]["buttons"] = button

        if r.new_session:
            if r.has_screen == 1:
                list_products = db.get_yandex_list(user["active_list"]) #получаем наш список продуктов
                mess = "Привет, " + user["first_name"] + ", у вас готов список продуктов.\nПродублировать его по СМС, Телеграм или вацап?"
                img = {
                      "type": "BigImage",
                      "image_id": "213044/74c83c1a5365983fa045",
                      "title": "список:",
                      "description": list_products
                    }
                response["response"]["card"] = img

                #items = []

                #for item in list_products:
                #    v = {"image_id": "213044/74c83c1a5365983fa045",
                #         "title": item[0].lower()
                #    }
                #    items.append(v)


                #footer = {
                #    "type": "ItemsList",
                #    "items": items,
                #    "footer":{
                #        "text": "Подвал"
                #      }
                #    }
                #response["response"]["card"] = footer
            elif r.has_screen == 0:
                mess = "Привет, " + user["first_name"] + ", у вас готов список продуктов, отправить его вам по СМС, в Телеграм или в Вацап?"

        else:
            if re.search(r'смс|первое|сообщ|sms',r.original_utterance.lower()):
                mess = "Список отправлен по СМС"
            elif re.search(r'телег|второе',r.original_utterance.lower()):

                mess = "Список отправлен в телеграмм"

                list_products = db.get_yandex_list(user["active_list"])

                bot.send_message(user["id_chat_telegram"], "{0}".format(list_products))


            elif re.search(r'вацап|вотсапп|what|ватсап',r.original_utterance.lower()):
                mess = "Список отправлен в вацап"
            elif re.search(r'нет|не отп|не надо|no|отмена|не |никуда|никак',r.original_utterance.lower()):
                mess = "Хорошо, ищите список в этом чате или личном кабинете"


            #если после ветки выше мы так и не заполнии mess, то отправим дополнительный запрос
            if not(mess):
                mess = "Не поняла, отправить список вам по СМС, Телеграм или Вацап?"
                #set_button()
            else:
                discount = db.find_yandex_list_discont(user["active_list"])

                #если есть акционные товары сообщим об этом пользователю
                if discount:
                    if r.has_screen == 1:
                        mess = mess + "\n\nВнимание, в Магните сейчас акция:"
                        img = {
                          "type": "BigImage",
                          "image_id": "1521359/2933617ee01f80c6e5d0",
                          "title": discount,
                          "description": ""
                        }
                        response["response"]["card"] = img
                    else:
                        mess = mess + "\n\nВнимание, в Магните сейчас акция:" + discount


                db.update_yandex_user(r.user_id, stage_code = 10)
                db.update_yandex_list(user["active_list"], 0) #активный список делаем неактивным
                #response["response"]["end_session"] = True #закрываем соединение, чтобы при следующем обращении оно было как новое



    db.yandex_log(user["id_user_local"], mess, r.original_utterance)
    response["response"]["text"] = mess

    return json.dumps(response)



@app.route('/telegrambot',methods=['POST','GET'])
def index():
    if(request.method == 'POST'):
        req_result = request.get_json()

        r = ParserRequestFromTelegram(req_result)
        logging.info("JSON_TELEGRAM: " + str(request.json))

        if r.json_type == 'message':

            if r.message_text == '/start':

                #добавляем пользователя к нам в БД
                db.add_subscriber(r.user_id, r.first_name, r.last_name, r.user_name, r.chat_id, r.chat_type, r.chat_title)

                #отправим приветственное сообщение
                bot.send_message(r.chat_id, "Привет, {0}! Могу помочь осуществить покупку".format(r.first_name))

            else:

                bot.send_message(r.chat_id, "Функционал в разработке")




        return jsonify(req_result)




if __name__ == '__main__':
    app.run()
