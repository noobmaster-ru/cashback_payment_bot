import logging
import asyncio

from aiogram import F
from aiogram.types import CallbackQuery, URLInputFile
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from redis.asyncio import Redis

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
    superbanking: Superbanking,
    redis_client: Redis,
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
    except Exception:
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
    if bank_id is None:
        text = "Не удалось определить банк, введите реквизиты заново."
        await callback.message.answer(
            text=StringConverter.escape_markdown_v2(text),
            parse_mode="MarkdownV2"
        )
        await state.set_state(States.waiting_for_phone_number)
        return

    balance = await asyncio.to_thread(superbanking.post_api_balance)

    text = (
        f"Баланс счёта: *{balance}₽*"
    )
    await callback.message.answer(
        text=StringConverter.escape_markdown_v2(text),
        parse_mode="MarkdownV2"
    )

    if balance < 0:
        text = (
            "Не удалось проверить баланс счёта, выплата остановлена. "
            "Повторите попытку через несколько секунд."
        )
        await callback.message.answer(
            text=StringConverter.escape_markdown_v2(text),
            parse_mode="MarkdownV2"
        )
        await state.set_state(States.waiting_for_phone_number)
        return

    if balance < constants.BALANCE_LIMIT_EXECUTION:
        text = (
            f"Баланс *{balance}₽* ниже лимита *{constants.BALANCE_LIMIT_EXECUTION}₽*, "
            "выплата не выполнена."
        )
        await callback.message.answer(
            text=StringConverter.escape_markdown_v2(text),
            parse_mode="MarkdownV2"
        )
        await state.set_state(States.waiting_for_phone_number)
        return

    order_number = await superbanking.get_next_order_number(redis_client=redis_client)
    payment_status_code, _ = await asyncio.to_thread(
        superbanking.post_create_and_sign_payment,
        phone=phone_formated,
        bank_identifier=bank_id,
        amount=amount,
        order_number=order_number,
    )
    
    if payment_status_code != 200:
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
        f"Выплата *{order_number}*:\n\nТелефон: {phone_number}\nБанк: {bank}\nСумма: {amount}\n\n"
        "произведена *успешно* давайте оформим следующую.\n\n"
        "Напишите номер телефона"
    )
    msg = await callback.message.answer(
        text=StringConverter.escape_markdown_v2(text),
        parse_mode="MarkdownV2"
    )

    await state.set_state(States.waiting_for_phone_number)
    

    await asyncio.sleep(constants.TIME_SLEEP)
    
    logger.info(f"orderNumber = {order_number}")
    
    check_photo_url = await asyncio.to_thread(
        superbanking.post_confirm_operation,
        order_number=order_number,
    )
    if check_photo_url[0] != 200 or check_photo_url[1] == "none":
        text = (
            f"Выплата *{order_number}* выполнена, но не удалось получить чек."
        )
        await callback.message.answer(
            text=StringConverter.escape_markdown_v2(text),
            parse_mode="MarkdownV2",
            reply_to_message_id=msg.message_id
        )
        return
    # text = (
    #     f"Чек по операции *{response_payment_status_code_and_order_number_tuple[1]}*:\n {check_photo_url[1]}\n"
    # )
    
    # await callback.message.answer(
    #     text=StringConverter.escape_markdown_v2(text),
    #     parse_mode="MarkdownV2",
    #     reply_to_message_id=msg.message_id
    # )
    
    # Создаем объект файла из ссылки
    pdf_file = URLInputFile(
        check_photo_url[1],
        filename="Чек.pdf"  # Укажите имя, с которым файл отобразится у юзера
    )
    text = (
        f"Чек *{order_number}*"
    )
    # Отправляем документ
    await callback.message.answer_document(
        document=pdf_file,
        caption=StringConverter.escape_markdown_v2(text),
        parse_mode="MarkdownV2",
        reply_to_message_id=msg.message_id # Если нужно ответить на текущее сообщение
    )
