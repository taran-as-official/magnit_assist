import pymysql
from datetime import datetime

class MySQL:

    def __init__(self):
        self.host = "taranasofficial.mysql.pythonanywhere-services.com"
        self.user = "taranasofficial"
        self.passwd = "1234qwer"
        self.db = "taranasofficial$taran_as_official_db"
        self.conn = None

    def open_connection(self):
        """Connect to MySQL Database."""
        try:
            if self.conn is None:
                self.conn = pymysql.connect(
                    self.host,
                    user=self.user,
                    passwd=self.passwd,
                    db=self.db
                )
        except pymysql.MySQLError as e:
            print('Ошибка при подключении в БД: '+ e)
        finally:
            print('Успешное подклчюение к БД')



    def run_query(self, query):
        """Execute SQL query."""
        try:
            self.open_connection()
            with self.conn.cursor() as cur:
                print("Выполнение запроса: " + query)
                cur.execute(query)
                result = cur.fetchall()
                self.conn.commit()
                cur.close()
                return result
        except pymysql.MySQLError as e:
            print('Ошибка при выполнении запроса ' + query + '\n' + str(e))
        finally:
            if self.conn:
                self.conn.close()
                self.conn = None
                print('Успешное отключение от БД')


    def add_subscriber(self, user_id, f_name, l_name, u_name, chat_id, chat_type, chat_title, status = 0):
        c_date = datetime.now()
        #Добавляем нового подписчика
        sql_query = """INSERT IGNORE INTO users
                       SET id_user     =  {0},
                           first_name  = '{1}',
                           last_name   = '{2}',
                           user_name   = '{3}',
                           create_date = '{4}'""".format(user_id,f_name,l_name,u_name,c_date)
        self.run_query(sql_query)

        #добавляем чат id
        sql_query = """INSERT IGNORE INTO users_chat
                       SET id_user     =  {0},
                           chat_id     =  {1},
                           chat_type   = '{2}',
                           create_date = '{3}',
                           chat_title  = '{4}'""".format(user_id, chat_id, chat_type, c_date, chat_title)
        self.run_query(sql_query)

        sql_query = """INSERT IGNORE INTO subscribe_users
                       SET id_user     =  {0},
                           id_status   =  {1},
                           create_date = '{2}'""".format(user_id,status,c_date)
        self.run_query(sql_query)

    def add_yandex_user(self, user_id, app_id):

        l_date = datetime.now()

        sql_query = """INSERT INTO `yandex_users_tbl`
                               SET `id_user`         = '{0}',
                                   `create_date`     = '{1}'""".format(user_id, l_date)
        self.run_query(sql_query)

        #добавляем связь пользователя и приложения
        sql_query = """INSERT INTO `yandex_users_reference_tbl` (`id_user_local`, `id_app_local`)
                        SELECT `id_user_local`, `id_app_local`
                          FROM `yandex_users_tbl` , `yandex_app_tbl`
                         WHERE `id_user` = '{0}'
                           AND `id_app`  = '{1}'""".format(user_id,app_id)
        self.run_query(sql_query)

        #добавляем связь пользователя и приложения
        #sql_query = """INSERT IGNORE INTO yandex_users_reference_tbl
        #               SET id_app_local      = '{0}',
        #                   id_user_local     = '{1}'""".format(app_id, user_id)
        #self.run_query(sql_query)


    def yandex_user_exists(self, user_id, app_id=""):
        #Проверяем есть ли уже юзер в базе
        sql_query = """select u.id_user
                             ,u.first_name
                             ,u.last_name
                             ,u.patronymic_name
                             ,u.id_user_local
                             ,u.id_stage
                             ,l.id_list
                             ,u.user_phone
                             ,l.is_order
                             ,u.city
                             ,u.street
                             ,u.house_number
                        from yandex_users_tbl u
                        left join yandex_list_tbl l on l.id_user_local = u.id_user_local
                                                   and l.active = 1
                       where id_user = '{0}'
                    """.format(user_id)

        userInf = self.run_query(sql_query)

        #если пользователя не существует у нас в БД, то добавим его
        if not(userInf):

            #добавим пользователя к нам в БД
            self.add_yandex_user(user_id, app_id)
            #снова запрашиваем инфу
            userInf = self.run_query(sql_query)




        #распарсим результат по пользователю из БД
        user = {
                    "id_user"   : userInf[0][0],
                    "first_name": userInf[0][1],
                    "id_user_local": userInf[0][4],
                    "id_stage"   : userInf[0][5],
                    "active_list": userInf[0][6], #активный список
                    "phone"      : userInf[0][7], #номер телефона
                    "is_list_order": userInf[0][8], #является ли список для заказа
                    "city":        userInf[0][9], #адрес пользователя
                    "street":        userInf[0][10], #адрес пользователя
                    "house_number":  userInf[0][11] #адрес пользователя
                }

        return user


    def update_yandex_user(self, user_id, first_name="", last_name="", patronymic_name="", user_phone ="",stage_code="",city="",street="",house_number="" ):



        #обновляем только те стобцы, в которые передано не пустое значение
        sql_query = """ UPDATE `yandex_users_tbl`
                           SET `first_name`      = if('{1}' = '', `first_name`, '{1}'),
                               `last_name`       = if('{2}' = '', `last_name`, '{2}'),
                               `patronymic_name` = if('{3}' = '', `patronymic_name`, '{3}'),
                               `user_phone`      = if('{4}' = '', `user_phone`, '{4}'),
                               `id_stage`        = if('{5}' = '', `id_stage`, '{5}'),
                               `city`            = if('{6}' = '', `city`, '{6}'),
                               `street`          = if('{7}' = '', `street`, '{7}'),
                               `house_number`    = if('{8}' = '', `house_number`, '{8}')
                         WHERE `id_user` = '{0}'""".format(user_id, first_name.title(), last_name.title(), patronymic_name.title(),user_phone, stage_code,city,street,house_number)
        self.run_query(sql_query)

    def add_yandex_list(self, id_user_local, is_list_order = 0):


        #создаем список
        sql_query = """INSERT INTO `yandex_list_tbl`
                               SET `id_user_local`  = '{0}',
                                   `is_order`       = '{1}'""".format(id_user_local, is_list_order)
        self.run_query(sql_query)

    def add_yandex_list_product(self, id_list, product_name):


        #добавляем продукт
        sql_query = """INSERT INTO `yandex_list_product_tbl`
                               SET `id_list`  = '{0}',
                                   `product`  = '{1}'""".format(id_list,product_name)
        self.run_query(sql_query)

    def update_yandex_list(self, id_list, active):


        #добавляем продукт
        sql_query = """UPDATE `yandex_list_tbl`
                          SET `active`  = '{1}'
                        WHERE `id_list` = '{0}'""".format(id_list, active)
        self.run_query(sql_query)

    def get_yandex_list(self, id_list = '', phone_num = "",is_order = 0):

        if phone_num:
            #выводим крайний составленный список
            sql_query = """select concat(rpad(p.product,20,' '),ifnull(concat(p2.price,'p.'),'')) prod
                              from yandex_list_product_tbl p
                              left join yandex_products_tbl p2 on lower(p2.product_name) = lower(p.product)
                              where p.id_list = (select l.id_list
                                                  from yandex_users_tbl u
                                                  join yandex_list_tbl l on u.id_user_local = l.id_user_local
                                                                        and l.is_order = '{1}'
                                                 where u.user_phone = '{0}'
                                                 order by l.create_date desc limit 1)
                            union all
                            select concat(rpad('ИТОГО:',19,' '),ifnull(concat('~',sum(p2.price),'p.'),'')) prod
                              from yandex_list_product_tbl p
                              left join yandex_products_tbl p2 on lower(p2.product_name) = lower(p.product)
                              where p.id_list = (select l.id_list
                                                  from yandex_users_tbl u
                                                  join yandex_list_tbl l on u.id_user_local = l.id_user_local
                                                                        and l.is_order = '{1}'
                                                 where u.user_phone = '{0}'
                                                 order by l.create_date desc limit 1);""".format(phone_num, is_order)

            result = self.run_query(sql_query)

            prod_list = []

            for item in result:
                prod_list.append(item[0])
            return prod_list
        else:
            #выводим активный список
            sql_query = """select concat(rpad(l.product,(70 - length(ifnull(concat(p.price,'p.'),0))),'.'),ifnull(concat(p.price,'p.'),'')) prod
                             from yandex_list_product_tbl l
                             left join yandex_products_tbl p on lower(p.product_name) = lower(l.product)
                            where l.id_list = '{0}'
                            union all
                            select concat(rpad('ИТОГО:',(67 - length(ifnull(concat(p.price,'p.'),0))),'.'),ifnull(concat('~',sum(p.price),'p.'),'')) prod
                              from yandex_list_product_tbl l
                              left join yandex_products_tbl p on lower(p.product_name) = lower(l.product)
                              where l.id_list = '{0}';""".format(id_list)

            result = self.run_query(sql_query)

            #формируем красивый список
            prod_list = ""

            for item in result:
                prod_list = prod_list + item[0].lower()

            return prod_list


    def find_yandex_list_discont (self, id_list):

        #выводим активный список
        sql_query = """select p.product_name, p.price, d.percent
                         from yandex_list_product_tbl l
                         join yandex_products_tbl p on lower(l.product) = lower(p.product_name)
                         join yandex_products_discount_tbl d on d.id_product = p.id_product
                        where l.id_list = {0}
                     order by l.create_date;""".format(id_list)

        result = self.run_query(sql_query)

        #формируем красивый список
        discount_list = ""

        for item in result:
            discount_list = discount_list + item[0] + ": " + str(item[1] - (item[1]/100*item[2])) + "р. вместо " + str(item[1]) + "р. скидка " + str(item[2]) + "% !!!\n"

        return discount_list

    #функция по поиску рецептов, возвращает недостающие ингридиенты
    def find_yandex_product_recipe (self, id_list):

        #выводим активный список
        sql_query = """select r.recipe_name, p.product_name
                         from yandex_recipe_structure_tbl s
                         join yandex_recipe_tbl r on r.id_recipe = s.id_recipe
                         join yandex_products_tbl p on p.id_product = s.id_product
                        where s.id_recipe in (select distinct s2.id_recipe
                                                from yandex_recipe_structure_tbl s2
                                                join yandex_products_tbl p2 on s2.id_product = p2.id_product
                                                join yandex_list_product_tbl l on lower(l.product) = lower(p2.product_name)
                                                where l.id_list = {0})
                        and s.id_product not in (select s.id_product
                                                   from yandex_list_product_tbl l
                                                   join yandex_products_tbl p on lower(l.product) = lower(p.product_name)
                                                   join yandex_recipe_structure_tbl s on s.id_product = p.id_product
                                                  where l.id_list = {0});""".format(id_list)

        result = self.run_query(sql_query)

        recipe = {}
        products = []

        if result:
            for item in result:
                products.append(item[1].lower())

            #формируем красивый список
            recipe = {"name": result[0][0],
                      "products": products
            }

        return recipe




    def yandex_log(self, id_user_loc, send_message, send_answer ):

        #сначала логируем, то что мы отправили и получили от пользователя
        sql_query = """INSERT INTO `yandex_users_dialog_log_tbl`
                            SET `id_user_local`      = '{0}',
                                `send_message`  = '{1}',
                                `send_answer`   = '{2}'""".format(id_user_loc, send_message, send_answer)
        self.run_query(sql_query)



    def close(self):
        #Закрываем соединение с БД
        self.connection.close()