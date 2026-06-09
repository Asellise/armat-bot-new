from aiogram import Router, F
from aiogram.types import CallbackQuery

from db.database import AsyncSessionLocal
from db.crud import get_schedule_by_day, get_schedule_by_direction, get_active_directions
from db.models import DAYS_OF_WEEK
from bot.keyboards.user import schedule_menu_keyboard, days_keyboard, directions_keyboard, back_to_main_keyboard

router = Router()


def format_schedule_item(item) -> str:
    return f"🕐 <b>{item.time}</b> — {item.direction}\n   👤 {item.teacher} | ⏱ {item.duration_minutes} мин"


@router.callback_query(F.data == "schedule")
async def cb_schedule_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "📅 <b>Расписание занятий</b>\n\nВыберите способ просмотра:",
        reply_markup=schedule_menu_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "schedule:by_day")
async def cb_schedule_by_day(callback: CallbackQuery):
    await callback.message.edit_text(
        "📆 <b>Выберите день недели:</b>",
        reply_markup=days_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("schedule:day:"))
async def cb_schedule_day(callback: CallbackQuery):
    day_num = int(callback.data.split(":")[2])
    day_name = DAYS_OF_WEEK[day_num]

    async with AsyncSessionLocal() as session:
        items = await get_schedule_by_day(session, day_num)

    if not items:
        text = f"📅 <b>{day_name}</b>\n\nВ этот день занятий нет."
    else:
        lines = [f"📅 <b>{day_name}</b>\n"]
        for item in items:
            lines.append(format_schedule_item(item))
        text = "\n".join(lines)

    from aiogram.utils.keyboard import InlineKeyboardBuilder as IKB

    builder = IKB()
    builder.button(text="◀️ К дням недели", callback_data="schedule:by_day")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(1)

    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "schedule:by_direction")
async def cb_schedule_by_direction(callback: CallbackQuery):
    async with AsyncSessionLocal() as session:
        directions = await get_active_directions(session)

    if not directions:
        await callback.message.edit_text(
            "💃 Направлений пока нет в расписании.",
            reply_markup=back_to_main_keyboard(),
            parse_mode="HTML",
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        "💃 <b>Выберите направление:</b>",
        reply_markup=directions_keyboard(directions),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("schedule:dir:"))
async def cb_schedule_direction(callback: CallbackQuery):
    direction = callback.data[len("schedule:dir:"):]

    async with AsyncSessionLocal() as session:
        items = await get_schedule_by_direction(session, direction)

    if not items:
        text = f"💃 <b>{direction}</b>\n\nЗанятий по этому направлению пока нет."
    else:
        lines = [f"💃 <b>{direction}</b>\n"]
        for item in items:
            day_name = DAYS_OF_WEEK[item.day_of_week]
            lines.append(f"📆 <b>{day_name}</b> — {format_schedule_item(item)}")
        text = "\n".join(lines)

    from aiogram.utils.keyboard import InlineKeyboardBuilder as IKB
    builder = IKB()
    builder.button(text="◀️ К направлениям", callback_data="schedule:by_direction")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(1)

    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()
