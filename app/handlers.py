from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram import html, Router, F
from aiogram.fsm.state import State, StatesGroup


from app.utils.keyboards import StartKeyboard, get_nts_inline, delete_nt_inline
from app.utils.middlewares import DepMiddleware
from app.services.notification_service import NotificationService

router = Router()

router.message.outer_middleware(DepMiddleware())
router.callback_query.outer_middleware(DepMiddleware())

class CreateNotification(StatesGroup):
    ticker = State()
    target_price = State()


@router.message(CommandStart())
async def command_start_handler(message: Message, nt_service: NotificationService) -> None:
    """
    This handler receives messages with `/start` command
    """
    await message.answer(f"Привет, {html.bold(message.from_user.full_name)}!\nВыбери команду.", reply_markup=StartKeyboard)


@router.message(F.text == "Создать уведомление")
async def create_notification_handler(message: Message, state: FSMContext, nt_service: NotificationService) -> None:
    await state.set_state(CreateNotification.ticker)
    await message.answer("Введите тикер акции, которая торгуется на мосбирже. Например: HEAD")

@router.message(CreateNotification.ticker)
async def ticker_handler(message: Message, state: FSMContext, nt_service: NotificationService) -> None:
    if not (0 < len(message.text) <= 4):
        await message.answer(
            f"Ошибка при вводе данных: длина тикера должна быть от 1 до 4 символов.",
            reply_markup=StartKeyboard)
        await state.clear()
        return None
    price = await nt_service.get_current_price_by_ticker(message.text.upper())
    if not price:
        await message.answer(
            f"Ошибка при вводе данных: акция с тикером: {message.text.upper()} не существует.",
            reply_markup=StartKeyboard)
        await state.clear()
        return None

    await state.update_data(ticker=message.text.upper())
    await state.set_state(CreateNotification.target_price)
    await message.answer(f"Введите целевую цену акции в рублях. Текущая: {price}₽")

@router.message(CreateNotification.target_price)
async def ticker_handler(message: Message, state: FSMContext, nt_service: NotificationService) -> None:
    try:
        target_price = message.text.replace(" ", "").replace(",", ".").replace("р", "").replace("₽", "")
        float(target_price)
    except Exception as e:
        await message.answer(
            f"Ошибка при вводе данных: введите цену в виде десятичной дроби, например 4500.5.",
            reply_markup=StartKeyboard)
        await state.clear()
        return None

    await state.update_data(target_price=message.text)
    data = await state.get_data()

    new_nt = await nt_service.add_notification(data, message.from_user.id)
    if not new_nt:
        await message.answer(
            f"Ошибка создания уведомления: Внутрення ошибка сервера.",
            reply_markup=StartKeyboard)
        await state.clear()
        return None

    await message.answer(f"Уведомление для {data["ticker"]} с целевой ценой: {data["target_price"]}₽ успешно создано. Изменение: {round(new_nt, 1)}%", reply_markup=StartKeyboard)
    await state.clear()

@router.message(F.text == "Список уведомлений")
async def get_notifications_handler(message: Message, nt_service: NotificationService) -> None:
    print(f"{message.from_user.id=}")
    nts = await nt_service.get_notifications_by_user_id(message.from_user.id)
    if not nts:
        await message.answer("У вас еще нет уведомлений", reply_markup=StartKeyboard)
        return None
    await message.answer("Список ваших уведомлений", reply_markup=get_nts_inline(nts))

@router.callback_query(F.data == "Back_to_nts")
async def back_to_nts_handler(call: CallbackQuery, nt_service: NotificationService) -> None:
    nts = await nt_service.get_notifications_by_user_id(call.from_user.id)
    await call.message.edit_text("Список ваших уведомлений", reply_markup=get_nts_inline(nts))

@router.callback_query(F.data == "Back_to_start")
async def back_start_handler(call: CallbackQuery) -> None:
    await call.message.delete()
    await call.message.answer(text="Выберите", reply_markup=StartKeyboard)

@router.callback_query(F.data.startswith("nt_"))
async def nt_id_handler(call: CallbackQuery, nt_service: NotificationService) -> None:
    nt_id = int(call.data.replace("nt_",""))
    nt = await nt_service.get_notification_by_id(nt_id)
    await call.message.edit_text("Нажмите на уведомление для удаления", reply_markup=delete_nt_inline(nt))

@router.callback_query(F.data.startswith("del_"))
async def nt_delete_handler(call: CallbackQuery, nt_service: NotificationService) -> None:
    nt_id = int(call.data.replace("del_",""))
    await nt_service.delete_notification_by_id(nt_id)
    nts = await nt_service.get_notifications_by_user_id(call.from_user.id)
    await call.message.edit_text("Список ваших уведомлений", reply_markup=get_nts_inline(nts))