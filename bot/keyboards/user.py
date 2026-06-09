from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

DAYS = {
    0: "Понедельник",
    1: "Вторник",
    2: "Среда",
    3: "Четверг",
    4: "Пятница",
    5: "Суббота",
    6: "Воскресенье",
}


def main_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📅 Расписание", callback_data="schedule")
    builder.button(text="✍️ Записаться", callback_data="enroll")
    builder.button(text="ℹ️ О школе", callback_data="about")
    builder.adjust(1)
    return builder.as_markup()


def schedule_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📆 По дням недели", callback_data="schedule:by_day")
    builder.button(text="💃 По направлению", callback_data="schedule:by_direction")
    builder.button(text="◀️ Назад", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()


def days_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for day_num, day_name in DAYS.items():
        builder.button(text=day_name, callback_data=f"schedule:day:{day_num}")
    builder.button(text="◀️ Назад", callback_data="schedule")
    builder.adjust(2)
    return builder.as_markup()


def directions_keyboard(directions: list[str]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for d in directions:
        builder.button(text=d, callback_data=f"schedule:dir:{d}")
    builder.button(text="◀️ Назад", callback_data="schedule")
    builder.adjust(2)
    return builder.as_markup()


def enrollment_directions_keyboard(directions: list[str]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for d in directions:
        builder.button(text=d, callback_data=f"enroll:dir:{d}")
    builder.button(text="Другое направление", callback_data="enroll:dir:Другое")
    builder.adjust(2)
    return builder.as_markup()


def enrollment_confirm_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Подтвердить", callback_data="enroll:confirm")
    builder.button(text="❌ Отменить", callback_data="enroll:cancel")
    builder.adjust(2)
    return builder.as_markup()


def back_to_main_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ В главное меню", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()


def phone_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Поделиться номером", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
