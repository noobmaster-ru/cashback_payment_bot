import logging
from aiogram import Bot
from aiogram.types import Message
from aiogram.filters import StateFilter, Command
from aiogram.fsm.context import FSMContext

from src.infrastructure.states import States
from src.tools.string_converter import StringConverter
from src.core.config import constants
from src.infrastructure.superbanking import Superbanking

from .router import router

@router.message(Command("balance"))
async def get_balance(
    message: Message,
    superbanking: Superbanking
):
    balance = superbanking.post_api_balance()
    text = (
        f"Баланс счёта: *{balance}₽*"
    )
    await message.answer(
        text=StringConverter.escape_markdown_v2(text),
        parse_mode="MarkdownV2"
    )
    
@router.message(StateFilter(None))
async def cmd_start(
    message: Message,
    state: FSMContext
):
    telegram_id = message.from_user.id
    if not telegram_id in constants.admins_ids:
        text = (
            "Пока"
        )
        await message.answer(
            text=StringConverter.escape_markdown_v2(text),
            parse_mode="MarkdownV2"
        )
        return
    
    username = message.from_user.username or "-"
    full_name = message.from_user.full_name or "-"
    msg_text = message.text or "-"

    logging.info(
        f"FIRST MESSAGE from (@{username}, {full_name}), id={telegram_id}: {msg_text} ..."
    )

    text = (
        "Здравствуйте!\n"
        "Я - бот для выплаты кэшбека\n\n"
        "Мне нужно:\n"
        "- номер телефона\n"
        "- название банка (например Т-банк, Сбер, Альфа)\n"
        "- сумма выплаты\n\n"
        "Отправьте номер телефона/карты"
    )
    await message.answer(
        text=StringConverter.escape_markdown_v2(text),
        parse_mode="MarkdownV2"
    )

    await state.set_state(States.waiting_for_phone_number)
