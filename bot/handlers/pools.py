from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

from bot.database.crud import get_top_pools, get_pool_by_address, get_all_pools
from bot.utils.formatters import format_pools_list, format_pool_message, format_pools_by_fee_tier
from bot.adapters.hyperion import HyperionAdapter
from bot.database.crud import upsert_pool
from loguru import logger
from collections import defaultdict

router = Router()


@router.message(Command("pools"))
async def cmd_pools(message: Message):
    """Команда для показа топ пулов"""
    try:
        # Получаем топ 10 пулов
        pools = await get_top_pools(min_tvl=0.0, min_apr=0.0, limit=10)
        
        if not pools:
            # Пытаемся обновить данные из адаптера
            await update_pools_from_adapter()
            pools = await get_top_pools(min_tvl=0.0, min_apr=0.0, limit=10)
        
        if not pools:
            await message.answer("❌ Пулы не найдены. Попробуйте обновить данные.")
            return
        
        text = format_pools_list(pools, "📊 Топ 10 пулов по APR:")
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Обновить", callback_data="refresh_pools"),
                InlineKeyboardButton(text="🔍 Фильтры", callback_data="filter_pools")
            ]
        ])
        
        await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Error in cmd_pools: {e}")
        await message.answer("❌ Произошла ошибка при получении пулов.")


@router.message(Command("pool"))
async def cmd_pool(message: Message):
    """Команда для показа конкретного пула по адресу"""
    try:
        # Парсим аргументы команды
        args = message.text.split()[1:] if message.text else []
        
        if not args:
            await message.answer(
                "❌ Укажите адрес пула\n\n"
                "Использование: /pool <pool_address>\n"
                "Пример: /pool 0x1234...abcd"
            )
            return
        
        pool_address = args[0].strip()
        
        # Получаем пул из БД
        pool = await get_pool_by_address(pool_address)
        
        if not pool:
            # Пытаемся обновить данные и найти снова
            await update_pools_from_adapter()
            pool = await get_pool_by_address(pool_address)
        
        if not pool:
            await message.answer(
                f"❌ Пул с адресом <code>{pool_address}</code> не найден.\n\n"
                "Попробуйте:\n"
                "- Проверить правильность адреса\n"
                "- Использовать /pools для просмотра доступных пулов"
            )
            return
        
        text = format_pool_message(pool)
        await message.answer(text, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Error in cmd_pool: {e}")
        await message.answer("❌ Произошла ошибка при получении пула.")


@router.message(Command("fee_tiers"))
async def cmd_fee_tiers(message: Message):
    """Команда для показа пулов, сгруппированных по Fee Tier"""
    try:
        # Получаем все пулы
        pools = await get_all_pools()
        
        if not pools:
            # Пытаемся обновить данные из адаптера
            await update_pools_from_adapter()
            pools = await get_all_pools()
        
        if not pools:
            await message.answer("❌ Пулы не найдены. Попробуйте обновить данные.")
            return
        
        # Группируем по fee_rate
        pools_by_tier = defaultdict(list)
        for pool in pools:
            fee_rate = getattr(pool, 'fee_rate', 0) or 0
            pools_by_tier[fee_rate].append(pool)
        
        # Сортируем пулы внутри каждого tier по TVL
        for fee_rate in pools_by_tier:
            pools_by_tier[fee_rate].sort(key=lambda p: p.tvl_usd, reverse=True)
        
        text = format_pools_by_fee_tier(dict(pools_by_tier))
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Обновить", callback_data="refresh_pools")
            ]
        ])
        
        await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Error in cmd_fee_tiers: {e}")
        await message.answer("❌ Произошла ошибка при получении пулов по Fee Tier.")


@router.callback_query(F.data == "refresh_pools")
async def callback_refresh_pools(callback: CallbackQuery):
    """Обновление списка пулов"""
    await callback.answer("Обновляю данные...")
    
    try:
        # Обновляем данные из адаптера
        await update_pools_from_adapter()
        
        # Получаем обновленный список
        pools = await get_top_pools(min_tvl=0.0, min_apr=0.0, limit=10)
        
        if not pools:
            await callback.message.edit_text("❌ Пулы не найдены после обновления.")
            return
        
        text = format_pools_list(pools, "📊 Топ 10 пулов по APR (обновлено):")
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Обновить", callback_data="refresh_pools"),
                InlineKeyboardButton(text="🔍 Фильтры", callback_data="filter_pools")
            ]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Error in callback_refresh_pools: {e}")
        await callback.message.edit_text("❌ Ошибка при обновлении данных.")


@router.callback_query(F.data == "filter_pools")
async def callback_filter_pools(callback: CallbackQuery):
    """Обработка фильтров"""
    await callback.answer()
    await callback.message.edit_text(
        "🔍 Фильтры пулов\n\n"
        "Используйте команды:\n"
        "/find [apr] - найти пулы с минимальным APR\n"
        "/pool <address> - показать конкретный пул\n"
        "/fee_tiers - показать пулы по Fee Tier\n"
        "Пример: /find 20 - найдет пулы с APR > 20%"
    )


async def update_pools_from_adapter():
    """Обновить пулы из адаптера"""
    try:
        adapter = HyperionAdapter()
        pools_data = await adapter.get_pools()
        
        for pool_data in pools_data:
            pool_dict = pool_data.to_dict()
            await upsert_pool(pool_dict)
        
        logger.info(f"Updated {len(pools_data)} pools from adapter")
        
    except Exception as e:
        logger.error(f"Error updating pools from adapter: {e}")
