from aiogram.fsm.state import StatesGroup, State

class StatesForm(StatesGroup):
    writing_firstname = State()
    writing_lastname = State()
    writing_country = State()
    writing_birth_date = State()
    writing_mail = State()
    writing_phone = State()
    writing_old_counties_educations = State()
    loading_passport = State()
    loading_passport_translation = State()
    loading_visa_form = State()
    loading_bank_statement = State()
    select_person_access = State()
    loading_comments = State()

class StatesReductMsg(StatesGroup):
    reduct_msg = State()


class StatesReductBtn(StatesGroup):
    reduct_btn = State()

class StateAddBtn(StatesGroup):
    add_msg = State()
    add_btn = State()


class StateHundleApplication(StatesGroup):
    pass