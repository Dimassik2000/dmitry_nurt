#import mysql.connector as connector
import asyncio
import logging
from config import user, password, host, database
from datetime import datetime
#from data.text import getDataFromXlxs, getDataFromXlxs, action_dict, list_dict, message_dict
import numpy as np
import pandas as pd

import pymysql


class Database:
    def __init__(self):
        self.connection = pymysql.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            cursorclass=pymysql.cursors.DictCursor
        )
        with self.connection.cursor() as cursor:
            cursor.execute("""CREATE TABLE IF NOT EXISTS 
            menus(id INT AUTO_INCREMENT PRIMARY KEY, message TEXT, 
            button_name VARCHAR(150), message_ru TEXT, button_name_ru VARCHAR(150), 
            message_fr TEXT, button_name_fr VARCHAR(150), 
            message_ar TEXT, button_name_ar VARCHAR(150), 
            message_ch TEXT, button_name_ch VARCHAR(150));""")
            cursor.execute("""CREATE TABLE IF NOT EXISTS buttons_lists(id INT AUTO_INCREMENT PRIMARY KEY);""")
            cursor.execute("""CREATE TABLE IF NOT EXISTS users(id INT PRIMARY KEY, 
            language ENUM('ru', 'en', 'fr', 'ch', 'ar'), is_admin BOOL);""")
            cursor.execute("""CREATE TABLE IF NOT EXISTS forms(form_id INT AUTO_INCREMENT PRIMARY KEY, 
            user_id INT, firstname VARCHAR(50), lastname VARCHAR(50), country VARCHAR(50), 
            birth_date DATE, mail VARCHAR(256), phone VARCHAR(32), before_study_country VARCHAR(50), 
            passport VARCHAR(20), passport_tranlation VARCHAR(20), application_form VARCHAR(20), 
            bank_statment VARCHAR(20), yourself_applying BOOL, comments TEXT, 
            apply_date DATETIME, is_reviewed BOOL, FOREIGN KEY (user_id) REFERENCES users (id));""")
            self.connection.commit()
    
    #users

    def add_user(self, id, lang = 'en', is_admin = False):
        with self.connection.cursor() as cursor:
            cursor.execute(f"""INSERT INTO users(id, language, is_admin) VALUES ({id}, '{lang}', {is_admin});""")
            self.connection.commit()

    def check_user(self, id: int)-> bool:
        with self.connection.cursor() as cursor:
            cursor.execute(f"""SELECT id FROM users WHERE id = {id};""")
            is_exists = cursor.fetchall()
            return bool(len(is_exists))

    def check_admin(self, id: int)-> bool:
        with self.connection.cursor() as cursor:
            cursor.execute(f"""SELECT is_admin FROM users WHERE id = {id};""")
            is_admin = cursor.fetchall()
            return bool((is_admin[0]['is_admin']))


    def get_lang(self, id):
        with self.connection.cursor() as cursor:
            cursor.execute(f"""SELECT language FROM users WHERE id = {id};""")
            return cursor.fetchall()[0]['language']
    
    def update_lang(self, id, lang = 'en'):
        with self.connection.cursor() as cursor:
            cursor.execute(f"""UPDATE users SET language = '{lang}' WHERE id = {id};""")
            self.connection.commit()

    def del_user(self, id):
        with self.connection.cursor() as cursor:
            cursor.execute(f"""DELETE FROM users WHERE id = {id};""")
            self.connection.commit()
    
    def del_all_users(self):
        with self.connection.cursor() as cursor:
            cursor.execute(f"""DELETE FROM users WHERE is_admin = {False};""")
            self.connection.commit()

    def get_all_users(self):
        with self.connection.cursor() as cursor:
            cursor.execute("""SELECT * FROM users;""")
            return cursor.fetchall()

    #buttons_lists
    def set_start_data_buttons_list(self):
        data = pd.read_excel('data/excel_tables/buttons.xlsx').to_dict()
        for key in data.keys():
            column = dict()
            for row_num in data[key].keys():
                elem = data[key][row_num]
                if(pd.isnull(data[key][row_num])):
                    data[key] = column
                    break
                else:
                    column[row_num] = data[key][row_num]
        with self.connection.cursor() as cursor:
            for i in range(12):
                cursor.execute(f"""INSERT INTO buttons_lists() VALUES();""")
            self.connection.commit()  
            for key in data.keys():
                cursor.execute(f"""ALTER TABLE buttons_lists ADD {key} VARCHAR(15) NULL;;""")
            self.connection.commit() 
            for key in data.keys():
                for i in range(1, len(data[key]) + 1):
                    cursor.execute(f"""UPDATE buttons_lists SET {key} = '{data[key][i - 1]}' WHERE id = {i};""")
            self.connection.commit()       

    def get_buttons_list(self, action):
        with self.connection.cursor() as cursor:
            cursor.execute(f"""SELECT {action} FROM buttons_lists;""")
            message = cursor.fetchall()
            return list(filter(lambda x: x is not None,list(map(lambda x: list(x.values())[0],message))))

    def add_buttons_list(self, id, child_actions, parent_action):
        with self.connection.cursor() as cursor:
            parent_list = self.get_buttons_list(parent_action)
            cursor.execute(f"""UPDATE buttons_lists SET {parent_action} = '{parent_list[len(parent_list) - 1]}' WHERE id = {len(parent_list) + 1};""")
            cursor.execute(f"""UPDATE buttons_lists SET {parent_action} = 'action{id}' WHERE id = {len(parent_list)};""")
            cursor.execute(f"""ALTER TABLE buttons_lists ADD action{id} VARCHAR(15) NULL;""")
            for i in range(1, len(child_actions) + 1):
                cursor.execute(f"""UPDATE buttons_lists SET action{id} = '{child_actions[i - 1]}' WHERE id = {i};""")
            cursor.execute(f"""UPDATE buttons_lists SET action{id} = '{parent_action}' WHERE id = {len(child_actions) + 1};""")
            self.connection.commit()  
            return True

    def del_button(self, action):
        with self.connection.cursor() as cursor:
            buttons_list = self.get_buttons_list(action)
            parent_action = buttons_list[len(buttons_list) - 1]
            cursor.execute(f"""ALTER TABLE buttons_lists DROP COLUMN {action}; """)
            parent_butons_list = self.get_buttons_list(parent_action)
            shift_start = False
            for i in range(1, len(parent_butons_list)):
                if(not shift_start):
                    if(parent_butons_list[i - 1] == action):
                        shift_start = True
                    else:
                        continue
                cursor.execute(f"""UPDATE buttons_lists SET {parent_action} = '{parent_butons_list[i]}' WHERE id = {i};""")

            cursor.execute(f"""UPDATE buttons_lists SET {parent_action} = NULL WHERE id = {len(parent_butons_list)};""")

            self.connection.commit()  
            

    #menus

    def set_start_data_menus(self):
        menus = pd.read_excel('data/excel_tables/menus.xlsx').to_numpy()
        with self.connection.cursor() as cursor:
            for elems in menus:
                query = """
    INSERT INTO menus (id, message, button_name, message_ru, button_name_ru, message_fr, button_name_fr, message_ar, button_name_ar, message_ch, button_name_ch) 
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
""" 

                values = (
                int(elems[0][6:]),
                elems[1],
                elems[2],
                elems[3],
                elems[4],
                elems[5],
                elems[6],
                elems[7],
                elems[8],
                elems[9],
                elems[10]
                )   

                cursor.execute(query, values)
                # cursor.execute("""INSERT INTO menus(id, message, button_name, message_ru, button_name_ru, message_fr, button_name_fr, message_ar, button_name_ar, message_ch, button_name_ch) 
                # VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);""",(int(elems[0][6:]), elems[1], elems[2], elems[3], elems[4], elems[5], elems[6], elems[7], elems[8], elems[9], elems[10]))
                # #VALUES(?, ?, ?, ?, ? );""", (elems[0], elems[1], elems[2], elems[3], elems[4]))
            self.connection.commit()   

    def add_new_action_describtion(self, descriptions)-> int:
        with self.connection.cursor() as cursor:
            cursor.execute(f"""INSERT INTO menus(message, button_name, message_ru, button_name_ru) 
            VALUES('{descriptions[0]}', '{descriptions[1]}', '{descriptions[2]}', '{descriptions[3]}');""")
            self.connection.commit() 
            cursor.execute(f"""SELECT LAST_INSERT_ID();""")
            id = cursor.fetchall()
            return int(id[0]['LAST_INSERT_ID()'])         


    def get_message(self, id, lang = "en"):
        with self.connection.cursor() as cursor:
            if(lang == "en"):
                cursor.execute(f"""SELECT message FROM menus WHERE id='{id}';""")
            else:
                cursor.execute(f"""SELECT message{"_" + lang} FROM menus WHERE id='{id}';""")
            message = cursor.fetchall()
            return str(list(message[0].values())[0])

    def get_button_name(self, id, lang = "en"):
        with self.connection.cursor() as cursor:
            if(lang == "en"):
                cursor.execute(f"""SELECT button_name FROM menus WHERE id='{id}';""")
            else:
                cursor.execute(f"""SELECT button_name{"_" + lang} FROM menus WHERE id='{id}';""")
            button_name = cursor.fetchall()
            return str(list(button_name[0].values())[0])

    def update_message(self, id, msg, lang = "en"):
        with self.connection.cursor() as cursor:
            if(lang == "en"):
                cursor.execute(f"""UPDATE menus SET message = '{msg}' WHERE id='{id}';""")
            else:
                cursor.execute(f"""UPDATE menus SET message{"_" + lang} = '{msg}' WHERE id='{id}';""")
            self.connection.commit()  

    def update_button_name(self, id, button_name, lang = "en"):
        with self.connection.cursor() as cursor:
            if(lang == "en"):
                cursor.execute(f"""UPDATE menus SET button_name = '{button_name}' WHERE id='{id}';""")
            else:
                cursor.execute(f"""UPDATE menus SET button_name{"_" + lang} = '{button_name}' WHERE id='{id}';""")
            self.connection.commit()  

    



    #forms
    def add_new_form(self, user_id, firstname, lastname, country, birth_date, mail, phone, before_study_country, passport, passport_tranlation, application_form, bank_statment, yourself_applying, comments):
        with self.connection.cursor() as cursor:
            apply_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.cursor.execute(f"""INSERT INTO forms(user_id, firstname, lastname, country, birth_date, mail, phone, 
            before_study_country, passport, passport_tranlation, application_form, bank_statment, 
            yourself_applying, comments, apply_date) VALUES({user_id}, {firstname}, {lastname}, {country}, {birth_date}, 
            {mail}, {phone}, {before_study_country}, {passport}, 
            {passport_tranlation}, {application_form}, {bank_statment}, {yourself_applying}, {comments}, {apply_date});""")             
            self.connection.commit()
    
    
    def get_all_forms(self):
        with self.connection.cursor() as cursor:
            self.cursor.execute(f"""SELECT form_id FROM forms;""")             
            message = cursor.fetchall()
            return str(list(message[0].values())[0])     

    def get_elem_by_id(self, elem, form_id):
        with self.connection.cursor() as cursor:
            self.cursor.execute(f"""SELECT {elem} FROM forms WHERE form_id = {form_id};""")             
            message = cursor.fetchall()
            return str(list(message[0].values())[0])      

    def add_new_form_by_id(self, user_id):
        with self.connection.cursor() as cursor:
            self.cursor.execute(f"""INSERT INTO forms(user_id) VALUES({user_id});""")             
            self.connection.commit()

    def add_elem_by_id(self, elem, value, form_id):
        with self.connection.cursor() as cursor:
            self.cursor.execute(f"""UPDATE forms SET {elem} = '{value}';""")             
            self.connection.commit()   

    

    


    





    
