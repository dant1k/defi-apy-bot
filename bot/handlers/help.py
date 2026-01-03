"""
Обработчик команды /help - описание всех функций бота
"""
from aiogram import Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from loguru import logger

router = Router()


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Команда /help - показать описание всех функций"""
    try:
        help_text = (
            "📚 <b>Справка по командам бота</b>\n\n"
            "<b>Основные команды:</b>\n"
            "<code>/start</code> - Начать работу с ботом\n"
            "<code>/help</code> - Показать эту справку\n\n"
            "<b>Просмотр пулов:</b>\n"
            "<code>/pools</code> - Топ 10 пулов по TVL\n"
            "<code>/farm</code> - Пулы с farming\n\n"
            "<b>Поиск и фильтрация:</b>\n"
            "<code>/top [tvl|volume|apr|fees]</code> - Топ пулов по метрике\n"
            "<code>/search &lt;токен&gt;</code> - Поиск пулов по токену\n"
            "<code>/pool &lt;токен_a&gt;-&lt;токен_b&gt;</code> - Детальная информация о пуле\n\n"
            "<b>📈 Информация о пулах:</b>\n"
            "Каждый пул показывает:\n"
            "• Название пары (например: USDT-USDC)\n"
            "• Fee Tier (комиссия пула)\n"
            "• TVL, Volume 24H, Fees 24H\n"
            "• APR (Fee APR + Farm APR)"
        )
        
        await message.answer(help_text, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Error in cmd_help: {e}")
        await message.answer("❌ Произошла ошибка при показе справки.")


@router.message(Command("commands"))
async def cmd_commands(message: Message):
    """Краткий список всех команд"""
    try:
        commands_text = """
⚡ <b>Быстрый список команд:</b>

<code>/start</code> - Начать работу
<code>/help</code> - Подробная справка
<code>/stats</code> - Market Overview
<code>/pools</code> - Топ пулов
<code>/farm</code> - Пулы с farming
<code>/top [tvl|volume|apr|fees]</code> - Топ по метрике
<code>/search &lt;токен&gt;</code> - Поиск
<code>/pool &lt;токен_a&gt;-&lt;токен_b&gt;</code> - Детали пула

Используйте <code>/help</code> для подробного описания всех функций.
        """
        
        # Главное меню теперь постоянное (ReplyKeyboardMarkup), не нужно добавлять inline кнопки
        await message.answer(commands_text, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Error in cmd_commands: {e}")
        await message.answer("❌ Произошла ошибка.")

