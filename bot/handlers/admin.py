from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from config import settings
from db.database import AsyncSessionLocal
from db.crud import (
    get_all_users,
    get_all_schedule,
    get_schedule_item,
    create_schedule_item,
    update_schedule_item,
    delete_schedule_item,
    get_enrollment_requests,
    mark_enrollment_seen,
)
from db.models import DAYS_OF_WEEK
from bot.keyboards.admin import (
    admin_menu_keyboard,
    admin_requests_keyboard,
    admin_request_detail_keyboard,
    admin_broadcast_confirm_keyboard,
    admin_schedule_keyboard,
    admin_schedule_item_keyboard,
    admin_schedule_edit_keyboard,
    admin_days_keyboard,
    admin_delete_confirm_keyboard,
)
from bot.states import AdminBroadcast, AdminScheduleAdd, AdminScheduleEdit

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id == settings.ADMIN_ID


# ── Admin guard ────────────────────────────────────────────────────────────────

@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ У вас нет доступа к панели администратора.")
        return
    await state.clear()
    await message.answer(
        "🔧 <b>Панель администратора</b>\n\nВыберите раздел:",
        reply_markup=admin_menu_keyboard(),
    )


@router.callback_query(F.data == "admin:menu")
async def cb_admin_menu(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа.", show_alert=True)
        return
    await state.clear()
    await callback.message.edit_text(
        "🔧 <b>Панель администратора</b>\n\nВыберите раздел:",
        reply_markup=admin_menu_keyboard(),
    )
    await callback.answer()


# ── Enrollment Requests ────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin:requests")
async def cb_admin_requests(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа.", show_alert=True)
        return

    async with AsyncSessionLocal() as session:
        requests = await get_enrollment_requests(session)

    if not requests:
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        b = InlineKeyboardBuilder()
        b.button(text="◀️ Назад", callback_data="admin:menu")
        await callback.message.edit_text(
            "📋 <b>Заявки на запись</b>\n\nЗаявок пока нет.",
            reply_markup=b.as_markup(),
        )
        await callback.answer()
        return

    new_count = sum(1 for r in requests if r.status == "new")
    await callback.message.edit_text(
        f"📋 <b>Заявки на запись</b>\n\n"
        f"Всего: {len(requests)} | Новых: {new_count}\n\n"
        "Выберите заявку:",
        reply_markup=admin_requests_keyboard(requests),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:req:"))
async def cb_admin_request_detail(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа.", show_alert=True)
        return

    req_id = int(callback.data.split(":")[2])
    async with AsyncSessionLocal() as session:
        requests = await get_enrollment_requests(session)

    req = next((r for r in requests if r.id == req_id), None)
    if not req:
        await callback.answer("Заявка не найдена.", show_alert=True)
        return

    status_text = "🆕 Новая" if req.status == "new" else "✅ Просмотрена"
    created = req.created_at.strftime("%d.%m.%Y %H:%M")
    text = (
        f"📋 <b>Заявка #{req.id}</b>\n\n"
        f"👤 Имя: {req.name}\n"
        f"📞 Телефон: <code>{req.phone}</code>\n"
        f"💃 Направление: {req.direction}\n"
        f"👤 Telegram ID: <code>{req.user_id}</code>\n"
        f"📅 Дата: {created}\n"
        f"Статус: {status_text}"
    )
    if req.message:
        text += f"\n💬 Сообщение: {req.message}"

    await callback.message.edit_text(
        text,
        reply_markup=admin_request_detail_keyboard(req.id, req.status),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:req_seen:"))
async def cb_admin_req_seen(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа.", show_alert=True)
        return

    req_id = int(callback.data.split(":")[2])
    async with AsyncSessionLocal() as session:
        await mark_enrollment_seen(session, req_id)

    await callback.answer("✅ Отмечено как просмотренное.")

    # Refresh request detail
    async with AsyncSessionLocal() as session:
        requests = await get_enrollment_requests(session)
    req = next((r for r in requests if r.id == req_id), None)
    if req:
        created = req.created_at.strftime("%d.%m.%Y %H:%M")
        text = (
            f"📋 <b>Заявка #{req.id}</b>\n\n"
            f"👤 Имя: {req.name}\n"
            f"📞 Телефон: <code>{req.phone}</code>\n"
            f"💃 Направление: {req.direction}\n"
            f"👤 Telegram ID: <code>{req.user_id}</code>\n"
            f"📅 Дата: {created}\n"
            f"Статус: ✅ Просмотрена"
        )
        await callback.message.edit_text(
            text,
            reply_markup=admin_request_detail_keyboard(req.id, req.status),
        )


# ── Broadcast ──────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin:broadcast")
async def cb_admin_broadcast(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа.", show_alert=True)
        return

    await state.clear()
    await callback.message.edit_text(
        "📢 <b>Рассылка сообщений</b>\n\n"
        "Введите текст сообщения для рассылки всем пользователям:\n"
        "(поддерживается HTML-форматирование)",
        reply_markup=None,
    )
    await state.set_state(AdminBroadcast.message)
    await callback.answer()


@router.message(AdminBroadcast.message)
async def process_broadcast_message(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    await state.update_data(text=message.text or message.caption or "")
    preview = message.text or "(медиа-сообщение)"

    await message.answer(
        f"📢 <b>Предварительный просмотр:</b>\n\n{preview}\n\n"
        "Отправить это сообщение всем пользователям?",
        reply_markup=admin_broadcast_confirm_keyboard(),
    )
    await state.set_state(AdminBroadcast.confirm)


@router.callback_query(AdminBroadcast.confirm, F.data == "admin:broadcast_confirm")
async def process_broadcast_confirm(callback: CallbackQuery, state: FSMContext, bot: Bot):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа.", show_alert=True)
        return

    data = await state.get_data()
    text = data.get("text", "")
    await state.clear()

    async with AsyncSessionLocal() as session:
        users = await get_all_users(session)

    await callback.message.edit_text(
        f"📢 Начинаю рассылку для {len(users)} пользователей..."
    )

    sent = 0
    failed = 0
    for user in users:
        try:
            await bot.send_message(user.id, text)
            sent += 1
        except Exception:
            failed += 1

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    b = InlineKeyboardBuilder()
    b.button(text="◀️ В меню", callback_data="admin:menu")

    await callback.message.edit_text(
        f"✅ <b>Рассылка завершена</b>\n\n"
        f"Отправлено: {sent}\n"
        f"Ошибок: {failed}",
        reply_markup=b.as_markup(),
    )
    await callback.answer()


@router.callback_query(AdminBroadcast.confirm, F.data == "admin:menu")
async def process_broadcast_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "🔧 <b>Панель администратора</b>\n\nВыберите раздел:",
        reply_markup=admin_menu_keyboard(),
    )
    await callback.answer()


# ── Schedule Management ────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin:schedule")
async def cb_admin_schedule(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа.", show_alert=True)
        return

    await state.clear()
    async with AsyncSessionLocal() as session:
        items = await get_all_schedule(session)

    if not items:
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        b = InlineKeyboardBuilder()
        b.button(text="➕ Добавить занятие", callback_data="admin:sched_add")
        b.button(text="◀️ Назад", callback_data="admin:menu")
        b.adjust(1)
        await callback.message.edit_text(
            "📅 <b>Управление расписанием</b>\n\nРасписание пусто.",
            reply_markup=b.as_markup(),
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        f"📅 <b>Управление расписанием</b>\n\nВсего занятий: {len(items)}\n"
        "Выберите занятие для управления:",
        reply_markup=admin_schedule_keyboard(items),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:sched:"))
async def cb_admin_schedule_item(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа.", show_alert=True)
        return

    item_id = int(callback.data.split(":")[2])
    async with AsyncSessionLocal() as session:
        item = await get_schedule_item(session, item_id)

    if not item:
        await callback.answer("Занятие не найдено.", show_alert=True)
        return

    day_name = DAYS_OF_WEEK[item.day_of_week]
    status = "✅ Активно" if item.active else "❌ Неактивно"
    text = (
        f"📅 <b>Занятие #{item.id}</b>\n\n"
        f"📆 День: {day_name}\n"
        f"🕐 Время: {item.time}\n"
        f"💃 Направление: {item.direction}\n"
        f"👤 Преподаватель: {item.teacher}\n"
        f"⏱ Длительность: {item.duration_minutes} мин\n"
        f"Статус: {status}"
    )
    await callback.message.edit_text(
        text,
        reply_markup=admin_schedule_item_keyboard(item.id, item.active),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:sched_toggle:"))
async def cb_admin_schedule_toggle(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа.", show_alert=True)
        return

    item_id = int(callback.data.split(":")[2])
    async with AsyncSessionLocal() as session:
        item = await get_schedule_item(session, item_id)
        if not item:
            await callback.answer("Занятие не найдено.", show_alert=True)
            return
        await update_schedule_item(session, item_id, active=not item.active)
        item = await get_schedule_item(session, item_id)

    day_name = DAYS_OF_WEEK[item.day_of_week]
    status = "✅ Активно" if item.active else "❌ Неактивно"
    text = (
        f"📅 <b>Занятие #{item.id}</b>\n\n"
        f"📆 День: {day_name}\n"
        f"🕐 Время: {item.time}\n"
        f"💃 Направление: {item.direction}\n"
        f"👤 Преподаватель: {item.teacher}\n"
        f"⏱ Длительность: {item.duration_minutes} мин\n"
        f"Статус: {status}"
    )
    await callback.message.edit_text(
        text,
        reply_markup=admin_schedule_item_keyboard(item.id, item.active),
    )
    await callback.answer("Статус обновлён.")


@router.callback_query(F.data.startswith("admin:sched_delete:"))
async def cb_admin_schedule_delete(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа.", show_alert=True)
        return

    parts = callback.data.split(":")
    # admin:sched_delete:<id>  (not confirm)
    item_id = int(parts[2])
    async with AsyncSessionLocal() as session:
        item = await get_schedule_item(session, item_id)

    if not item:
        await callback.answer("Занятие не найдено.", show_alert=True)
        return

    day_name = DAYS_OF_WEEK[item.day_of_week]
    await callback.message.edit_text(
        f"🗑 <b>Удалить занятие?</b>\n\n"
        f"{day_name} {item.time} — {item.direction} ({item.teacher})\n\n"
        "Это действие необратимо.",
        reply_markup=admin_delete_confirm_keyboard(item_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:sched_delete_confirm:"))
async def cb_admin_schedule_delete_confirm(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа.", show_alert=True)
        return

    item_id = int(callback.data.split(":")[2])
    async with AsyncSessionLocal() as session:
        await delete_schedule_item(session, item_id)

    await callback.answer("🗑 Занятие удалено.")

    # Refresh schedule list
    async with AsyncSessionLocal() as session:
        items = await get_all_schedule(session)

    if not items:
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        b = InlineKeyboardBuilder()
        b.button(text="➕ Добавить занятие", callback_data="admin:sched_add")
        b.button(text="◀️ Назад", callback_data="admin:menu")
        b.adjust(1)
        await callback.message.edit_text(
            "📅 <b>Управление расписанием</b>\n\nРасписание пусто.",
            reply_markup=b.as_markup(),
        )
    else:
        await callback.message.edit_text(
            f"📅 <b>Управление расписанием</b>\n\nВсего занятий: {len(items)}\n"
            "Выберите занятие:",
            reply_markup=admin_schedule_keyboard(items),
        )


# ── Add Schedule Item ──────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin:sched_add")
async def cb_admin_schedule_add(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа.", show_alert=True)
        return

    await state.clear()
    await callback.message.edit_text(
        "➕ <b>Добавление занятия</b>\n\n"
        "Шаг 1: Выберите <b>день недели</b>:",
        reply_markup=admin_days_keyboard(),
    )
    await state.set_state(AdminScheduleAdd.day)
    await callback.answer()


@router.callback_query(AdminScheduleAdd.day, F.data.startswith("admin:sched_day:"))
async def process_add_day(callback: CallbackQuery, state: FSMContext):
    day = int(callback.data.split(":")[2])
    await state.update_data(day_of_week=day)
    day_name = DAYS_OF_WEEK[day]

    await callback.message.edit_text(
        f"✅ День: <b>{day_name}</b>\n\n"
        "Шаг 2: Введите <b>время начала</b> в формате ЧЧ:ММ (например: 18:30):",
        reply_markup=None,
    )
    await state.set_state(AdminScheduleAdd.time)
    await callback.answer()


@router.message(AdminScheduleAdd.time)
async def process_add_time(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    time_str = message.text.strip() if message.text else ""
    # Validate HH:MM format
    import re
    if not re.match(r"^\d{1,2}:\d{2}$", time_str):
        await message.answer("⚠️ Введите время в формате ЧЧ:ММ, например: 18:30")
        return

    await state.update_data(time=time_str)
    await message.answer(
        f"✅ Время: <b>{time_str}</b>\n\n"
        "Шаг 3: Введите <b>направление</b> (стиль танца):"
    )
    await state.set_state(AdminScheduleAdd.direction)


@router.message(AdminScheduleAdd.direction)
async def process_add_direction(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    direction = message.text.strip() if message.text else ""
    if not direction:
        await message.answer("⚠️ Введите название направления.")
        return

    await state.update_data(direction=direction)
    await message.answer(
        f"✅ Направление: <b>{direction}</b>\n\n"
        "Шаг 4: Введите <b>имя преподавателя</b>:"
    )
    await state.set_state(AdminScheduleAdd.teacher)


@router.message(AdminScheduleAdd.teacher)
async def process_add_teacher(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    teacher = message.text.strip() if message.text else ""
    if not teacher:
        await message.answer("⚠️ Введите имя преподавателя.")
        return

    await state.update_data(teacher=teacher)
    await message.answer(
        f"✅ Преподаватель: <b>{teacher}</b>\n\n"
        "Шаг 5: Введите <b>длительность</b> занятия в минутах (например: 60):"
    )
    await state.set_state(AdminScheduleAdd.duration)


@router.message(AdminScheduleAdd.duration)
async def process_add_duration(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    text = message.text.strip() if message.text else ""
    if not text.isdigit() or int(text) <= 0:
        await message.answer("⚠️ Введите длительность в минутах (целое число, например: 60).")
        return

    duration = int(text)
    await state.update_data(duration_minutes=duration)

    data = await state.get_data()
    day_name = DAYS_OF_WEEK[data["day_of_week"]]

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    b = InlineKeyboardBuilder()
    b.button(text="✅ Добавить", callback_data="admin:sched_add_confirm")
    b.button(text="❌ Отменить", callback_data="admin:schedule")
    b.adjust(2)

    await message.answer(
        f"📋 <b>Проверьте данные нового занятия:</b>\n\n"
        f"📆 День: {day_name}\n"
        f"🕐 Время: {data['time']}\n"
        f"💃 Направление: {data['direction']}\n"
        f"👤 Преподаватель: {data['teacher']}\n"
        f"⏱ Длительность: {duration} мин",
        reply_markup=b.as_markup(),
    )
    await state.set_state(AdminScheduleAdd.confirm)


@router.callback_query(AdminScheduleAdd.confirm, F.data == "admin:sched_add_confirm")
async def process_add_confirm(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа.", show_alert=True)
        return

    data = await state.get_data()
    await state.clear()

    async with AsyncSessionLocal() as session:
        item = await create_schedule_item(
            session,
            day_of_week=data["day_of_week"],
            time=data["time"],
            direction=data["direction"],
            teacher=data["teacher"],
            duration_minutes=data["duration_minutes"],
        )

    day_name = DAYS_OF_WEEK[item.day_of_week]
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    b = InlineKeyboardBuilder()
    b.button(text="📅 К расписанию", callback_data="admin:schedule")
    b.button(text="◀️ В меню", callback_data="admin:menu")
    b.adjust(1)

    await callback.message.edit_text(
        f"✅ <b>Занятие добавлено!</b>\n\n"
        f"📆 {day_name} {item.time} — {item.direction}\n"
        f"👤 {item.teacher} | ⏱ {item.duration_minutes} мин",
        reply_markup=b.as_markup(),
    )
    await callback.answer()


# ── Edit Schedule Item ─────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("admin:sched_edit:"))
async def cb_admin_schedule_edit(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа.", show_alert=True)
        return

    item_id = int(callback.data.split(":")[2])
    await state.clear()
    await state.update_data(item_id=item_id)

    await callback.message.edit_text(
        "✏️ <b>Редактирование занятия</b>\n\nВыберите поле для изменения:",
        reply_markup=admin_schedule_edit_keyboard(item_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:sched_editfield:"))
async def cb_admin_schedule_editfield(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа.", show_alert=True)
        return

    parts = callback.data.split(":")
    item_id = int(parts[2])
    field = parts[3]

    await state.update_data(item_id=item_id, field=field)

    field_prompts = {
        "day_of_week": "Выберите новый день недели:",
        "time": "Введите новое время в формате ЧЧ:ММ:",
        "direction": "Введите новое направление:",
        "teacher": "Введите нового преподавателя:",
        "duration_minutes": "Введите новую длительность в минутах:",
    }

    if field == "day_of_week":
        await callback.message.edit_text(
            f"✏️ {field_prompts[field]}",
            reply_markup=admin_days_keyboard(),
        )
        await state.set_state(AdminScheduleEdit.field)
    else:
        await callback.message.edit_text(
            f"✏️ {field_prompts.get(field, 'Введите новое значение:')}",
            reply_markup=None,
        )
        await state.set_state(AdminScheduleEdit.value)

    await callback.answer()


@router.callback_query(AdminScheduleEdit.field, F.data.startswith("admin:sched_day:"))
async def process_edit_day(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа.", show_alert=True)
        return

    day = int(callback.data.split(":")[2])
    data = await state.get_data()
    item_id = data["item_id"]

    async with AsyncSessionLocal() as session:
        await update_schedule_item(session, item_id, day_of_week=day)

    await state.clear()
    day_name = DAYS_OF_WEEK[day]
    await callback.answer(f"✅ День обновлён: {day_name}")

    async with AsyncSessionLocal() as session:
        item = await get_schedule_item(session, item_id)

    day_name2 = DAYS_OF_WEEK[item.day_of_week]
    status = "✅ Активно" if item.active else "❌ Неактивно"
    text = (
        f"📅 <b>Занятие #{item.id}</b>\n\n"
        f"📆 День: {day_name2}\n"
        f"🕐 Время: {item.time}\n"
        f"💃 Направление: {item.direction}\n"
        f"👤 Преподаватель: {item.teacher}\n"
        f"⏱ Длительность: {item.duration_minutes} мин\n"
        f"Статус: {status}"
    )
    await callback.message.edit_text(
        text,
        reply_markup=admin_schedule_item_keyboard(item.id, item.active),
    )


@router.message(AdminScheduleEdit.value)
async def process_edit_value(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    data = await state.get_data()
    item_id = data["item_id"]
    field = data["field"]
    value = message.text.strip() if message.text else ""

    import re

    if field == "time":
        if not re.match(r"^\d{1,2}:\d{2}$", value):
            await message.answer("⚠️ Введите время в формате ЧЧ:ММ")
            return
    elif field == "duration_minutes":
        if not value.isdigit() or int(value) <= 0:
            await message.answer("⚠️ Введите целое положительное число")
            return
        value = int(value)
    elif not value:
        await message.answer("⚠️ Значение не может быть пустым.")
        return

    async with AsyncSessionLocal() as session:
        await update_schedule_item(session, item_id, **{field: value})
        item = await get_schedule_item(session, item_id)

    await state.clear()

    day_name = DAYS_OF_WEEK[item.day_of_week]
    status = "✅ Активно" if item.active else "❌ Неактивно"
    text = (
        f"📅 <b>Занятие #{item.id} — обновлено</b>\n\n"
        f"📆 День: {day_name}\n"
        f"🕐 Время: {item.time}\n"
        f"💃 Направление: {item.direction}\n"
        f"👤 Преподаватель: {item.teacher}\n"
        f"⏱ Длительность: {item.duration_minutes} мин\n"
        f"Статус: {status}"
    )
    await message.answer(
        text,
        reply_markup=admin_schedule_item_keyboard(item.id, item.active),
    )
