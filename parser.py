import re

class ParserRequestFromTelegram:
    def __init__(self, json_file):

        #если ответ содержит ключ message, то значит это сообщение от пользователя
        if json_file.get('message'):
            self.json_type = 'message'
            self.chat_id = json_file.get('message').get('chat').get('id',"")
            self.chat_type = json_file.get('message').get('chat').get('type',"")
            self.chat_title = json_file.get('message').get('chat').get('title',"")
            self.message_text = json_file.get('message').get('text',"")
            self.message_id = json_file.get('message').get('message_id',"")
            self.user_id = json_file.get('message').get('from').get('id',"")
            self.first_name = json_file.get('message').get('from').get('first_name',"")
            self.last_name = json_file.get('message').get('from').get('last_name',"")
            self.user_name = json_file.get('message').get('from').get('username',"")


        elif json_file.get('callback_query'):
            self.json_type = 'callback_query'
            self.chat_id = json_file.get('callback_query').get('from').get('id',"")
            self.callback_data = json_file.get('callback_query').get('data',"")
            self.message_id = json_file.get('callback_query').get('message').get('message_id',"")

class ParserRequestFromYandex:
    def __init__(self, json_file):

        self.version = json_file.get('version')
        self.session = json_file.get('session')
        self.user_id = self.session.get('user').get('user_id',"")
        self.application_id = json_file.get('session').get('application').get('application_id',"")
        self.new_session = json_file.get('session').get('new')
        self.original_utterance = json_file.get('request').get('original_utterance',"")
        self.command = json_file.get('request').get('command',"")
        self.tokens = json_file['request']['nlu']['tokens']

        self.has_screen = json_file["meta"]["interfaces"].get("screen") #имеет ли интерфейс пользователя экран?


        if self.has_screen is None:
            self.has_screen = 0 #есть экран
        else:
            self.has_screen = 1 #нет экрана

        #ищем имя, фамилию отчество, адрес
        self.first_name = ""
        self.last_name = ""
        self.patronymic_name = ""
        self.city = ""
        self.street = ""
        self.house_number = ""
        self.user_phone = ""

        for item in json_file['request']['nlu']['entities']:
            if item['type'] in ['YANDEX.FIO']:
                self.first_name = item.get('value').get('first_name',"")
                self.last_name = item.get('value').get('last_name',"")
                self.patronymic_name = item.get('value').get('patronymic_name',"")
            if item['type'] in ['YANDEX.GEO']:
                self.city = item.get('value').get('city',"")
                self.street = item.get('value').get('street',"")
                self.house_number = item.get('value').get('house_number',"")

        #ищем номер телефона
        #удаляем все пробелы и - , если есть
        phone_num = re.sub(r'[-\(\)\+]','',self.command.replace(' ',''))

        #в номере должно быть 11 цифр
        if re.search(r'^[78]\d{10}$', phone_num):
            self.user_phone = re.sub(r'^7', '8', phone_num) #заменяем первую 7 на 8