#     def __del__(self):
# #         self.connection.close()
# #
# #
# #
# #
# # Db = Database()
#Db.add_buttons_list(Db.add_new_action_describtion(["dsfsd", "dsfsd", "dsfsdf", "sdfdsfs"]), [], "action1")

#print(Db.get_buttons_list("action1"))
# Db.del_all_users()
# for i in range(0, 50):
#     Db.add_user(i)

# Db.add_user(100, 'ru')
# a = Db.get_all_users()
# for g in a:
#     print(g)

# g = Db.check_user(200)

# print(g)
# # for i in range(1,5):
#     print(Db.get_message(i))
#     print(Db.get_button_name(i))

#Db.set_start_data_buttons_list()
#Db.set_start_data_menus()

# class Database:
#     def __init__(self):
#         try:
#             self.conn = connector.connect(user=user, password=password, host=host, database=database)
#             self.cursor = self.conn.cursor()
#             #self.cursor.execute("Drop table forms;DROP TABLE menus;Drop table users;Drop table buttons;")
#             self.cursor.execute('CREATE TABLE IF NOT EXISTS menus(id INT AUTO_INCREMENT PRIMARY KEY, message TEXT, button_name VARCHAR(150), action VARCHAR(10) NOT NULL);')
#             self.cursor.execute('CREATE TABLE IF NOT EXISTS buttons(id VARCHAR(10), b0 VARCHAR(10), b1 VARCHAR(10), b2 VARCHAR(10), b3 VARCHAR(10), b4 VARCHAR(10), b5 VARCHAR(10), b6 VARCHAR(10), b7 VARCHAR(10),  b8 VARCHAR(10),  b9 VARCHAR(10), b10 VARCHAR(10), b11 VARCHAR(10), b12 VARCHAR(10), b13 VARCHAR(10), b14 VARCHAR(10), b15 VARCHAR(10));')
#             self.cursor.execute("CREATE TABLE IF NOT EXISTS users(id INT AUTO_INCREMENT PRIMARY KEY, language ENUM('ru', 'en', 'fr', 'ch', 'ar'));")
#             self.cursor.execute("CREATE TABLE IF NOT EXISTS forms(form_id INT AUTO_INCREMENT PRIMARY KEY,user_id INT, firstname VARCHAR(50), lastname VARCHAR(50), country VARCHAR(50), birth_date DATE, mail VARCHAR(256), phone VARCHAR(32), before_study_country VARCHAR(50), passport VARCHAR(20), passport_tranlation VARCHAR(20), application_form VARCHAR(20), bank_statment VARCHAR(20), yourself_applying BOOL, comments TEXT, apply_date DATETIME, FOREIGN KEY (user_id) REFERENCES users (id));")
#             self.conn.commit()
#         finally:
#             self.conn.close()
        
