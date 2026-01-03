"""
Улучшенный API класс для работы с Hyperion GraphQL API
Включает кэширование, обогащение данных и Market Stats
"""
import aiohttp
import time
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from loguru import logger

from bot.utils.fee_tier import format_fee_tier, get_fee_tier_category, get_fee_tier_description


@dataclass
class MarketStats:
    """Статистика рынка"""
    total_value_locked: float
    cumulative_volume: float  # Исторический объем (пока используем 0, так как нет в API)
    volume_24h: float
    capital_efficiency: float


class HyperionAPI:
    """Класс для работы с Hyperion GraphQL API с кэшированием"""
    
    API_URL = "https://hyperfluid-api.alcove.pro/v1/graphql"
    CACHE_TTL = 60  # Кэш на 60 секунд
    
    def __init__(self):
        self._cache: Optional[List[Dict]] = None
        self._cache_timestamp: float = 0
    
    async def get_all_pools(self, force_refresh: bool = False) -> List[Dict]:
        """
        Получить все пулы с кэшированием
        
        Args:
            force_refresh: Принудительно обновить кэш
            
        Returns:
            List[Dict]: Список обогащенных пулов
        """
        current_time = time.time()
        
        # Проверяем кэш
        if not force_refresh and self._cache and (current_time - self._cache_timestamp) < self.CACHE_TTL:
            logger.debug("Returning cached pools")
            return self._cache
        
        try:
            # Получаем данные из API
            raw_pools = await self._fetch_pools_from_api()
            
            # ✅ Фильтрация пулов с минимальным TVL ($100,000) и Volume 24H ($50,000)
            active_pools = [
                p for p in raw_pools 
                if float(p.get('tvlUSD', 0)) >= 100000 
                and float(p.get('dailyVolumeUSD', 0)) >= 50000
            ]
            logger.info(f"Filtered {len(active_pools)} active pools from {len(raw_pools)} total (min TVL: $100,000, min Volume 24H: $50,000)")
            
            # Обогащаем данные только для активных пулов
            enriched_pools = [self._enrich_pool(pool) for pool in active_pools]
            
            # Сохраняем в кэш
            self._cache = enriched_pools
            self._cache_timestamp = current_time
            
            logger.info(f"Fetched and enriched {len(enriched_pools)} active pools")
            return enriched_pools
            
        except Exception as e:
            logger.error(f"Error fetching pools: {e}")
            # Возвращаем старый кэш если есть
            if self._cache:
                logger.warning("Returning stale cache due to API error")
                return self._cache
            raise
    
    async def _fetch_pools_from_api(self) -> List[Dict]:
        """Получить сырые данные из API"""
        query = """
        query GetAllPools {
          api {
            getPoolStat {
              id
              tvlUSD
              dailyVolumeUSD
              feesUSD
              feeAPR
              farmAPR
              pool {
                token1
                token2
                feeRate
                currentTick
                sqrtPrice
                activeLpAmount
              }
            }
          }
        }
        """
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.API_URL,
                json={"query": query},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status != 200:
                    text = await response.text()
                    logger.error(f"API request failed with status {response.status}: {text}")
                    raise Exception(f"API request failed with status {response.status}")
                
                data = await response.json()
                
                # Проверяем на ошибки GraphQL
                if "errors" in data:
                    error_msg = data.get("errors", [])
                    logger.error(f"GraphQL errors: {error_msg}")
                    raise Exception(f"GraphQL errors: {error_msg}")
                
                # Извлекаем данные пулов
                api_data = data.get("data", {}).get("api", {})
                pools_stat = api_data.get("getPoolStat", [])
                
                if not pools_stat:
                    logger.warning("No pools found in API response")
                    return []
                
                return pools_stat
    
    def _enrich_pool(self, pool: Dict) -> Dict:
        """
        Обогатить данные пула вычисляемыми полями
        
        Args:
            pool: Сырые данные пула из API
            
        Returns:
            Dict: Обогащенные данные
        """
        pool_info = pool.get("pool", {})
        fee_rate = int(pool_info.get("feeRate", 0))
        fee_apr = float(pool.get("feeAPR", 0))
        farm_apr = float(pool.get("farmAPR", 0))
        total_apr = fee_apr + farm_apr
        
        # ✅ ИСПРАВЛЕНО: Использовать token1 и token2 из pool данных
        token_a_address = pool_info.get("token1", "")
        token_b_address = pool_info.get("token2", "")
        
        # Получаем символы токенов через маппинг
        token_a = self._get_token_symbol(token_a_address)
        token_b = self._get_token_symbol(token_b_address)
        
        # Обогащаем данные
        enriched = {
            **pool,  # Исходные данные
            'token_a': token_a,
            'token_b': token_b,
            'fee_tier_display': format_fee_tier(fee_rate),
            'fee_tier_value': fee_rate,
            'total_apr': total_apr,
            'has_farm': farm_apr > 0,
            'apr_change': "+1" if total_apr > 100 else "0",
        }
        
        return enriched
    
    def _get_token_symbol(self, token_address: str) -> str:
        """
        Конвертирует адрес токена в символ
        
        Args:
            token_address: Адрес токена (полный или FA адрес)
            
        Returns:
            str: Символ токена или укороченный адрес
        """
        from bot.utils.token_registry import get_token_symbol
        return get_token_symbol(token_address)
    
    def get_market_stats(self, pools: List[Dict]) -> MarketStats:
        """
        Вычислить статистику рынка
        
        Args:
            pools: Список пулов
            
        Returns:
            MarketStats: Статистика рынка
        """
        if not pools:
            return MarketStats(
                total_value_locked=0.0,
                cumulative_volume=0.0,
                volume_24h=0.0,
                capital_efficiency=0.0
            )
        
        total_tvl = sum(float(p.get("tvlUSD", 0)) for p in pools)
        volume_24h = sum(float(p.get("dailyVolumeUSD", 0)) for p in pools)
        
        # Capital Efficiency = Volume 24H / TVL
        capital_efficiency = volume_24h / total_tvl if total_tvl > 0 else 0.0
        
        return MarketStats(
            total_value_locked=total_tvl,
            cumulative_volume=0.0,  # Исторический объем не доступен в API
            volume_24h=volume_24h,
            capital_efficiency=capital_efficiency
        )
    
    def filter_pools(
        self,
        pools: List[Dict],
        min_tvl: float = 100000,  # ✅ ИЗМЕНЕНО: Минимум $100,000 по умолчанию
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
            fee_tiers: Список fee tiers для фильтрации [100, 500, 2500, 10000]
            has_farm: Фильтр по наличию farming (True/False/None)
            sort_by: Критерий сортировки (tvl|volume|apr|fees)
            limit: Максимум результатов
            
        Returns:
            List[Dict]: Отфильтрованные и отсортированные пулы
        """
        filtered = pools.copy()
        
        # ✅ ВСЕГДА фильтруем пулы с низким TVL
        filtered = [p for p in filtered if float(p.get("tvlUSD", 0)) >= min_tvl]
        
        # ✅ Фильтруем пулы с низким Volume 24H ($50,000)
        filtered = [p for p in filtered if float(p.get("dailyVolumeUSD", 0)) >= 50000]
        
        # ✅ Убираем пулы с нулевыми метриками
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

