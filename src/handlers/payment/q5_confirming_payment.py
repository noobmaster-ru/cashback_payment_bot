import time
import logging
import asyncio
from aiogram import F
from aiogram.types import CallbackQuery, URLInputFile
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from concurrent.futures import ThreadPoolExecutor

from src.infrastructure.states import States
from src.infrastructure.superbanking import Superbanking
from src.tools.string_converter import StringConverter
from src.core.config import constants

from .router import router

logger = logging.getLogger(__name__)

@router.callback_query(StateFilter(States.confirming_requisites), F.data == "no_confirm_payment")
async def no_confirm_payment(
    callback: CallbackQuery, 
    state: FSMContext
):
    """
    Пользователь указал, что реквизиты неверные — начинаем ввод заново.
    """

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
        "Отправьте номер телефона"
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
        f"🧑‍💻Выполняю выплату, подождите 10 секунд"
    )
    await callback.message.answer(
        text=StringConverter.escape_markdown_v2(text),
        parse_mode="MarkdownV2"
    )
    phone_number = data.get('phone_number', '-')
    bank = data.get('bank', '-')
    amount = data.get('amount', '-')

    
    amount = StringConverter.parse_amount(text=str(amount)) 
    phone_formated = StringConverter.convert_phone_to_superbanking_format(phone_number=phone_number)
    bank_id = superbanking.parse_bank_identifier(text=bank)
    
    # Создаем пул потоков (2 потока для двух задач)
    with ThreadPoolExecutor(max_workers=2) as executor:
        # Отправляем задачи на выполнение
        future_payment = executor.submit(
            superbanking.post_create_and_sign_payment, 
            phone=phone_formated, 
            bank_identifier=bank_id, 
            amount=amount
        )
        future_balance = executor.submit(superbanking.post_api_balance)

        # Получаем результаты (код подождет завершения обоих запросов здесь)
        response_payment_status_code_and_order_number_tuple = future_payment.result()
        balance = future_balance.result()

    text = (
        f"Баланс счёта: *{balance}₽*"
    )
    await callback.message.answer(
        text=StringConverter.escape_markdown_v2(text),
        parse_mode="MarkdownV2"
    )
    
    if response_payment_status_code_and_order_number_tuple[0] != 200:
        text = (
            f"У нас возникли некоторые проблемы при выплате , можете , пожалуйста , заново ввести номер телефона"
        )
        await callback.message.answer(
            text=StringConverter.escape_markdown_v2(text),
            parse_mode="MarkdownV2"
        )
        await state.set_state(States.waiting_for_phone_number)
        return 

    text = (
        f"Выплата *{response_payment_status_code_and_order_number_tuple[1]}* произведена успешно\n"
        "Давайте оформим следующую.\n\n"
        "Напишите номер телефона"
    )
    msg = await callback.message.answer(
        text=StringConverter.escape_markdown_v2(text),
        parse_mode="MarkdownV2"
    )

    await state.set_state(States.waiting_for_phone_number)
    
    
    await asyncio.sleep(constants.TIME_SLEEP)
    
    logger.info(f"orderNumber = {response_payment_status_code_and_order_number_tuple[1]}")
    
    check_photo_url = superbanking.post_confirm_operation(
        order_number=response_payment_status_code_and_order_number_tuple[1]
    )
    text = (
        f"Чек по операции *{response_payment_status_code_and_order_number_tuple[1]}*: {check_photo_url[1]}\n"
    )
    
    document = URLInputFile(
        check_photo_url[1], 
        filename="чек.pdf"  # Важно указать имя с .pdf
    )
    await msg.reply_document(
        document=document,
        caption=StringConverter.escape_markdown_v2(text),
        parse_mode="MarkdownV2"
    )