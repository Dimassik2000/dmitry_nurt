from aiogram import types, Bot
from aiogram.filters import BaseFilter
from typing import Union, Dict, Any
from bot import db

class IsAdminFilter(BaseFilter):
    async def __call__(self, callback: types.CallbackQuery) -> Union[bool, Dict[str, Any]]:
        user_id = callback.message.chat.id
        if(db.check_user(user_id)):
            return db.check_admin(user_id)
        else:
            return False