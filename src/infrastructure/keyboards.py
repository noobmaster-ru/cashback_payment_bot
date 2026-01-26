from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# === Клавиатура Да / Нет ===
yes_no_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=f"✅ Да", callback_data=f"confirm_payment"),
            InlineKeyboardButton(text=f"❌ Нет", callback_data=f"no_confirm_payment")
        ]
    ])