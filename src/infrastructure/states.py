from aiogram.fsm.state import StatesGroup, State

class States(StatesGroup):
    waiting_for_phone_number = State()
    waiting_for_bank = State()
    waiting_for_amount = State()
    confirming_requisites = State()
    
    
    continue_dialog = State()