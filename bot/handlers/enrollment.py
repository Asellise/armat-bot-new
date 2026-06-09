from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove

from config import settings
from db.database import AsyncSessionLocal
from db.crud import get_or_create_user, create_enrollment_request, get_active_directions
from bot.keyboards.user import (
    enrollment_directions_keyboard,
    enrollment_confirm_keyboard,
    back_to_main_keyboard,
    phone_keyboard,
    main_menu_keyboard,
)
from bot.states import EnrollmentForm

router = Router()


# ── Entry point ────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "enroll")
async def cb_enroll_start(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "✍️ <b>Запись на занятие</b>\n\n"
        "Шаг 1 из 4\n\n"
        "Пожалуйста, введите ваше <b>имя и фамилию</b>:",
        reply_markup=None,
    )
    await state.set_state(EnrollmentForm.name)
    await callback.answer()


# ── Step 1: Name ───────────────────────────────────────────────────────────────

@router.message(EnrollmentForm.name)
async def process_name(message: Message, state: FSMContext):
    name = message.text.strip() if message.text else ""
    if not name or len(name) < 2:
        await message.answer("⚠️ Пожалуйста, введите корректное имя (минимум 2 символа).")
        return

    await state.update_data(name=name)
    await message.answer(
        f"✅ Имя: <b>{name}</b>\n\n"
        "Шаг 2 из 4\n\n"
        "Введите ваш <b>номер телефона</b> или нажмите кнопку ниже:",
        reply_markup=phone_keyboard(),
    )
    await state.set_state(EnrollmentForm.phone)


# ── Step 2: Phone ──────────────────────────────────────────────────────────────

@router.message(EnrollmentForm.phone, F.contact)
async def process_phone_contact(message: Message, state: FSMContext):
    phone = message.contact.phone_number
    await _save_phone_and_ask_direction(message, state, phone)


@router.message(EnrollmentForm.phone, F.text)
async def process_phone_text(message: Message, state: FSMContext):
    phone = message.text.strip()
    # Basic phone validation
    digits = "".join(c for c in phone if c.isdigit())
    if len(digits) < 7:
        await message.answer("⚠️ Пожалуйста, введите корректный номер телефона.")
        return
    await _save_phone_and_ask_direction(message, state, phone)


async def _save_phone_and_ask_direction(message: Message, state: FSMContext, phone: str):
    await state.update_data(phone=phone)

    async with AsyncSessionLocal() as session:
        directions = await get_active_directions(session)

    await message.answer(
        f"✅ Телефон: <b>{phone}</b>\n\n"
        "Шаг 3 из 4\n\n"
        "Выберите <b>направление</b>, которое вас интересует:",
        reply_markup=ReplyKeyboardRemove(),
    )
    await message.answer(
        "Выберите направление:",
        reply_markup=enrollment_directions_keyboard(directions),
    )
    await state.set_state(EnrollmentForm.direction)


# ── Step 3: Direction ──────────────────────────────────────────────────────────

@router.callback_query(EnrollmentForm.direction, F.data.startswith("enroll:dir:"))
async def process_direction(callback: CallbackQuery, state: FSMContext):
    direction = callback.data[len("enroll:dir:"):]
    await state.update_data(direction=direction)

    data = await state.get_data()
    text = (
        "📋 <b>Проверьте ваши данные:</b>\n\n"
        f"👤 <b>Имя:</b> {data['name']}\n"
        f"📞 <b>Телефон:</b> {data['phone']}\n"
        f"💃 <b>Направление:</b> {direction}\n\n"
        "Шаг 4 из 4 — Подтвердите заявку:"
    )
    await callback.message.edit_text(text, reply_markup=enrollment_confirm_keyboard())
    await state.set_state(EnrollmentForm.confirm)
    await callback.answer()


# ── Step 4: Confirm ────────────────────────────────────────────────────────────

@router.callback_query(EnrollmentForm.confirm, F.data == "enroll:confirm")
async def process_confirm(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    user = callback.from_user

    async with AsyncSessionLocal() as session:
        await get_or_create_user(session, user.id, user.username, user.first_name)
        req = await create_enrollment_request(
            session,
            user_id=user.id,
            name=data["name"],
            phone=data["phone"],
            direction=data["direction"],
        )

    await state.clear()

    await callback.message.edit_text(
        "🎉 <b>Заявка отправлена!</b>\n\n"
        f"Имя: {data['name']}\n"
        f"Телефон: {data['phone']}\n"
        f"Направление: {data['direction']}\n\n"
        "Мы свяжемся с вами в ближайшее время!\n\n"
        "🌐 <a href=\"https://armatdance.ru\">armatdance.ru</a>",
        reply_markup=back_to_main_keyboard(),
    )

    # Notify admin
    username_part = f"@{user.username}" if user.username else "нет username"
    admin_text = (
        f"🆕 <b>Новая заявка #{req.id}</b>\n\n"
        f"👤 Имя: {data['name']}\n"
        f"📞 Телефон: {data['phone']}\n"
        f"💃 Направление: {data['direction']}\n\n"
        f"Telegram: {user.first_name} ({username_part})\n"
        f"ID: <code>{user.id}</code>"
    )
    try:
        await bot.send_message(settings.ADMIN_ID, admin_text)
    except Exception:
        pass  # Don't fail if admin notification fails

    await callback.answer()


@router.callback_query(EnrollmentForm.confirm, F.data == "enroll:cancel")
async def process_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "❌ Заявка отменена.\n\nВозвращаю в главное меню.",
        reply_markup=main_menu_keyboard(),
    )
    await callback.answer()
