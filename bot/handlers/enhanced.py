"""
Улучшенные handlers для бота с новым API и форматтером
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from collections import defaultdict
from typing import List, Dict
from loguru import logger

from bot.utils.hyperion_enhanced import HyperionAPI
from bot.utils.bluefin_enhanced import BluefinAPI
from bot.utils.telegram_formatter import TelegramFormatter


router = Router()

# Глобальные экземпляры API (с кэшированием)
api = HyperionAPI()
bluefin_api = BluefinAPI()
formatter = TelegramFormatter()


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    """Команда /stats - Market Overview"""
    try:
        msg = await message.answer("⏳ Загружаю данные...")
        
        pools = await api.get_all_pools()
        if not pools:
            await msg.edit_text("❌ Не удалось загрузить данные. Попробуйте позже.")
            return
        
        stats = api.get_market_stats(pools)
        text = formatter.format_market_overview(stats)
        
        # Создаем клавиатуру только с Refresh (главное меню теперь постоянное)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Refresh", callback_data="refresh_stats")]
        ])
        
        await msg.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Error in cmd_stats: {e}")
        await message.answer("❌ Произошла ошибка при получении статистики.")


@router.message(Command("pools"))
async def cmd_pools(message: Message):
    """Команда /pools - Все пулы (топ 10 по TVL)"""
    try:
        msg = await message.answer("⏳ Загружаю пулы...")
        
        pools = await api.get_all_pools()
        if not pools:
            await msg.edit_text("❌ Не удалось загрузить пулы.")
            return
        
        # Фильтруем и сортируем по TVL, лимит 10
        filtered_pools = api.filter_pools(pools, sort_by='tvl', limit=10)
        
        text = formatter.format_pools_table(filtered_pools, "📊 Top Pools by TVL")
        
        keyboard = _create_pools_keyboard()
        
        await msg.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Error in cmd_pools: {e}")
        await message.answer("❌ Произошла ошибка при получении пулов.")


@router.message(Command("farm"))
async def cmd_farm(message: Message):
    """Команда /farm - Пулы с farming"""
    try:
        msg = await message.answer("⏳ Загружаю пулы с farming...")
        
        pools = await api.get_all_pools()
        if not pools:
            await msg.edit_text("❌ Не удалось загрузить пулы.")
            return
        
        # Фильтруем только пулы с farming
        farm_pools = api.filter_pools(pools, has_farm=True, sort_by='tvl', limit=20)
        
        text = formatter.format_farm_pools(farm_pools)
        
        keyboard = _create_pools_keyboard()
        
        await msg.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Error in cmd_farm: {e}")
        await message.answer("❌ Произошла ошибка при получении пулов с farming.")




@router.message(Command("top"))
async def cmd_top(message: Message):
    """Команда /top [tvl|volume|apr|fees] - Топ по метрике"""
    try:
        args = message.text.split()[1:] if message.text else []
        sort_by = args[0] if args else 'tvl'
        
        if sort_by not in ['tvl', 'volume', 'apr', 'fees']:
            await message.answer(
                "❌ Неверный критерий сортировки.\n\n"
                "Использование: /top [tvl|volume|apr|fees]\n"
                "Пример: /top apr - топ по APR"
            )
            return
        
        msg = await message.answer("⏳ Загружаю пулы...")
        
        pools = await api.get_all_pools()
        if not pools:
            await msg.edit_text("❌ Не удалось загрузить пулы.")
            return
        
        # Сортируем по выбранному критерию
        sorted_pools = api.filter_pools(pools, sort_by=sort_by, limit=10)
        
        titles = {
            'tvl': '💰 Top Pools by TVL',
            'volume': '📊 Top Pools by Volume',
            'apr': '📈 Top Pools by APR',
            'fees': '💵 Top Pools by Fees'
        }
        
        text = formatter.format_pools_table(sorted_pools, titles.get(sort_by, "📊 Top Pools"))
        
        keyboard = _create_pools_keyboard()
        
        await msg.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Error in cmd_top: {e}")
        await message.answer("❌ Произошла ошибка при получении топ пулов.")


# Команда /search перенесена в bot/handlers/search.py для более продвинутого поиска через все блокчейны


@router.message(Command("pool"))
async def cmd_pool_detail(message: Message):
    """Команда /pool <token_a>-<token_b> - Детальная информация о пуле"""
    try:
        args = message.text.split()[1:] if message.text else []
        
        if not args:
            await message.answer(
                "❌ Укажите пару токенов\n\n"
                "Использование: /pool <token_a>-<token_b>\n"
                "Пример: /pool USDT-USDC"
            )
            return
        
        pool_id = args[0].strip()
        
        msg = await message.answer(f"🔍 Ищу пул {pool_id}...")
        
        pools = await api.get_all_pools()
        if not pools:
            await msg.edit_text("❌ Не удалось загрузить пулы.")
            return
        
        # Ищем пул по ID или по токенам
        pool = None
        for p in pools:
            if p.get("id") == pool_id:
                pool = p
                break
            else:
                token_a = p.get("token_a", "")
                token_b = p.get("token_b", "")
                if f"{token_a}-{token_b}" == pool_id or f"{token_b}-{token_a}" == pool_id:
                    pool = p
                    break
        
        if not pool:
            await msg.edit_text(f"❌ Пул {pool_id} не найден.")
            return
        
        text = formatter.format_pool_detail(pool)
        
        # Создаем клавиатуру с кнопками Refresh и ссылкой на сайт
        pool_id = pool.get("id", "")
        pool_url = _get_pool_url(pool_id) if pool_id else None
        
        keyboard_buttons = []
        if pool_url:
            keyboard_buttons.append([InlineKeyboardButton(text="🌐 Открыть на сайте", url=pool_url)])
        keyboard_buttons.append([InlineKeyboardButton(text="🔄 Refresh", callback_data=f"refresh_pool_{pool_id}")])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        await msg.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Error in cmd_pool_detail: {e}")
        await message.answer("❌ Произошла ошибка при получении информации о пуле.")


# Callback handlers
@router.callback_query(F.data == "refresh_stats")
async def callback_refresh_stats(callback: CallbackQuery):
    """Обновление статистики"""
    await callback.answer("Обновляю статистику...")
    
    try:
        pools = await api.get_all_pools(force_refresh=True)
        stats = api.get_market_stats(pools)
        text = formatter.format_market_overview(stats)
        
        # Создаем клавиатуру только с Refresh (главное меню теперь постоянное)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Refresh", callback_data="refresh_stats")]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error in callback_refresh_stats: {e}")
        await callback.answer("❌ Ошибка при обновлении", show_alert=True)


@router.callback_query(F.data == "pools_settings")
async def callback_pools_settings(callback: CallbackQuery):
    """Меню настроек пулов"""
    await callback.answer()
    
    try:
        text = (
            "⚙️ <b>Настройки пулов</b>\n\n"
            "Выберите способ сортировки или фильтр:\n\n"
            "• <b>Сортировка:</b> По TVL, Volume, APR, Fees\n"
            "• <b>Фильтр:</b> Только пулы с farming"
        )
        
        keyboard = _create_settings_keyboard()
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error in callback_pools_settings: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


@router.callback_query(F.data == "back_to_pools")
async def callback_back_to_pools(callback: CallbackQuery):
    """Вернуться к списку пулов из настроек"""
    await callback.answer()
    
    try:
        pools = await api.get_all_pools()
        filtered_pools = api.filter_pools(pools, sort_by='tvl', limit=10)
        
        text = formatter.format_pools_table(filtered_pools, "🏊 Hyperion Pools")
        keyboard = _create_pools_keyboard_with_links(filtered_pools, protocol_id="hyperion")
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error in callback_back_to_pools: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


@router.callback_query(F.data == "filter_farm")
async def callback_filter_farm(callback: CallbackQuery):
    """Фильтр по Farm"""
    await callback.answer("Показываю пулы с farming...")
    
    try:
        pools = await api.get_all_pools()
        filtered = api.filter_pools(pools, has_farm=True, sort_by='tvl', limit=20)
        
        text = formatter.format_farm_pools(filtered)
        keyboard = _create_pools_keyboard_with_links(filtered, protocol_id="hyperion")
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error in callback_filter_farm: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


@router.callback_query(F.data.startswith("sort_"))
async def callback_sort(callback: CallbackQuery):
    """Сортировка"""
    sort_by = callback.data.split("_")[-1]
    
    try:
        pools = await api.get_all_pools()
        sorted_pools = api.filter_pools(pools, sort_by=sort_by, limit=10)
        
        titles = {
            'tvl': '💰 Top Pools by TVL',
            'volume': '📊 Top Pools by Volume',
            'apr': '📈 Top Pools by APR',
            'fees': '💵 Top Pools by Fees'
        }
        
        text = formatter.format_pools_table(sorted_pools, titles.get(sort_by, "📊 Top Pools"))
        keyboard = _create_pools_keyboard_with_links(sorted_pools, protocol_id="hyperion")
        
        try:
            await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
            await callback.answer(f"Сортировка: {sort_by}")
        except Exception as edit_error:
            # Игнорируем ошибку "message is not modified" - это нормально, если данные не изменились
            error_str = str(edit_error)
            if "message is not modified" in error_str.lower():
                await callback.answer(f"Уже отсортировано по {sort_by}", show_alert=False)
            else:
                raise
    except Exception as e:
        logger.error(f"Error in callback_sort: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


@router.callback_query(F.data == "refresh_pools")
async def callback_refresh_pools(callback: CallbackQuery):
    """Обновление пулов"""
    await callback.answer("Обновляю пулы...")
    
    try:
        pools = await api.get_all_pools(force_refresh=True)
        filtered_pools = api.filter_pools(pools, sort_by='tvl', limit=10)
        
        text = formatter.format_pools_table(filtered_pools, "📊 Top Pools by TVL")
        keyboard = _create_pools_keyboard_with_links(filtered_pools, protocol_id="hyperion")
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error in callback_refresh_pools: {e}")
        await callback.answer("❌ Ошибка при обновлении", show_alert=True)


@router.callback_query(F.data.startswith("refresh_pool_"))
async def callback_refresh_pool(callback: CallbackQuery):
    """Обновление отдельного пула"""
    await callback.answer("Обновляю пул...")
    
    try:
        # Извлекаем pool_id из callback_data
        pool_id = callback.data.replace("refresh_pool_", "")
        
        pools = await api.get_all_pools(force_refresh=True)
        if not pools:
            await callback.answer("❌ Не удалось загрузить пулы", show_alert=True)
            return
        
        # Ищем пул по ID или по токенам
        pool = None
        for p in pools:
            if p.get("id") == pool_id:
                pool = p
                break
            else:
                token_a = p.get("token_a", "")
                token_b = p.get("token_b", "")
                if f"{token_a}-{token_b}" == pool_id or f"{token_b}-{token_a}" == pool_id:
                    pool = p
                    break
        
        if not pool:
            await callback.answer("❌ Пул не найден", show_alert=True)
            return
        
        text = formatter.format_pool_detail(pool)
        
        # Создаем клавиатуру с кнопками Refresh и ссылкой на сайт
        pool_url = _get_pool_url(pool_id) if pool_id else None
        
        keyboard_buttons = []
        if pool_url:
            keyboard_buttons.append([InlineKeyboardButton(text="🌐 Открыть на сайте", url=pool_url)])
        keyboard_buttons.append([InlineKeyboardButton(text="🔄 Refresh", callback_data=f"refresh_pool_{pool_id}")])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error in callback_refresh_pool: {e}")
        await callback.answer("❌ Ошибка при обновлении", show_alert=True)


def _get_pool_url(pool_id: str) -> str:
    """
    Генерирует URL для пула на сайте Hyperion DEX
    
    Args:
        pool_id: ID пула
        
    Returns:
        str: URL пула
    """
    return f"https://hyperion.xyz/pool/{pool_id}"


def _get_protocol_url(protocol_id: str) -> str:
    """
    Генерирует URL для главной страницы протокола
    
    Args:
        protocol_id: ID протокола (hyperion, bluefin)
        
    Returns:
        str: URL протокола
    """
    if protocol_id == 'hyperion':
        return "https://hyperion.xyz"
    elif protocol_id == 'bluefin':
        return "https://trade.bluefin.io"
    return ""


def _get_protocol_display_name(protocol_id: str) -> str:
    """
    Получить отображаемое имя протокола
    
    Args:
        protocol_id: ID протокола
        
    Returns:
        str: Отображаемое имя
    """
    names = {
        'hyperion': 'Hyperion',
        'bluefin': 'Bluefin'
    }
    return names.get(protocol_id, protocol_id.capitalize())


# Callback handlers для новой логики навигации
@router.callback_query(F.data == "select_blockchain_aptos")
async def callback_select_blockchain_aptos(callback: CallbackQuery):
    """Обработка выбора блокчейна Aptos - показать список протоколов с данными"""
    await callback.answer("Загружаю данные...")
    
    try:
        text = "🔷 <b>Aptos Blockchain</b>\n\n"
        text += "Выберите протокол для просмотра пулов:\n\n"
        
        # Загружаем данные Hyperion
        pools = await api.get_all_pools()
        hyperion_tvl = 0.0
        hyperion_volume = 0.0
        hyperion_fees = 0.0
        
        if pools:
            stats = api.get_market_stats(pools)
            hyperion_tvl = stats.total_value_locked
            hyperion_volume = stats.volume_24h
            hyperion_fees = sum(float(p.get("feesUSD", 0)) for p in pools)
        
        # Форматируем протоколы с данными
        text += "🌊 <b>Hyperion</b>\n"
        text += f"   💰 TVL: ${hyperion_tvl:,.2f}\n"
        text += f"   📈 Volume 24H: ${hyperion_volume:,.2f}\n"
        text += f"   💵 Fees 24H: ${hyperion_fees:,.2f}\n\n"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🌊 Hyperion", callback_data="select_protocol_hyperion")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_blockchains")]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error in callback_select_blockchain_aptos: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


@router.callback_query(F.data == "back_to_blockchains")
async def callback_back_to_blockchains(callback: CallbackQuery):
    """Обработка кнопки 'Назад' - вернуться к выбору блокчейна"""
    await callback.answer()
    
    try:
        text = (
            "🔷 <b>Выберите блокчейн</b>\n\n"
            "Доступные блокчейны:"
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔷 Aptos", callback_data="select_blockchain_aptos")],
            [InlineKeyboardButton(text="🔵 Sui", callback_data="select_blockchain_sui")]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error in callback_back_to_blockchains: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


@router.callback_query(F.data == "select_blockchain_sui")
async def callback_select_blockchain_sui(callback: CallbackQuery):
    """Обработка выбора блокчейна Sui - показать список протоколов с данными"""
    await callback.answer("Загружаю данные...")
    
    try:
        text = "🔵 <b>Sui Blockchain</b>\n\n"
        text += "Выберите протокол для просмотра пулов:\n\n"
        
        # Загружаем данные Bluefin Exchange (пулы ликвидности)
        pools = await bluefin_api.get_all_pools()
        bluefin_tvl = 0.0
        bluefin_volume = 0.0
        bluefin_fees = 0.0
        
        if pools:
            stats = bluefin_api.get_market_stats(pools)
            bluefin_tvl = stats.total_value_locked
            bluefin_volume = stats.total_volume_24h
            bluefin_fees = stats.total_fees_24h
        
        # Форматируем протоколы с данными
        text += "🐋 <b>Bluefin Exchange</b>\n"
        text += f"   💰 TVL: ${bluefin_tvl:,.2f}\n"
        text += f"   📈 Volume 24H: ${bluefin_volume:,.2f}\n"
        text += f"   💵 Fees 24H: ${bluefin_fees:,.2f}\n\n"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🐋 Bluefin Exchange", callback_data="select_protocol_bluefin")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_blockchains")]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error in callback_select_blockchain_sui: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


@router.callback_query(F.data == "select_protocol_bluefin")
async def callback_select_protocol_bluefin(callback: CallbackQuery):
    """Обработка выбора протокола Bluefin Exchange - показать пулы ликвидности"""
    await callback.answer("Загружаю пулы...")
    
    try:
        pools = await bluefin_api.get_all_pools()
        if not pools:
            await callback.message.edit_text("❌ Не удалось загрузить пулы.")
            return
        
        # Фильтруем и сортируем по TVL, лимит 10
        filtered_pools = bluefin_api.filter_pools(pools, sort_by='tvl', limit=10)
        
        text = formatter.format_bluefin_pools_table(filtered_pools, "🐋 Bluefin Pools")
        
        keyboard = _create_pools_keyboard_with_links(filtered_pools, protocol_id="bluefin")
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error in callback_select_protocol_bluefin: {e}")
        await callback.answer("❌ Ошибка при загрузке пулов", show_alert=True)


@router.callback_query(F.data == "select_protocol_hyperion")
async def callback_select_protocol_hyperion(callback: CallbackQuery):
    """Обработка выбора протокола Hyperion - сразу показываем пулы"""
    await callback.answer("Загружаю пулы...")
    
    try:
        pools = await api.get_all_pools()
        if not pools:
            await callback.message.edit_text("❌ Не удалось загрузить пулы.")
            return
        
        # Фильтруем и сортируем по TVL, лимит 10
        filtered_pools = api.filter_pools(pools, sort_by='tvl', limit=10)
        
        text = formatter.format_pools_table(filtered_pools, "🏊 Hyperion Pools")
        
        # Создаем клавиатуру с кнопкой перехода на сайт протокола
        keyboard = _create_pools_keyboard_with_links(filtered_pools, protocol_id="hyperion")
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error in callback_select_protocol_hyperion: {e}")
        await callback.answer("❌ Ошибка при загрузке пулов", show_alert=True)


@router.callback_query(F.data == "show_pools_hyperion")
async def callback_show_pools_hyperion(callback: CallbackQuery):
    """Обработка кнопки 'Показать пулы' - показать список пулов"""
    await callback.answer("Загружаю пулы...")
    
    try:
        pools = await api.get_all_pools()
        if not pools:
            await callback.message.edit_text("❌ Не удалось загрузить пулы.")
            return
        
        # Фильтруем и сортируем по TVL, лимит 10
        filtered_pools = api.filter_pools(pools, sort_by='tvl', limit=10)
        
        text = formatter.format_pools_table(filtered_pools, "🏊 Hyperion Pools")
        
        # Создаем клавиатуру с кнопкой перехода на сайт протокола
        keyboard = _create_pools_keyboard_with_links(filtered_pools, protocol_id="hyperion")
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error in callback_show_pools_hyperion: {e}")
        await callback.answer("❌ Ошибка при загрузке пулов", show_alert=True)


def _create_pools_keyboard() -> InlineKeyboardMarkup:
    """Создать простую клавиатуру для списка пулов"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔄 Обновить", callback_data="refresh_pools"),
            InlineKeyboardButton(text="⚙️ Настройки", callback_data="pools_settings")
        ],
        [
            InlineKeyboardButton(text="⬅️ Назад к протоколам", callback_data="select_blockchain_aptos")
        ]
    ])


