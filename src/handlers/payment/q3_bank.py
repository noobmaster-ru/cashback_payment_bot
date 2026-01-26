import re
from aiogram.types import Message
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext


from src.infrastructure.states import States
from src.tools.string_converter import StringConverter
from src.core.config import constants

from .router import router


@router.message(StateFilter(States.waiting_for_bank))
async def handle_bank_name(
    message: Message, 
    state: FSMContext
):
    text = message.text.strip()

    bank_match = re.search(constants.bank_pattern, text, flags=re.IGNORECASE)
    bank = bank_match.group(0).capitalize() if bank_match else None
    await state.update_data(bank=bank)

    data = await state.get_data()
    text = (
        f"📩 Получены реквизиты:\n"
        f"Номер телефона: `{data.get('phone_number', '-')}`\n"
        f"Банк: {bank}\n\n"
        f"Теперь напишите *сумму* выплаты"
    )
    await message.answer(
        text=StringConverter.escape_markdown_v2(text),
        parse_mode="MarkdownV2"
    )
    await state.set_state(States.waiting_for_amount)
    return