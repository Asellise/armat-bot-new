from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup

DAYS = {
    0: "Пн",
    1: "Вт",
    2: "Ср",
    3: "Чт",
    4: "Пт",
    5: "Сб",
    6: "Вс",
}


def admin_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📋 Заявки на запись", callback_data="admin:requests")
    builder.button(text="📢 Рассылка", callback_data="admin:broadcast")
    builder.button(text="📅 Управление расписанием", callback_data="admin:schedule")
    builder.adjust(1)
    return builder.as_markup()


def admin_requests_keyboard(requests: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for req in requests:
        status_icon = "🆕" if req.status == "new" else "✅"
        builder.button(
            text=f"{status_icon} #{req.id} {req.name} — {req.direction}",
            callback_data=f"admin:req:{req.id}",
        )
    builder.button(text="◀️ Назад", callback_data="admin:menu")
    builder.adjust(1)
    return builder.as_markup()


def admin_request_detail_keyboard(req_id: int, status: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if status == "new":
        builder.button(text="✅ Отметить как просмотренную", callback_data=f"admin:req_seen:{req_id}")
    builder.button(text="◀️ К списку заявок", callback_data="admin:requests")
    builder.adjust(1)
    return builder.as_markup()


def admin_broadcast_confirm_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Отправить всем", callback_data="admin:broadcast_confirm")
    builder.button(text="❌ Отменить", callback_data="admin:menu")
    builder.adjust(2)
    return builder.as_markup()


def admin_schedule_keyboard(items: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for item in items:
        status = "✅" if item.active else "❌"
        builder.button(
            text=f"{status} {DAYS[item.day_of_week]} {item.time} — {item.direction}",
            callback_data=f"admin:sched:{item.id}",
        )
    builder.button(text="➕ Добавить занятие", callback_data="admin:sched_add")
    builder.button(text="◀️ Назад", callback_data="admin:menu")
    builder.adjust(1)
    return builder.as_markup()


def admin_schedule_item_keyboard(item_id: int, active: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    toggle_text = "❌ Деактивировать" if active else "✅ Активировать"
    builder.button(text=toggle_text, callback_data=f"admin:sched_toggle:{item_id}")
    builder.button(text="✏️ Редактировать", callback_data=f"admin:sched_edit:{item_id}")
    builder.button(text="🗑 Удалить", callback_data=f"admin:sched_delete:{item_id}")
    builder.button(text="◀️ К расписанию", callback_data="admin:schedule")
    builder.adjust(1)
    return builder.as_markup()


def admin_schedule_edit_keyboard(item_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    fields = [
        ("День недели", "day_of_week"),
        ("Время", "time"),
        ("Направление", "direction"),
        ("Преподаватель", "teacher"),
        ("Длительность (мин)", "duration_minutes"),
    ]
    for label, field in fields:
        builder.button(text=label, callback_data=f"admin:sched_editfield:{item_id}:{field}")
    builder.button(text="◀️ Назад", callback_data=f"admin:sched:{item_id}")
    builder.adjust(1)
    return builder.as_markup()


def admin_days_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    days_full = {
        0: "Понедельник", 1: "Вторник", 2: "Среда",
        3: "Четверг", 4: "Пятница", 5: "Суббота", 6: "Воскресенье",
    }
    for num, name in days_full.items():
        builder.button(text=name, callback_data=f"admin:sched_day:{num}")
    builder.adjust(2)
    return builder.as_markup()


def admin_delete_confirm_keyboard(item_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да, удалить", callback_data=f"admin:sched_delete_confirm:{item_id}")
    builder.button(text="❌ Отмена", callback_data=f"admin:sched:{item_id}")
    builder.adjust(2)
    return builder.as_markup()
