from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

StartKeyboard = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Создать уведомление")],
    [KeyboardButton(text="Список уведомлений")],
], resize_keyboard=True,
input_field_placeholder="Выберите пункт меню",
one_time_keyboard=True)