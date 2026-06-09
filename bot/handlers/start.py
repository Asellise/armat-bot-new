from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery

from db.database import AsyncSessionLocal
from db.crud import get_or_create_user
from bot.keyboards.user import main_menu_keyboard, back_to_main_keyboard

router = Router()

ABOUT_TEXT = (
    "🩰 <b>Школа танцев ARMAT</b>\n\n"
    "Мы открыты для всех — от начинающих до профессионалов.\n\n"
    "🌐 Сайт: <a href=\"https://armatdance.ru\">armatdance.ru</a>\n"
    "📍 Адрес: уточняйте на сайте\n"
    "📞 Телефон: уточняйте на сайте\n\n"
    "Выберите нужный раздел в меню ниже 👇"
)


@router.message(CommandStart())
async def cmd_start(message: Message):
    async with AsyncSessionLocal() as session:
        await get_or_create_user(
            session,
            user_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
        )

    text = (
        f"👋 Добро пожаловать, <b>{message.from_user.first_name}</b>!\n\n"
        "Я — бот школы танцев <b>ARMAT</b>.\n"
        "Здесь вы можете посмотреть расписание занятий и записаться на пробное.\n\n"
        "Выберите действие:"
    )
    await message.answer(text, reply_markup=main_menu_keyboard(), parse_mode="HTML")


@router.callback_query(F.data == "main_menu")
async def cb_main_menu(callback: CallbackQuery):
    text = (
        "🏠 <b>Главное меню</b>\n\n"
        "Выберите действие:"
    )
    await callback.message.edit_text(text, reply_markup=main_menu_keyboard(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "about")
async def cb_about(callback: CallbackQuery):
    await callback.message.edit_text(ABOUT_TEXT, reply_markup=back_to_main_keyboard(), parse_mode="HTML")
    await callback.answer()