#     def add_form(self, user_id, firstname, lastname, country, birth_date, mail, phone, before_study_country, passport, passport_tranlation, application_form, bank_statment, yourself_applying, comments)-> bool:
#         try:
#             self.conn.connect()
#             self.cursor = self.conn.cursor()
#             apply_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#             self.cursor.execute(f"INSERT INTO forms(user_id, firstname, lastname, country, birth_date, mail, phone, before_study_country, passport, passport_tranlation, application_form, bank_statment, yourself_applying, comments, apply_date) VALUES({user_id, firstname, lastname, country, birth_date, mail, phone, before_study_country, passport, passport_tranlation, application_form, bank_statment, yourself_applying, comments, apply_date});")
#             self.conn.commit()

#         except:
#             pass
#         finally:
#             self.conn.close()

#     def load_start_data(self):
#         try:
#             self.conn.connect()
#             self.cursor = self.conn.cursor()
#             menus = getDataFromXlxs('data/excel_tables/menus.xlsx', 'Sheet1')
#             buttons = getDataFromXlxs('data/excel_tables/buttons.xlsx', 'Sheet1')
#             for elems in menus:
#                 self.cursor.execute(f"INSERT INTO menus(message, button_name, action) VALUES('{elems[1]}', '{elems[2]}', '{elems[3]}');")
#             for buttons_list in buttons:
#                 val = f"'{buttons_list[0]}',"
#                 tags = 'id,'
#                 for i in range(1, len(buttons_list)):
#                     val += f"'{buttons_list[i]}',"
#                     tags += f'b{i - 1},'
#                 val = val[ : -1]
#                 tags = tags[ : -1]
#                 self.cursor.execute(f"INSERT INTO buttons({tags}) VALUES({val});")        
#             self.conn.commit()

