import re
import logging

from aiogram.types import Message
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from src.infrastructure.states import States
from src.tools.string_converter import StringConverter
from src.core.config import constants

from .router import router

# --- Новый хэндлер для реквизитов: ---
@router.message(StateFilter(States.waiting_for_phone_number))
async def handle_phone_number(
    message: Message,
    state: FSMContext
):
    telegram_id = message.from_user.id
    if not telegram_id in constants.admins_ids:
        return
    text = message.text.strip()
    # --- Поиск данных ---
    phones = re.findall(constants.phone_pattern, text)

    # Запись в переменные (берём первое найденное или None)
    phone_number = phones[0] if phones else None


    # --- Сохраняем найденное в FSM ---
    await state.update_data(phone_number=phone_number)
    

    logging.info(f"  user: {telegram_id} gave requisites: phone_number = {phone_number}")


    text = (
        f"📩 Получены реквизиты:\n"
        f"Номер телефона: `{phone_number}`\n\n"
        f"Теперь напишите название банка"
    )
    await message.answer(
        text=StringConverter.escape_markdown_v2(text),
        parse_mode="MarkdownV2"
    )
    await state.set_state(States.waiting_for_bank)
    return