from aiogram import F
from aiogram.types import CallbackQuery
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext


from src.infrastructure.states import States
from src.infrastructure.superbanking import Superbanking
from src.tools.string_converter import StringConverter

from .router import router

@router.callback_query(StateFilter(States.confirming_requisites), F.data == "no_confirm_payment")
async def no_confirm_payment(
    callback: CallbackQuery, 
    state: FSMContext
):
    """
    Пользователь указал, что реквизиты неверные — начинаем ввод заново.
    """
    await callback.answer()
    data = await state.get_data()
    
    # Удаленияем определенного ключа (например, 'username') из словаря Python
    if 'bank' in data:
        del data['bank']
    if 'amount' in data:
        del data['amount']
    if 'phone_number' in data:
        del data['phone_number']

    # Обновление данных в FSMContext
    await state.set_data(data)
    
    # ставим новое состояние
    text = (
        "❌ Хорошо, давайте попробуем ещё раз(по порядку запишем всё заново)\n"
        "Отправьте номер телефона/карты "
    )
    await callback.message.edit_text(
       text=StringConverter.escape_markdown_v2(text),
       parse_mode="MarkdownV2"
    )
    await state.set_state(States.waiting_for_phone_number)

@router.callback_query(StateFilter(States.confirming_requisites), F.data == "confirm_payment")
async def confirm_payment(
    callback: CallbackQuery, 
    state: FSMContext,
    superbanking: Superbanking
):
    await callback.answer()
    """
    Пользователь указал, что реквизиты верные — делаем выплату
    """

    data = await state.get_data()
    phone_number = data.get('phone_number', '-')
    bank = data.get('bank', '-')
    amount = data.get('amount', '-')

    
    amount = StringConverter.parse_amount(text=str(amount)) 
    phone_formated = StringConverter.convert_phone_to_superbanking_format(phone_number=phone_number)
    bank_id = superbanking.parse_bank_identifier(text=bank)
    response_status_code = superbanking.create_payment(
        phone=phone_formated,
        bank_identifier=bank_id,
        amount=amount
    )

    if response_status_code != 200:
        text = (
            f"У нас возникли некоторые проблемы при выплате , можете , пожалуйста , заново ввести номер телефона/карты"
        )
        await callback.message.answer(
            text=StringConverter.escape_markdown_v2(text),
            parse_mode="MarkdownV2"
        )
        await state.set_state(States.waiting_for_phone_number)
        return 
    
    try:
        msg_id_to_delete = data.get("msg_id_to_delete",'-')
        msg_chat_id_to_delete = data.get("msg_chat_id_to_delete",'-')
        await callback.bot.delete_message(
            chat_id=msg_chat_id_to_delete, 
            message_id=msg_id_to_delete
        )
    except:
        pass
    
    text = (
        "Выплата произведена, давайте оформим следующую.\n"
        "Напишите номер телефона\n"
    )
    await callback.message.answer(
        text=StringConverter.escape_markdown_v2(text),
        parse_mode="MarkdownV2"
    )

    await state.set_state(States.waiting_for_phone_number)