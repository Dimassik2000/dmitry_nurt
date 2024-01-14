# import json

# def getDataFromJson(file: str) -> {}:
#     with open(file, "r") as f_in:
#         result = json.load(f_in)
#     return result

# def addJsonListDict():
#     data_FAQ = getDataFromJson("data/FAQ.json")
#     sectionNames = []
#     #for element in data_FAQ:
#         #sectionName = element['section']
#         #sectionNames.append(sectionName)
#         #action_dict[sectionName] = 'question'
#     for element in data_FAQ[0]['expression']:
#         sectionName = element['answer']
#         sectionNames.append(sectionName)
#         action_dict[sectionName] = 'question'
#         message_dict['FAQ'] = sectionName
#     list_dict['FAQ'] = sectionNames



# action_dict = {'Apply for trining': 'education_apply', 'Information adout education': 'education_info', 'Help section': 'help_section', 'Navigation': 'navigation', \
#         "Submit documents for training": "submit_documents",\
#     "Required documents":"required_documents",\
#     "Reception calendar": "reception_calendar",\
#            "Programs and Сourses": "education_programs",\
#     "Tuition fees": "tuition_fees", \
#     "Frequently Asked Questions": "FAQ",\
#     "Contact support": "contact_support",\
#     "Useful tips": "useful_tips",\
#     "First steps in Ekaterinburg": "education_apply_start",\
#     "Cabinet search": "cabinet_search"
#         }

# list_dict ={'bot_start': ['Apply for trining', 'Information adout education', 'Help section', 'Navigation'],\
#     'education_apply': ["Submit documents for training", "Required documents", "Reception calendar"],\
#     'education_info': ["Programs and Сourses", "Tuition fees"],\
#     'help_section': [    "Frequently Asked Questions", "Contact support", "Useful tips"],\
#     'navigation': ["First steps in Ekaterinburg", "Cabinet search"]
#     }
# message_dict={
#     'bot_start': 'bot_start',\
#     'education_apply': 'education_apply',\
#     'education_info': 'education_info',\
#     'help_section': 'help_section',\
#     'navigation': 'navigation',
#     'FAQ': 'Select intereted section'
# }

# addJsonListDict()
import pandas as pd
import numpy as np

def getDataFromXlsx(address: str, sheet: str)-> dict:
    data = pd.read_excel(address).to_dict()
    for key in data.keys():
        column = dict()
        for row_num in data[key].keys():
            elem = data[key][row_num]
            if(pd.isnull(data[key][row_num])):
                data[key] = column
                break
            else:
                column[row_num] = data[key][row_num]


    print(data)


def getDataFromXlsx2(address: str, sheet: str)-> dict:
    data = pd.read_excel(address).to_numpy()


    print(data)



#buttons = getDataFromXlsx('data/excel_tables/buttons.xlsx', 'Sheet1')
menus = getDataFromXlsx2('data/excel_tables/menus.xlsx', 'Sheet1')