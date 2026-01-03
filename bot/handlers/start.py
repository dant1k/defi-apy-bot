from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command

from bot.database.crud import get_or_create_user
from loguru import logger

router = Router()


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Создать постоянное меню внизу экрана"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🏠 Главное меню"),
                KeyboardButton(text="🔷 Выбрать блокчейн")
            ],
            [
                KeyboardButton(text="📚 Справка")
            ]
        ],
        resize_keyboard=True,
        persistent=True
    )


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Обработка команды /start"""
    try:
        # Регистрируем пользователя
        await get_or_create_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username
        )
        
        # Создаем постоянное меню
        keyboard = get_main_menu_keyboard()
        
        welcome_text = (
            "👋 Добро пожаловать в <b>DeFi APY Bot</b>!\n\n"
            "Я помогу вам анализировать пулы ликвидности в различных DeFi протоколах.\n\n"
            "С помощью этого бота вы можете:\n"
            "• Просматривать статистику протоколов (TVL, Volume, Fees)\n"
            "• Анализировать пулы ликвидности\n"
            "• Отслеживать APR и доходность\n"
            "• Находить лучшие возможности для инвестирования\n\n"
            "<b>📋 Закрепленное меню внизу экрана:</b>\n\n"
            "• <b>🏠 Главное меню</b> - вернуться к этому приветственному сообщению\n"
            "• <b>🔷 Выбрать блокчейн</b> - выбрать блокчейн для работы\n"
            "• <b>📚 Справка</b> - полная информация о командах\n\n"
            "👉 Нажмите кнопку <b>📚 Справка</b> в меню, чтобы узнать все доступные команды и начать работу!"
        )
        
        await message.answer(welcome_text, reply_markup=keyboard, parse_mode="HTML")
        logger.info(f"User {message.from_user.id} started the bot")
        
    except Exception as e:
        logger.error(f"Error in cmd_start: {e}")
        await message.answer("❌ Произошла ошибка. Попробуйте позже.")


# Обработчики текстовых сообщений от кнопок меню
@router.message(F.text == "🏠 Главное меню")
async def handle_menu_home(message: Message):
    """Обработка нажатия на кнопку '🏠 Главное меню'"""
    # Вызываем cmd_start для показа стартового сообщения
    await cmd_start(message)


@router.message(F.text == "🔷 Выбрать блокчейн")
async def handle_menu_blockchain(message: Message):
    """Обработка нажатия на кнопку '🔷 Выбрать блокчейн'"""
    try:
        text = (
            "🔷 <b>Выберите блокчейн</b>\n\n"
            "Доступные блокчейны:"
        )
        
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔷 Aptos", callback_data="select_blockchain_aptos")],
            [InlineKeyboardButton(text="🔵 Sui", callback_data="select_blockchain_sui")]
        ])
        
        await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error in handle_menu_blockchain: {e}")
        await message.answer("❌ Произошла ошибка.")


@router.message(F.text == "📚 Справка")
async def handle_menu_help(message: Message):
    """Обработка нажатия на кнопку '📚 Справка'"""
    # Перенаправляем на команду /help
    from bot.handlers.help import cmd_help
    await cmd_help(message)


# Старые callback обработчики (оставляем для совместимости, но они больше не используются в меню)
@router.callback_query(F.data == "cmd_stats")
async def callback_cmd_stats(callback: CallbackQuery):
    """Обработка нажатия на кнопку 'Market Stats' (callback)"""
    await callback.answer()
    await callback.message.edit_text(
        "📊 <b>Market Stats</b>\n\n"
        "Показывает общую статистику рынка:\n"
        "• Total Value Locked (TVL)\n"
        "• Cumulative Volume\n"
        "• 24H Trading Volume\n"
        "• Capital Efficiency\n\n"
        "Используйте команду: <code>/stats</code>",
        parse_mode="HTML"
    )


@router.callback_query(F.data == "cmd_pools")
async def callback_cmd_pools(callback: CallbackQuery):
    """Обработка нажатия на кнопку 'Все пулы' (callback)"""
    await callback.answer()
    await callback.message.edit_text(
        "🏊 <b>Все пулы</b>\n\n"
        "Показывает топ 10 пулов по TVL с информацией:\n"
        "• Название пары и Fee Tier\n"
        "• TVL, Volume 24H, Fees 24H\n"
        "• APR (Fee + Farm)\n\n"
        "Используйте команду: <code>/pools</code>\n\n"
        "Доступны inline кнопки для фильтрации и сортировки.",
        parse_mode="HTML"
    )


@router.callback_query(F.data == "cmd_farm")
async def callback_cmd_farm(callback: CallbackQuery):
    """Обработка нажатия на кнопку 'Farm пулы' (callback)"""
    await callback.answer()
    await callback.message.edit_text(
        "🌾 <b>Farm пулы</b>\n\n"
        "Показывает только пулы с farming (farmAPR > 0).\n"
        "Эти пулы дают дополнительный доход от farming.\n\n"
        "Используйте команду: <code>/farm</code>",
        parse_mode="HTML"
    )


@router.callback_query(F.data == "cmd_help")
async def callback_cmd_help(callback: CallbackQuery):
    """Обработка нажатия на кнопку 'Справка' (callback)"""
    await callback.answer()
    await callback.message.edit_text(
        "📚 <b>Справка</b>\n\n"
        "Полное описание всех команд и функций бота.\n\n"
        "Используйте команду: <code>/help</code>\n\n"
        "Или краткий список: <code>/commands</code>",
        parse_mode="HTML"
    )
