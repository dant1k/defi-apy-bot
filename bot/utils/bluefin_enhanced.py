"""
API класс для работы с Bluefin Exchange API - Liquidity Pools
Включает кэширование, обогащение данных и Market Stats
"""
import aiohttp
import time
from dataclasses import dataclass
from typing import List, Dict, Optional
from loguru import logger

from bot.utils.fee_tier import format_fee_tier


@dataclass
class BluefinMarketStats:
    """Статистика рынка Bluefin Exchange (для пулов)"""
    total_value_locked: float
    total_volume_24h: float
    total_fees_24h: float
    active_pools_count: int


class BluefinAPI:
    """Класс для работы с Bluefin Exchange API - Liquidity Pools"""
    
    # TODO: Нужно найти правильный endpoint для пулов ликвидности
    # Пока используем exchange API, возможно нужен другой endpoint
    API_BASE_URL = "https://api.sui-prod.bluefin.io/v1/exchange"
    CACHE_TTL = 60  # Кэш на 60 секунд
    
    def __init__(self):
        self._cache: Optional[List[Dict]] = None
        self._cache_timestamp: float = 0
    
    async def get_all_pools(self, force_refresh: bool = False) -> List[Dict]:
        """
        Получить все пулы ликвидности с кэшированием
        
        Args:
            force_refresh: Принудительно обновить кэш
            
        Returns:
            List[Dict]: Список обогащенных пулов
        """
        current_time = time.time()
        
        # Проверяем кэш
        if not force_refresh and self._cache and (current_time - self._cache_timestamp) < self.CACHE_TTL:
            logger.debug("Returning cached Bluefin pools")
            return self._cache
        
        try:
            # Получаем данные из API
            raw_pools = await self._fetch_pools_from_api()
            
            # Фильтрация активных пулов (с TVL > 0 и Volume > 0)
            active_pools = [
                p for p in raw_pools 
                if float(p.get('tvlUSD', p.get('tvl', 0))) > 0
                and float(p.get('volume24h', p.get('volume', 0))) > 0
            ]
            logger.info(f"Filtered {len(active_pools)} active pools from {len(raw_pools)} total")
            
            # Обогащаем данные только для активных пулов
            enriched_pools = [self._enrich_pool(pool) for pool in active_pools]
            
            # Сохраняем в кэш
            self._cache = enriched_pools
            self._cache_timestamp = current_time
            
            logger.info(f"Fetched and enriched {len(enriched_pools)} active pools")
            return enriched_pools
            
        except Exception as e:
            logger.error(f"Error fetching Bluefin pools: {e}")
            # Возвращаем старый кэш если есть
            if self._cache:
                logger.warning("Returning stale cache due to API error")
                return self._cache
            raise
    
    async def _fetch_pools_from_api(self) -> List[Dict]:
        """
        Получить сырые данные пулов из API
        
        ВАЖНО: Bluefin Exchange не предоставляет публичный API для пулов ликвидности.
        
        Возможные варианты получения данных:
        1. Через Sui GraphQL Indexer (чтение данных напрямую с блокчейна)
           URL: https://api.mainnet.sui.io/v1/graphql
        2. Через Bluefin SDK (Python/TypeScript клиенты)
           - Python: https://github.com/fireflyprotocol/bluefin-client-python-sui
           - TypeScript: https://github.com/fireflyprotocol/bluefin-v2-client-ts
        3. Через сторонние агрегаторы (GeckoTerminal, DefiLlama)
        4. Связаться с командой Bluefin для доступа к приватному API
        
        Пока возвращаем пустой список - требуется реализация одного из вариантов выше.
        """
        logger.warning(
            "Bluefin pools API: No public API endpoint found. "
            "Options: Sui Indexer, Bluefin SDK, or third-party aggregators."
        )
        # TODO: Реализовать получение данных через один из вариантов выше
        return []
    
    def _enrich_pool(self, pool: Dict) -> Dict:
        """
        Обогатить данные пула вычисляемыми полями
        
        Args:
            pool: Сырые данные пула из API
            
        Returns:
            Dict: Обогащенные данные
        """
        # Извлекаем основные данные (структура может отличаться в зависимости от API)
        pool_id = pool.get('id', pool.get('address', ''))
        token_a_symbol = pool.get('token0', pool.get('tokenA', {}).get('symbol', '???'))
        token_b_symbol = pool.get('token1', pool.get('tokenB', {}).get('symbol', '???'))
        
        tvl = float(pool.get('tvlUSD', pool.get('tvl', 0)))
        volume_24h = float(pool.get('volume24h', pool.get('volume24H', pool.get('volume', 0))))
        fees_24h = float(pool.get('fees24h', pool.get('fees24H', pool.get('fees', 0))))
        
        # Fee tier (Bluefin использует 0.01%, 0.05%, 0.20%, 1.00%)
        fee_rate = int(pool.get('feeRate', pool.get('fee', 0)))
        if fee_rate > 0 and fee_rate < 100:
            # Конвертируем из процентов (0.05 = 0.05%) в формат как у Hyperion (500 = 0.05%)
            fee_rate = int(fee_rate * 10000)
        
        # APR (если доступно)
        fee_apr = float(pool.get('feeAPR', pool.get('apr', 0)))
        farm_apr = float(pool.get('farmAPR', 0))
        total_apr = fee_apr + farm_apr
        
        # Обогащаем данные
        enriched = {
            **pool,  # Исходные данные
            'pool_address': pool_id,
            'token_a': token_a_symbol,
            'token_b': token_b_symbol,
            'tvlUSD': tvl,
            'dailyVolumeUSD': volume_24h,
            'feesUSD': fees_24h,
            'fee_tier_display': format_fee_tier(fee_rate),
            'fee_tier_value': fee_rate,
            'feeAPR': fee_apr,
            'farmAPR': farm_apr,
            'total_apr': total_apr,
            'has_farm': farm_apr > 0,
        }
        
        return enriched
    
    def get_market_stats(self, pools: List[Dict]) -> BluefinMarketStats:
        """
        Вычислить статистику рынка (для пулов)
        
        Args:
            pools: Список пулов
            
        Returns:
            BluefinMarketStats: Статистика рынка
        """
        if not pools:
            return BluefinMarketStats(
                total_value_locked=0.0,
                total_volume_24h=0.0,
                total_fees_24h=0.0,
                active_pools_count=0
            )
        
        total_tvl = sum(float(p.get("tvlUSD", 0)) for p in pools)
        total_volume = sum(float(p.get("dailyVolumeUSD", 0)) for p in pools)
        total_fees = sum(float(p.get("feesUSD", 0)) for p in pools)
        
        return BluefinMarketStats(
            total_value_locked=total_tvl,
            total_volume_24h=total_volume,
            total_fees_24h=total_fees,
            active_pools_count=len(pools)
        )
    
    def filter_pools(
        self,
        pools: List[Dict],
        min_tvl: float = 100000,
        min_volume: float = 50000,
        fee_tiers: Optional[List[int]] = None,
        has_farm: Optional[bool] = None,
        sort_by: str = 'tvl',
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        Фильтровать и сортировать пулы
        
        Args:
            pools: Список пулов
            min_tvl: Минимальный TVL (по умолчанию $100,000)
            min_volume: Минимальный Volume 24H (по умолчанию $50,000)
            fee_tiers: Список fee tiers для фильтрации
            has_farm: Фильтр по наличию farming (True/False/None)
            sort_by: Критерий сортировки (tvl|volume|apr|fees)
            limit: Максимум результатов
            
        Returns:
            List[Dict]: Отфильтрованные и отсортированные пулы
        """
        filtered = pools.copy()
        
        # Фильтруем по минимальному TVL
        filtered = [p for p in filtered if float(p.get("tvlUSD", 0)) >= min_tvl]
        
        # Фильтруем по минимальному Volume 24H
        filtered = [p for p in filtered if float(p.get("dailyVolumeUSD", 0)) >= min_volume]
        
        # Убираем пулы с нулевыми метриками
        filtered = [p for p in filtered if float(p.get("tvlUSD", 0)) > 0]
        
        # Фильтр по fee tiers
        if fee_tiers:
            filtered = [p for p in filtered if p.get("fee_tier_value") in fee_tiers]
        
        # Фильтр по farming
        if has_farm is not None:
            filtered = [p for p in filtered if p.get("has_farm") == has_farm]
        
        # Сортировка
        sort_keys = {
            'tvl': lambda p: float(p.get("tvlUSD", 0)),
            'volume': lambda p: float(p.get("dailyVolumeUSD", 0)),
            'apr': lambda p: float(p.get("total_apr", 0)),
            'fees': lambda p: float(p.get("feesUSD", 0)),
        }
        
        sort_key = sort_keys.get(sort_by, sort_keys['tvl'])
        filtered.sort(key=sort_key, reverse=True)
        
        # Лимит
        if limit:
            filtered = filtered[:limit]
        
        return filtered
