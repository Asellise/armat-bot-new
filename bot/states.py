from aiogram.fsm.state import State, StatesGroup


class EnrollmentForm(StatesGroup):
    name = State()
    phone = State()
    direction = State()
    confirm = State()


class AdminBroadcast(StatesGroup):
    message = State()
    confirm = State()


class AdminScheduleAdd(StatesGroup):
    day = State()
    time = State()
    direction = State()
    teacher = State()
    duration = State()
    confirm = State()


class AdminScheduleEdit(StatesGroup):
    field = State()
    value = State()
