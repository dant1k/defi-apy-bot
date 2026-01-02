from typing import List
from bot.database.models import Pool
from bot.utils.fee_tier import format_fee_tier, get_fee_tier_description


def format_pool_message(pool: Pool) -> str:
    """Форматировать сообщение для одного пула"""
    pair_name = f"{pool.token_x_symbol}/{pool.token_y_symbol}"
    
    # Получаем fee tier информацию
    fee_rate = getattr(pool, 'fee_rate', 0) or 0
    fee_tier_desc = get_fee_tier_description(fee_rate) if fee_rate else "N/A"
    fees_24h = getattr(pool, 'fees_24h', 0.0) or 0.0
    
    message = f"🏊 <b>{pair_name}</b> ({pool.protocol})\n"
    message += f"📍 Адрес: <code>{pool.pool_address}</code>\n\n"
    message += f"💰 TVL: ${pool.tvl_usd:,.0f}\n"
    message += f"📊 Volume (24H): ${pool.volume_24h:,.0f}\n"
    message += f"💵 Fees (24H): ${fees_24h:,.0f}\n"
    message += f"📈 APR: <b>{pool.total_apr:.2f}%</b>\n"
    message += f"   ├─ Fee APR: {pool.apr_fees:.2f}%\n"
    message += f"   └─ Farm APR: {pool.apr_farming:.2f}%\n\n"
    message += f"🎯 Fee Tier: {fee_tier_desc}\n"
    
    return message


def format_pools_list(pools: List[Pool], header: str = "📊 Топ пулов по APR:") -> str:
    """Форматировать список пулов"""
    if not pools:
        return "❌ Пулы не найдены"
    
    message = f"{header}\n\n"
    
    for i, pool in enumerate(pools, 1):
        pair_name = f"{pool.token_x_symbol}/{pool.token_y_symbol}"
        
        # Форматируем адрес пула (короткий формат)
        pool_address_short = pool.pool_address
        if len(pool_address_short) > 20:
            pool_address_short = f"{pool_address_short[:8]}...{pool_address_short[-6:]}"
        
        # Используем реальные fees из БД
        fees_24h = getattr(pool, 'fees_24h', 0.0) or 0.0
        
        # Получаем fee tier информацию
        fee_rate = getattr(pool, 'fee_rate', 0) or 0
        fee_tier_display = format_fee_tier(fee_rate) if fee_rate else "N/A"
        fee_tier_desc = get_fee_tier_description(fee_rate) if fee_rate else "N/A"
        
        message += f"{i}. <b>{pair_name}</b> ({pool.protocol})\n"
        message += f"   🏊 Pool: <code>{pool_address_short}</code>\n"
        message += f"   💰 TVL: ${pool.tvl_usd:,.0f}\n"
        message += f"   📊 Volume (24H): ${pool.volume_24h:,.0f}\n"
        message += f"   💵 Fees (24H): ${fees_24h:,.0f}\n"
        message += f"   📈 APR: <b>{pool.total_apr:.2f}%</b>\n"
        message += f"      ├─ Fee APR: {pool.apr_fees:.2f}%\n"
        message += f"      └─ Farm APR: {pool.apr_farming:.2f}%\n"
        message += f"   🎯 Fee Tier: {fee_tier_desc}\n\n"
    
    return message


def format_pools_by_fee_tier(pools_by_tier: dict) -> str:
    """
    Форматировать пулы, сгруппированные по Fee Tier
    
    Args:
        pools_by_tier: Словарь {fee_rate: [pools]}
    
    Returns:
        str: Отформатированное сообщение
    """
    from bot.utils.fee_tier import get_fee_tier_category, format_fee_tier
    
    if not pools_by_tier:
        return "❌ Пулы не найдены"
    
    message = "📊 <b>Pools by Fee Tier:</b>\n\n"
    
    # Сортируем по fee_rate (от меньшего к большему)
    sorted_tiers = sorted(pools_by_tier.keys())
    
    for fee_rate in sorted_tiers:
        pools = pools_by_tier[fee_rate]
        if not pools:
            continue
        
        fee_percentage = format_fee_tier(fee_rate)
        category = get_fee_tier_category(fee_rate)
        
        descriptions = {
            "Ultra Low": "Stablecoins",
            "Low": "Correlated",
            "Medium": "Standard",
            "High": "Exotic",
        }
        description = descriptions.get(category, "")
        tier_label = f"{fee_percentage} - {category}"
        if description:
            tier_label += f" ({description})"
        
        message += f"🎯 <b>{tier_label}</b>\n"
        message += f"   Pools: {len(pools)}\n"
        
        # Показываем топ 5 пулов по TVL для каждого tier
        for pool in pools[:5]:
            pair_name = f"{pool.token_x_symbol}/{pool.token_y_symbol}"
            pool_address_short = pool.pool_address
            if len(pool_address_short) > 20:
                pool_address_short = f"{pool_address_short[:8]}...{pool_address_short[-6:]}"
            
            message += f"   • <code>{pool_address_short}</code> <b>{pair_name}</b>: ${pool.tvl_usd:,.0f} (APR: {pool.total_apr:.2f}%)\n"
        
        if len(pools) > 5:
            message += f"   ... и еще {len(pools) - 5} пулов\n"
        
        message += "\n"
    
    return message


def format_number(value: float) -> str:
    """Форматировать число с удобными единицами"""
    if value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f}B"
    elif value >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    elif value >= 1_000:
        return f"{value / 1_000:.2f}K"
    else:
        return f"{value:.2f}"
