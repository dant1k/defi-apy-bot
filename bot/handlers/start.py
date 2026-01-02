from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

from bot.database.crud import get_or_create_user
from loguru import logger

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Обработка команды /start"""
    try:
        # Регистрируем пользователя
        await get_or_create_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username
        )
        
        # Создаем клавиатуру
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔍 Найти пулы", callback_data="find_pools"),
                InlineKeyboardButton(text="📊 Топ пулы", callback_data="top_pools")
            ],
            [
                InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings")
            ]
        ])
        
        welcome_text = (
            "👋 Добро пожаловать в DeFi APY Bot!\n\n"
            "Я помогу вам анализировать пулы ликвидности на блокчейне Aptos.\n\n"
            "Доступные функции:\n"
            "🔍 Найти пулы по критериям\n"
            "📊 Топ пулов по APR\n"
            "⚙️ Настройка фильтров\n\n"
            "Выберите действие:"
        )
        
        await message.answer(welcome_text, reply_markup=keyboard)
        logger.info(f"User {message.from_user.id} started the bot")
        
    except Exception as e:
        logger.error(f"Error in cmd_start: {e}")
        await message.answer("❌ Произошла ошибка. Попробуйте позже.")


@router.callback_query(F.data == "find_pools")
async def callback_find_pools(callback: CallbackQuery):
    """Обработка нажатия на кнопку 'Найти пулы'"""
    await callback.answer()
    await callback.message.edit_text(
        "🔍 Поиск пулов\n\n"
        "Используйте команду /find с минимальным APR\n"
        "Например: /find 20 - найдет пулы с APR > 20%"
    )


@router.callback_query(F.data == "top_pools")
async def callback_top_pools(callback: CallbackQuery):
    """Обработка нажатия на кнопку 'Топ пулы'"""
    await callback.answer()
    await callback.message.edit_text(
        "📊 Топ пулов\n\n"
        "Используйте команду /pools чтобы увидеть топ 10 пулов по APR"
    )


@router.callback_query(F.data == "settings")
async def callback_settings(callback: CallbackQuery):
    """Обработка нажатия на кнопку 'Настройки'"""
    await callback.answer()
    await callback.message.edit_text(
        "⚙️ Настройки\n\n"
        "Здесь можно настроить фильтры:\n"
        "- Минимальный TVL\n"
        "- Минимальный APR\n\n"
        "Функция в разработке..."
    )

