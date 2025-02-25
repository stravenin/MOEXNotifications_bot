from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.core.schemas import Notification

StartKeyboard = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Создать уведомление")],
    [KeyboardButton(text="Список уведомлений")],
], resize_keyboard=True,
input_field_placeholder="Выберите пункт меню",
one_time_keyboard=True)

def get_nts_inline(nts: list[Notification]):
    markup = InlineKeyboardBuilder()  # Создаём клавиатуру

    buttons = [
        InlineKeyboardButton(text=f"{nt.ticker}: {nt.target_price}₽", callback_data=f"nt_{str(nt.id)}")
        for nt in nts
    ]

    # Добавляем кнопки в строки по 3
    for i in range(0, len(buttons), 3):
        markup.row(*buttons[i:i+3])

    markup.row(InlineKeyboardButton(text="Назад", callback_data="Back_to_start"))

    return markup.as_markup()  # Возвращаем клавиатуру
def delete_nt_inline(nt: Notification):
    markup = InlineKeyboardBuilder() # создаём клавиатуру
    markup.row_width = 1 # кол-во кнопок в строке
    markup.add(InlineKeyboardButton(text=f"Удалить {nt.ticker}: {nt.target_price}₽", callback_data=f"del_{str(nt.id)}"))
    markup.add(InlineKeyboardButton(text="Назад", callback_data="Back_to_nts"))
    return markup.as_markup() #возвращаем клавиатуру