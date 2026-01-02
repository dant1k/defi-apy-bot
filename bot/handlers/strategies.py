from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from bot.database.crud import get_top_pools
from bot.utils.formatters import format_pools_list
from loguru import logger

router = Router()


@router.message(Command("find"))
async def cmd_find(message: Message):
    """Команда для поиска пулов по минимальному APR"""
    try:
        # Парсим аргументы команды
        args = message.text.split()[1:] if message.text else []
        
        if not args:
            await message.answer(
                "❌ Укажите минимальный APR\n\n"
                "Использование: /find [min_apr]\n"
                "Пример: /find 20 - найдет пулы с APR > 20%"
            )
            return
        
        try:
            min_apr = float(args[0])
        except ValueError:
            await message.answer("❌ Неверный формат APR. Используйте число, например: /find 20")
            return
        
        if min_apr < 0 or min_apr > 10000:
            await message.answer("❌ APR должен быть от 0 до 10000%")
            return
        
        # Получаем пулы с фильтром
        pools = await get_top_pools(min_tvl=0.0, min_apr=min_apr, limit=20)
        
        if not pools:
            await message.answer(
                f"❌ Пулы с APR > {min_apr}% не найдены.\n\n"
                "Попробуйте:\n"
                "- Уменьшить минимальный APR\n"
                "- Использовать /pools для просмотра всех пулов"
            )
            return
        
        text = format_pools_list(
            pools,
            f"🔍 Найдено пулов с APR > {min_apr}%:"
        )
        
        await message.answer(text, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Error in cmd_find: {e}")
        await message.answer("❌ Произошла ошибка при поиске пулов.")

