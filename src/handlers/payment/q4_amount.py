import re
from aiogram.types import Message
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext


from src.infrastructure.states import States
from src.tools.string_converter import StringConverter
from src.infrastructure.keyboards import yes_no_keyboard
from src.core.config import constants


from .router import router

@router.message(StateFilter(States.waiting_for_amount))
async def handle_amount(
    message: Message, 
    state: FSMContext
):
    telegram_id = message.from_user.id
    if not telegram_id in constants.admins_ids:
        return
    text = message.text.strip()
    data = await state.get_data()

    amounts = re.findall(constants.amount_pattern, text, flags=re.IGNORECASE)
    amount = amounts[0] if amounts else None
    await state.update_data(
        amount=amount
    )

    text = (
        f"📩 Получены реквизиты:\n"
        f"Номер телефона: `{data.get('phone_number', '-')}`\n"
        f"Банк: {data.get('bank', '-')}\n"
        f"Сумма: `{amount}`\n\n"
        f"Реквизиты заполнены верно?"
    )
    msg = await message.answer(
        text=StringConverter.escape_markdown_v2(text),
        parse_mode="MarkdownV2",
        reply_markup=yes_no_keyboard
    )
    await state.set_state(States.confirming_requisites)
    await state.update_data(
        msg_id_to_delete=msg.message_id,
        msg_chat_id_to_delete=msg.chat.id
    )
    return
