localizations = {
    'ru': {
        'Hello': 'Hello_ru',\
           'bot_start': 'bot_start_ru',\
    'education_apply': 'education_apply_ru',\
    'education_info': 'education_info_ru',\
    'help_section': 'help_section_ru',\
    'navigation': 'navigation_ru',\
    'FAQ': 'Select intereted section_ru'
    }
}

def translate(text: str, lang: str ='en')-> str:
    if lang == 'ru':
        global localizations
        try:
            return localizations[lang][text]
        except:
            return text
    else:
        return text