#         finally:
#             self.conn.close()


#     def reload_main_data(self):
#         try:
#             self.conn.connect()
#             self.cursor = self.conn.cursor()
#             self.cursor.execute('SELECT action, button_name FROM menus;')
#             button_names = self.cursor.fetchall()
#             self.cursor.execute('SELECT action, message FROM menus;')
#             message = self.cursor.fetchall()
#             self.cursor.execute('SELECT * FROM buttons;')
#             buttons = self.cursor.fetchall()
        
#             for act in button_names:
#                 action_dict[act[0]] = act[1]

#             for act in message:
#                 message_dict[act[0]] = act[1]

#             for res in buttons:
#                 if('nan' in res ):
#                     end = res.index('nan')
#                 else:
#                     end = len(res)
#                 list_dict[res[0]] = res[1 : end]
#             self.conn.commit()
#         finally:
#             self.conn.close()

#     def cheak_user(self, id: int)-> bool:
#         try:
#             self.conn.connect()
#             result = self.cursor.execute(f'SELECT id FROM users WHERE id = {id};').fetchall()
#             return bool(len(result))
#         finally:
#             self.conn.close()
    
#     def add_user(self, id, lang = 'en'):
#         try:
#             self.conn.connect()
#             self.cursor.execute(f"INSERT INTO users(id, language) VALUES ({id},'{lang}');")
#         finally:
#             self.conn.commit()
#             self.conn.close()