def _create_pools_keyboard_with_links(pools: List[Dict], protocol_id: str = "hyperion") -> InlineKeyboardMarkup:
    """Создать клавиатуру с одной кнопкой для перехода на сайт протокола"""
    keyboard = []
    
    # Одна кнопка для перехода на сайт протокола
    protocol_url = _get_protocol_url(protocol_id)
    protocol_name = _get_protocol_display_name(protocol_id)
    
    if protocol_url:
        keyboard.append([
            InlineKeyboardButton(
                text=f"🌐 Перейти на {protocol_name}",
                url=protocol_url
            )
        ])
    
    # Навигационные кнопки - определяем callback_data в зависимости от протокола
    if protocol_id == "bluefin":
        refresh_callback = "refresh_bluefin_markets"
        settings_callback = "bluefin_settings"
        back_callback = "select_blockchain_sui"
    else:  # hyperion или другие
        refresh_callback = "refresh_pools"
        settings_callback = "pools_settings"
        back_callback = "select_blockchain_aptos"
    
    keyboard.append([
        InlineKeyboardButton(text="🔄 Обновить", callback_data=refresh_callback),
        InlineKeyboardButton(text="⚙️ Настройки", callback_data=settings_callback)
    ])
    keyboard.append([
        InlineKeyboardButton(text="⬅️ Назад к протоколам", callback_data=back_callback)
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def _create_settings_keyboard() -> InlineKeyboardMarkup:
    """Создать клавиатуру настроек с фильтрами и сортировкой"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💰 По TVL", callback_data="sort_tvl"),
            InlineKeyboardButton(text="📊 По Volume", callback_data="sort_volume")
        ],
        [
            InlineKeyboardButton(text="📈 По APR", callback_data="sort_apr"),
            InlineKeyboardButton(text="💵 По Fees", callback_data="sort_fees")
        ],
        [
            InlineKeyboardButton(text="🌾 Только Farm", callback_data="filter_farm")
        ],
        [
            InlineKeyboardButton(text="⬅️ Назад к пулам", callback_data="back_to_pools")
        ]
    ])




@router.callback_query(F.data == "refresh_bluefin_markets")
async def callback_refresh_bluefin_markets(callback: CallbackQuery):
    """Обновление пулов Bluefin"""
    await callback.answer("Обновляю пулы...")
    
    try:
        pools = await bluefin_api.get_all_pools(force_refresh=True)
        filtered_pools = bluefin_api.filter_pools(pools, sort_by='tvl', limit=10)
        
        text = formatter.format_bluefin_pools_table(filtered_pools, "🐋 Bluefin Pools")
        keyboard = _create_pools_keyboard_with_links(filtered_pools, protocol_id="bluefin")
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error in callback_refresh_bluefin_markets: {e}")
        await callback.answer("❌ Ошибка при обновлении", show_alert=True)

