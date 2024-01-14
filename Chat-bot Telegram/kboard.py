from typing import Optional
from aiogram.filters.callback_data import CallbackData

from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.filters import Command
#from data.text import action_dict, list_dict

from bot import db
from aiogram.enums import ParseMode
class NumbersCallbackFactory(CallbackData, prefix="d332da"):
    action: str
    value: Optional[int] = None

def createInlineKeyboardBuilder(action, lang) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    lines = db.get_buttons_list(action)
    for line in lines:
        if(action == "action1" or line != lines[len(lines) - 1]):
            id = line[6 : ]
            builder.button(text=db.get_button_name(id, lang), callback_data=line, parse_mode=ParseMode.HTML)
        else:
            builder.button(text="back", callback_data=line)
    builder.adjust(1)

    
    return builder.as_markup()


def create_inline_keyboard_builder_for_admins(texts, actions) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for i in range(len(texts)):
        builder.button(text=texts[i], callback_data=actions[i], parse_mode=ParseMode.HTML)
    builder.adjust(1)
    
    return builder.as_markup()

# def createInlineKeyboardBuilder( lines : [str], act: str=None) -> InlineKeyboardMarkup:
#     builder = InlineKeyboardBuilder()
#     idx = 0
#     for line in lines:
#         builder.button(text=line, callback_data=NumbersCallbackFactory(action=action_dict[line]))
#         idx += 1
#     builder.adjust(1)
#     return builder.as_markup()

def createReplyKeyboardBuilder(lines : [str]) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    for line in lines:
        builder.add(KeyboardButton(text=line))
    return builder.as_markup()

cancel_kboard =  createReplyKeyboardBuilder(["Отмена"])

# def setMenues():
#     for item in list_dict:
#         menu_dict[item] = createInlineKeyboardBuilder(list_dict[item])

# def getInlineKeyboardBuilder(name):
#     return menu_dict[name]

# setMenues()
