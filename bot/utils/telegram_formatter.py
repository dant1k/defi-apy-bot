"""
Форматтер для Telegram сообщений
Соответствует формату из задания
"""
from typing import List, Dict
from bot.utils.hyperion_enhanced import MarketStats
from bot.utils.bluefin_enhanced import BluefinMarketStats
from bot.utils.fee_tier import get_fee_tier_description


class TelegramFormatter:
    """Класс для форматирования сообщений Telegram"""
    
    @staticmethod
    def format_market_overview(stats: MarketStats) -> str:
        """
        Форматировать Market Overview
        
        Args:
            stats: Статистика рынка
            
        Returns:
            str: Отформатированное сообщение
        """
        message = "📊 <b>Market Overview</b>\n\n"
        message += f"💰 <b>Total Value Locked</b>\n"
        message += f"${stats.total_value_locked:,.2f}\n\n"
        message += f"📈 <b>Cumulative Volume</b>\n"
        message += f"${stats.cumulative_volume:,.2f}\n\n"
        message += f"🔄 <b>24H Trading Volume</b>\n"
        message += f"${stats.volume_24h:,.2f}\n\n"
        message += f"⚡ <b>Capital Efficiency</b>\n"
        message += f"{stats.capital_efficiency:.1f}\n"
        
        return message
    
    @staticmethod
    def format_protocol_stats(tvl: float, volume_24h: float, fees_24h: float, protocol_name: str = "Hyperion") -> str:
        """
        Форматировать статистику протокола (TVL, Volume 24H, Fees 24H)
        
        Args:
            tvl: Total Value Locked
            volume_24h: Volume за 24 часа
            fees_24h: Fees за 24 часа
            protocol_name: Название протокола
            
        Returns:
            str: Отформатированное сообщение
        """
        message = f"📊 <b>{protocol_name} Protocol</b>\n\n"
        message += f"💰 <b>TVL</b>\n"
        message += f"${tvl:,.2f}\n\n"
        message += f"📈 <b>Volume 24H</b>\n"
        message += f"${volume_24h:,.2f}\n\n"
        message += f"💵 <b>Fees 24H</b>\n"
        message += f"${fees_24h:,.2f}\n"
        
        return message
    
    @staticmethod
    def format_pools_table(pools: List[Dict], title: str = "📊 Top Pools") -> str:
        """
        Форматировать таблицу пулов
        
        Args:
            pools: Список пулов
            title: Заголовок
            
        Returns:
            str: Отформатированное сообщение
        """
        if not pools:
            return "❌ No active pools found"
        
        message = f"<b>{title}</b>\n\n"
        
        for i, pool in enumerate(pools[:10], 1):  # Топ 10
            # ✅ Проверка на валидность данных
            tvl = float(pool.get("tvlUSD", 0))
            if tvl <= 0:
                continue
            
            token_a = pool.get("token_a", "???")
            token_b = pool.get("token_b", "???")
            pair_name = f"{token_a}-{token_b}"
            fee_tier = pool.get("fee_tier_display", "N/A")
            
            volume = float(pool.get("dailyVolumeUSD", 0))
            fees = float(pool.get("feesUSD", 0))
            total_apr = float(pool.get("total_apr", 0))
            fee_apr = float(pool.get("feeAPR", 0))
            farm_apr = float(pool.get("farmAPR", 0))
            
            # Формат с эмодзи
            message += f"{i}. <b>{pair_name}</b>\n"
            message += f"🎯 Fee Tier: {fee_tier}\n"
            message += f"💰 TVL: ${tvl:,.0f}\n"
            message += f"📊 Volume 24H: ${volume:,.0f}\n"
            message += f"💵 Fees 24H: ${fees:,.2f}\n"
            message += f"📈 APR: {total_apr:.2f}%\n"
            message += f"   ├─ Fee APR: {fee_apr:.2f}%\n"
            message += f"   └─ Farm APR: {farm_apr:.2f}%\n\n"
        
        return message.strip()
    
    @staticmethod
    def format_pool_detail(pool: Dict) -> str:
        """
        Форматировать детальную информацию о пуле
        
        Args:
            pool: Данные пула
            
        Returns:
            str: Отформатированное сообщение
        """
        token_a = pool.get("token_a", "???")
        token_b = pool.get("token_b", "???")
        fee_tier_display = pool.get("fee_tier_display", "N/A")
        fee_rate = pool.get("fee_tier_value", 0)
        
        tvl = float(pool.get("tvlUSD", 0))
        volume = float(pool.get("dailyVolumeUSD", 0))
        fees = float(pool.get("feesUSD", 0))
        total_apr = float(pool.get("total_apr", 0))
        fee_apr = float(pool.get("feeAPR", 0))
        farm_apr = float(pool.get("farmAPR", 0))
        
        pool_info = pool.get("pool", {})
        active_lp = int(pool_info.get("activeLpAmount", 0) or 0)
        current_tick = int(pool_info.get("currentTick", 0) or 0)
        
        # Определяем описание для fee tier
        fee_tier_desc = get_fee_tier_description(fee_rate) if fee_rate else "N/A"
        category_desc = "Best for stablecoin pairs" if fee_rate == 100 else "Standard pairs"
        
        message = f"🏊‍♂️ <b>{token_a} - {token_b}</b>\n\n"
        message += f"🎯 Fee Tier: {fee_tier_display}\n"
        message += f"   └─ {category_desc}\n\n"
        message += f"💰 <b>Total Value Locked</b>\n"
        message += f"${tvl:,.2f}\n\n"
        message += f"📊 <b>Volume (24H)</b>\n"
        message += f"${volume:,.2f}\n\n"
        message += f"💵 <b>Fees (24H)</b>\n"
        message += f"${fees:,.2f}\n\n"
        message += f"📈 <b>Total APR: {total_apr:.2f}%</b>\n\n"
        message += f"📈 APR Breakdown:\n"
        message += f"   ├─ Fee APR: {fee_apr:.2f}%\n"
        message += f"   └─ Farm APR: {farm_apr:.2f}%\n\n"
        message += f"🔢 Active LP: {active_lp:,}\n"
        message += f"📍 Current Tick: {current_tick:,}\n"
        
        return message
    
    @staticmethod
    def format_bluefin_protocol_stats(
        tvl: float, 
        volume_24h: float, 
        fees_24h: float, 
        pools_count: int,
        protocol_name: str = "Bluefin Exchange"
    ) -> str:
        """
        Форматировать статистику протокола Bluefin (TVL, Volume 24H, Fees 24H)
        
        Args:
            tvl: Total Value Locked
            volume_24h: Volume за 24 часа
            fees_24h: Fees за 24 часа
            pools_count: Количество активных пулов
            protocol_name: Название протокола
            
        Returns:
            str: Отформатированное сообщение
        """
        message = f"🐋 <b>{protocol_name}</b>\n\n"
        message += f"💰 <b>TVL</b>\n"
        message += f"${tvl:,.2f}\n\n"
        message += f"📈 <b>Volume 24H</b>\n"
        message += f"${volume_24h:,.2f}\n\n"
        message += f"💵 <b>Fees 24H</b>\n"
        message += f"${fees_24h:,.2f}\n\n"
        message += f"🔢 <b>Active Pools</b>\n"
        message += f"{pools_count}\n"
        
        return message
    
    @staticmethod
    def format_bluefin_pools_table(pools: List[Dict], title: str = "🐋 Bluefin Pools") -> str:
        """
        Форматировать таблицу пулов Bluefin
        
        Args:
            pools: Список пулов
            title: Заголовок
            
        Returns:
            str: Отформатированное сообщение
        """
        if not pools:
            return "❌ No active pools found"
        
        message = f"<b>{title}</b>\n\n"
        
        for i, pool in enumerate(pools[:10], 1):  # Топ 10
            # ✅ Проверка на валидность данных
            tvl = float(pool.get("tvlUSD", 0))
            if tvl <= 0:
                continue
            
            token_a = pool.get("token_a", "???")
            token_b = pool.get("token_b", "???")
            pair_name = f"{token_a}-{token_b}"
            fee_tier = pool.get("fee_tier_display", "N/A")
            
            volume = float(pool.get("dailyVolumeUSD", 0))
            fees = float(pool.get("feesUSD", 0))
            total_apr = float(pool.get("total_apr", 0))
            fee_apr = float(pool.get("feeAPR", 0))
            farm_apr = float(pool.get("farmAPR", 0))
            
            # Формат с эмодзи (аналогично Hyperion)
            message += f"{i}. <b>{pair_name}</b>\n"
            message += f"🎯 Fee Tier: {fee_tier}\n"
            message += f"💰 TVL: ${tvl:,.0f}\n"
            message += f"📊 Volume 24H: ${volume:,.0f}\n"
            message += f"💵 Fees 24H: ${fees:,.2f}\n"
            message += f"📈 APR: {total_apr:.2f}%\n"
            message += f"   ├─ Fee APR: {fee_apr:.2f}%\n"
            message += f"   └─ Farm APR: {farm_apr:.2f}%\n\n"
        
        return message.strip()
    
    @staticmethod
    def format_bluefin_market_detail(market: Dict) -> str:
        """
        Форматировать детальную информацию о рынке Bluefin
        
        Args:
            market: Данные рынка
            
        Returns:
            str: Отформатированное сообщение
        """
        symbol = market.get("symbol", "UNKNOWN")
        base_symbol = market.get("base_symbol", symbol.split('-')[0] if '-' in symbol else symbol)
        
        price = float(market.get("price", 0))
        volume = float(market.get("volume_24h", 0))
        oi = float(market.get("open_interest", 0))
        funding_rate = float(market.get("funding_rate_percent", 0))
        funding_24h = float(market.get("funding_24h", 0))
        
        # Дополнительные данные из исходного market
        high_24h = float(market.get("high24h", market.get("high", 0)))
        low_24h = float(market.get("low24h", market.get("low", 0)))
        change_24h = float(market.get("change24h", market.get("change", 0)))
        
        message = f"🐋 <b>{symbol}</b>\n\n"
        message += f"💰 <b>Price</b>\n"
        message += f"${price:,.2f}\n\n"
        
        if change_24h != 0:
            change_emoji = "📈" if change_24h > 0 else "📉"
            message += f"{change_emoji} <b>24H Change</b>\n"
            message += f"{change_24h:+.2f}%\n\n"
        
        message += f"📊 <b>Volume (24H)</b>\n"
        message += f"${volume:,.2f}\n\n"
        message += f"📈 <b>Open Interest</b>\n"
        message += f"${oi:,.2f}\n\n"
        message += f"💵 <b>Funding Rate</b>\n"
        message += f"{funding_rate:.4f}%\n\n"
        message += f"💵 <b>Funding (24H)</b>\n"
        message += f"${funding_24h:,.2f}\n\n"
        
        if high_24h > 0 and low_24h > 0:
            message += f"📊 <b>24H Range</b>\n"
            message += f"High: ${high_24h:,.2f}\n"
            message += f"Low: ${low_24h:,.2f}\n"
        
        return message
    
    @staticmethod
    def format_farm_pools(pools: List[Dict]) -> str:
        """
        Форматировать пулы с farming
        
        Args:
            pools: Список пулов с farming
            
        Returns:
            str: Отформатированное сообщение
        """
        return TelegramFormatter.format_pools_table(
            pools,
            "🌾 Pools with Farming"
        )
    
    @staticmethod
    def format_pools_by_fee_tier(pools_by_tier: Dict[int, List[Dict]]) -> str:
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
        
        message = "📊 <b>Pools by Fee Tier</b>\n\n"
        
        # Сортируем по fee_rate
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
            message += f"   Pools: {len(pools)}\n\n"
        
        return message

