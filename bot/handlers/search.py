"""
Handlers для поиска пулов по токенам
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from loguru import logger

from bot.utils.token_search import token_search
from bot.utils.search_formatter import search_formatter


router = Router()


@router.message(F.text == "🔍 Поиск пулов")
async def search_command(message: Message):
    """Кнопка поиска пулов - показать меню"""
    
    await message.answer(
        """🔍 <b>Поиск пулов</b>

Введите токен для поиска:

<b>Примеры:</b>
• <code>APT</code> - все пулы с APT
• <code>USDC</code> - все пулы с USDC
• <code>APT/USDT</code> - конкретная пара

Поиск работает через все блокчейны и протоколы! 🌐""",
        parse_mode="HTML"
    )


@router.message(F.text.regexp(r'^[A-Za-z0-9]{2,10}(-|/)?[A-Za-z0-9]{0,10}$'))
async def process_search_query(message: Message):
    """Обрабатывает поисковый запрос (только текстовые сообщения, не команды)"""
    
    # Пропускаем команды - они обрабатываются отдельным обработчиком
    if message.text and message.text.startswith('/'):
        return
    
    query = message.text.strip()
    
    # Пропускаем кнопки меню
    menu_buttons = ["🔍 Поиск пулов", "🔷 Выбрать блокчейн", "🏠 Главное меню", "📚 Справка"]
    if query in menu_buttons:
        return
    
    query = query.upper()
    
    # Показываем индикатор загрузки
    msg = await message.answer("🔍 Ищу пулы...")
    
    try:
        # Выполняем поиск
        result = await token_search.search_token(query)
        
        if result.total_pools == 0:
            await msg.edit_text(
                f"❌ Пулы с <b>{query}</b> не найдены\n\n"
                f"Попробуйте другой токен или пару",
                parse_mode="HTML"
            )
            return
        
        # Форматируем результаты
        text = search_formatter.format_search_results(result)
        
        # Создаем клавиатуру с блокчейнами
        keyboard = []
        for chain in result.blockchains:
            keyboard.append([
                InlineKeyboardButton(
                    text=f"{chain.chain_emoji} {chain.chain_name} ({chain.pool_count})",
                    callback_data=f"search_chain_{query}_{chain.chain_id}"
                )
            ])
        
        keyboard.append([
            InlineKeyboardButton(
                text="🔄 Новый поиск",
                callback_data="new_search"
            )
        ])
        
        await msg.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        await msg.edit_text(
            "❌ Ошибка при поиске. Попробуйте еще раз.",
            parse_mode="HTML"
        )


@router.callback_query(F.data.startswith("search_chain_"))
async def show_blockchain_protocols(callback: CallbackQuery):
    """Показать протоколы для выбранного блокчейна"""
    await callback.answer()
    
    # Парсим callback_data: search_chain_APT_aptos
    parts = callback.data.split("_")
    if len(parts) < 4:
        await callback.answer("❌ Ошибка формата", show_alert=True)
        return
    
    token = parts[2]
    chain_id = "_".join(parts[3:])  # На случай если chain_id содержит подчеркивания
    
    try:
        # Повторяем поиск (из кэша будет быстро)
        result = await token_search.search_token(token)
        
        # Находим нужный блокчейн
        chain = next((c for c in result.blockchains if c.chain_id == chain_id), None)
        
        if not chain:
            await callback.answer("❌ Блокчейн не найден", show_alert=True)
            return
        
        # Форматируем
        text = search_formatter.format_blockchain_protocols(chain, token)
        
        # Клавиатура с протоколами
        keyboard = []
        for protocol in chain.protocols:
            keyboard.append([
                InlineKeyboardButton(
                    text=f"{protocol.protocol_emoji} {protocol.protocol_name} ({protocol.pool_count})",
                    callback_data=f"search_protocol_{token}_{chain_id}_{protocol.protocol_id}"
                )
            ])
        
        keyboard.append([
            InlineKeyboardButton(
                text="⬅️ Назад к блокчейнам",
                callback_data=f"search_back_{token}"
            ),
            InlineKeyboardButton(
                text="🔄 Новый поиск",
                callback_data="new_search"
            )
        ])
        
        await callback.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Error showing protocols: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


@router.callback_query(F.data.startswith("search_protocol_"))
async def show_protocol_pools(callback: CallbackQuery):
    """Показать пулы выбранного протокола"""
    await callback.answer()
    
    # Парсим: search_protocol_APT_aptos_hyperion
    parts = callback.data.split("_")
    if len(parts) < 5:
        await callback.answer("❌ Ошибка формата", show_alert=True)
        return
    
    token = parts[2]
    chain_id = parts[3]
    protocol_id = parts[4]
    
    try:
        # Получаем результаты
        result = await token_search.search_token(token)
        chain = next((c for c in result.blockchains if c.chain_id == chain_id), None)
        
        if not chain:
            await callback.answer("❌ Блокчейн не найден", show_alert=True)
            return
        
        protocol = next((p for p in chain.protocols if p.protocol_id == protocol_id), None)
        
        if not protocol:
            await callback.answer("❌ Протокол не найден", show_alert=True)
            return
        
        # Форматируем пулы
        text = search_formatter.format_protocol_pools(protocol, token)
        
        # Клавиатура
        keyboard = []
        
        # Одна кнопка для перехода на сайт протокола
        protocol_url = search_formatter.get_protocol_url(protocol_id)
        if protocol_url:
            protocol_name = protocol.protocol_name
            keyboard.append([
                InlineKeyboardButton(
                    text=f"🌐 Перейти на {protocol_name}",
                    url=protocol_url
                )
            ])
        
        # Навигационные кнопки
        keyboard.append([
            InlineKeyboardButton(
                text="⬅️ Назад к протоколам",
                callback_data=f"search_chain_{token}_{chain_id}"
            ),
            InlineKeyboardButton(
                text="🔄 Обновить",
                callback_data=callback.data
            )
        ])
        keyboard.append([
            InlineKeyboardButton(
                text="🔍 Новый поиск",
                callback_data="new_search"
            )
        ])
        
        await callback.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Error showing pools: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


@router.callback_query(F.data.startswith("search_back_"))
async def back_to_blockchains(callback: CallbackQuery):
    """Вернуться к списку блокчейнов"""
    await callback.answer()
    
    token = callback.data.replace("search_back_", "")
    
    try:
        # Повторяем поиск
        result = await token_search.search_token(token)
        
        if result.total_pools == 0:
            await callback.message.edit_text(
                f"❌ Пулы с <b>{token}</b> не найдены",
                parse_mode="HTML"
            )
            return
        
        # Форматируем результаты
        text = search_formatter.format_search_results(result)
        
        # Создаем клавиатуру с блокчейнами
        keyboard = []
        for chain in result.blockchains:
            keyboard.append([
                InlineKeyboardButton(
                    text=f"{chain.chain_emoji} {chain.chain_name} ({chain.pool_count})",
                    callback_data=f"search_chain_{token}_{chain.chain_id}"
                )
            ])
        
        keyboard.append([
            InlineKeyboardButton(
                text="🔄 Новый поиск",
                callback_data="new_search"
            )
        ])
        
        await callback.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error in back_to_blockchains: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


@router.callback_query(F.data == "new_search")
async def new_search(callback: CallbackQuery):
    """Новый поиск"""
    await callback.answer()
    
    text = """🔍 <b>Поиск пулов</b>

Введите токен для поиска:

<b>Примеры:</b>
• <code>APT</code> - все пулы с APT
• <code>USDC</code> - все пулы с USDC

Для поиска конкретной пары используйте команду:
<code>/search APT/USDT</code>

Поиск работает через все блокчейны и протоколы! 🌐"""
    
    await callback.message.edit_text(text, parse_mode="HTML")