#     def get_lang(self, id):
#         with self.conn:
#             return self.cursor.execute(f'SELECT language FROM users WHERE id = {id};').fetchall()
    
#     def update_lang(self, id, lang = 'en'):
#         with self.conn:
#             return self.cursor.execute(f'UPDATE users SET language = {lang} WHERE id = {id};')


#     def connect_db():
#         try:
#             conn = connector.connect(user=user, password=password, host=host, database=database)
#             conn.commit()
#         finally:
#             conn.close()
#         return conn


#     def create_tables():
#         try:
#             conn.connect()
#             cursor = conn.cursor()
#             cursor.execute('CREATE TABLE IF NOT EXISTS menus(id INT AUTO_INCREMENT PRIMARY KEY, message TEXT, button_name VARCHAR(150), action VARCHAR(10) NOT NULL, UNIQUE(action));')
#             cursor.execute('CREATE TABLE IF NOT EXISTS buttons(id VARCHAR(10), b0 VARCHAR(10), b1 VARCHAR(10), b2 VARCHAR(10), b3 VARCHAR(10), b4 VARCHAR(10), b5 VARCHAR(10), b6 VARCHAR(10), b7 VARCHAR(10),  b8 VARCHAR(10));')
#             cursor.execute("CREATE TABLE IF NOT EXISTS users(id INT AUTO_INCREMENT PRIMARY KEY, language ENUM('ru', 'en', 'fr', 'ch', 'ar'));")
#             cursor.execute("CREATE TABLE IF NOT EXISTS forms(form_id INT AUTO_INCREMENT PRIMARY KEY,user_id INT, firstname VARCHAR(50), lastname VARCHAR(50), country VARCHAR(50), birth_date DATE, mail VARCHAR(256), phone VARCHAR(16), before_study_country VARCHAR(50), passport VARCHAR(20), passport_tranlation VARCHAR(20), application_form VARCHAR(20), bank_statment VARCHAR(20), yourself_applying BOOL, comments TEXT, apply_date DATETIME, FOREIGN KEY (user_id) REFERENCES users (id));")
#             conn.commit()
#         finally:
#             conn.close()
    



#     def get_button_name(self, act):
#         try:
#             self.conn.connect()
#             self.cursor = self.conn.cursor()
#             self.cursor.execute(f"SELECT button_name FROM menus WHERE action='{act}';")
#             button_name = self.cursor.fetchall()
#             return str(button_name[0])[2:-3]
#         finally:
#             self.conn.close()
    

#     def get_message(self, act):
#         try:
#             self.conn.connect()
#             self.cursor = self.conn.cursor()
#             self.cursor.execute(f"SELECT message FROM menus WHERE action='{act}';")
#             message = self.cursor.fetchall()
#             return str(message[0])[2:-3]
#         finally:
#             self.conn.close()



#     def get_button_name1(self, act):
#         try:
#             self.conn.connect()
#             self.cursor = self.conn.cursor()
#             self.cursor.execute(f"SELECT button_name FROM menus WHERE action='{act}';")
#             button_name = self.cursor.fetchall()
#             return button_name
#         finally:
#             self.conn.close()

    


