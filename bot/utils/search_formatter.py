"""
Форматтеры для результатов поиска по токенам
"""
from typing import List, Tuple
from bot.utils.token_search import TokenSearchResult, BlockchainResult, ProtocolResult


class SearchFormatter:
    """Форматирование результатов поиска"""
    
    @staticmethod
    def format_search_results(result: TokenSearchResult) -> str:
        """Форматирует результаты поиска по токену"""
        
        if result.total_pools == 0:
            return f"❌ Пулы с <b>{result.token}</b> не найдены"
        
        msg = f"🔍 Найдено пулов с <b>{result.token}</b>: {result.total_pools}\n\n"
        msg += "📍 <b>Доступно на блокчейнах:</b>\n\n"
        
        for chain in result.blockchains:
            msg += f"{chain.chain_emoji} <b>{chain.chain_name}</b> ({chain.pool_count} pools)\n"
            msg += f"   💰 TVL: ${chain.total_tvl:,.0f}\n"
            
            # Показываем протоколы
            protocol_names = [f"{p.protocol_emoji} {p.protocol_name}" for p in chain.protocols]
            msg += f"   📊 Протоколы: {', '.join(protocol_names)}\n"
            
            # Лучший APR
            if chain.best_apr > 0:
                msg += f"   📈 Best APR: {chain.best_apr:.2f}%\n"
            
            msg += "\n"
        
        msg += "<i>Выберите блокчейн для просмотра протоколов:</i>"
        
        return msg.strip()
    
    @staticmethod
    def format_blockchain_protocols(
        chain: BlockchainResult, 
        token: str
    ) -> str:
        """Форматирует список протоколов для блокчейна"""
        
        msg = f"{chain.chain_emoji} <b>{chain.chain_name} - Пулы с {token}</b>\n\n"
        msg += f"Найдено: <b>{chain.pool_count}</b> пулов\n\n"
        msg += "📊 <b>По протоколам:</b>\n\n"
        
        for protocol in chain.protocols:
            msg += f"{protocol.protocol_emoji} <b>{protocol.protocol_name}</b>\n"
            msg += f"   • Pools: {protocol.pool_count}\n"
            msg += f"   • TVL: ${protocol.total_tvl:,.0f}\n"
            msg += f"   • Best APR: {protocol.best_apr:.2f}%\n"
            
            # Показываем топ-3 пула
            top_pools = sorted(protocol.pools, key=lambda x: float(x.get('total_apr', 0)), reverse=True)[:3]
            if top_pools:
                best = top_pools[0]
                pair_name = f"{best.get('token_a', '?')}-{best.get('token_b', '?')}"
                msg += f"   • Top: {pair_name} ({best.get('total_apr', 0):.1f}% APR)\n"
            
            msg += "\n"
        
        msg += "<i>Выберите протокол для просмотра пулов:</i>"
        
        return msg.strip()
    
    @staticmethod
    def format_protocol_pools(
        protocol: ProtocolResult,
        token: str
    ) -> str:
        """Форматирует список пулов протокола"""
        
        msg = f"{protocol.protocol_emoji} <b>{protocol.protocol_name} - {token} Pools</b>\n\n"
        msg += f"Топ {min(10, len(protocol.pools))} пулов:\n\n"
        
        for i, pool in enumerate(protocol.pools[:10], 1):
            token_a = pool.get('token_a', '???')
            token_b = pool.get('token_b', '???')
            pair_name = f"{token_a}-{token_b}"
            
            farm = " 🌾" if pool.get('has_farm') else ""
            fire = " 🔥" if pool.get('total_apr', 0) > 100 else ""
            
            # Поддержка разных форматов полей (Hyperion vs Bluefin)
            tvl = float(pool.get('tvlUSD', pool.get('tvl_usd', 0)))
            volume = float(pool.get('dailyVolumeUSD', pool.get('volume_24h', 0)))
            fees = float(pool.get('feesUSD', pool.get('fees_24h', 0)))
            apr = float(pool.get('total_apr', 0))
            
            msg += f"{i}. <b>{pair_name}</b>{farm}{fire}\n"
            msg += f"   💰 TVL: ${tvl:,.0f}\n"
            msg += f"   📊 Vol 24H: ${volume:,.0f} | "
            msg += f"💵 Fees 24H: ${fees:,.2f}\n"
            msg += f"   📈 APR: <b>{apr:.2f}%</b>\n\n"
        
        return msg.strip()
    
    @staticmethod
    def get_pool_url(pool_id: str, protocol_id: str) -> str:
        """
        Генерирует URL для пула на сайте протокола
        
        Args:
            pool_id: ID пула
            protocol_id: ID протокола (hyperion, bluefin)
            
        Returns:
            str: URL пула или пустая строка если не поддерживается
        """
        if protocol_id == 'hyperion':
            # Hyperion DEX на Aptos
            return f"https://hyperion.xyz/pool/{pool_id}"
        elif protocol_id == 'bluefin':
            # TODO: Добавить URL для Bluefin, когда будет известен формат
            return ""
        return ""
    
    @staticmethod
    def get_protocol_url(protocol_id: str) -> str:
        """
        Генерирует URL для главной страницы протокола
        
        Args:
            protocol_id: ID протокола (hyperion, bluefin)
            
        Returns:
            str: URL протокола или пустая строка если не поддерживается
        """
        if protocol_id == 'hyperion':
            return "https://hyperion.xyz"
        elif protocol_id == 'bluefin':
            return "https://trade.bluefin.io"
        return ""


# Singleton
search_formatter = SearchFormatter()

