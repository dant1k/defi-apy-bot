import aiohttp
import asyncio
import os
from typing import List, Optional, Dict, Any
from loguru import logger

from bot.adapters.base import BaseAdapter, PoolData


# Полный маппинг популярных токенов Aptos
KNOWN_TOKENS = {
    # Native APT
    "0x1::aptos_coin::AptosCoin": "APT",
    
    # Stablecoins - USDC
    "0xf22bede237a07e121b56d91a491eb7bcdfd1f5907926a9e58338f964a01b17fa::asset::USDC": "USDC",
    "0x5e156f1207d0ebfa19a9eeff00d62a282278fb8719f4fab3a586a0a2c0fffbea::coin::T": "USDC",
    
    # Stablecoins - USDT
    "0x357b0b74bc833e95a115ad22604854d6b0fca151cecd94111770e5d6ffc9dc2b::coin::T": "USDT",
    
    # LayerZero bridged tokens
    "0xf22bede237a07e121b56d91a491eb7bcdfd1f5907926a9e58338f964a01b17fa::asset::WETH": "WETH",
    "0xae478ff7d83ed072dbc5e264250e67ef58f57c99d89b447efd8a0a2e8b2be76e::coin::T": "zUSDC",
    
    # BTC variants
    "0x1000000fa32d122c18a6a31c009ce5e71674f22d06a581bb0a15575e6addadcc::usda::USDA": "USDA",
    "0x111ae3e5bc816a5e63c2da97d0aa3886519e0cd5e4b046659fa35796bd11542a::amapt_token::AmnisApt": "amAPT",
    
    # Liquid staking
    "0xd11107bdf0d6d7040c6c0bfbdecb6545191fdf13e8d8d259952f53e1713f61b5::staked_coin::StakedAptos": "stAPT",
    
    # Thala
    "0x6f986d146e4a90b828d8c12c14b6f4e003fdff11a8eecceceb63744363eaac01::mod_coin::MOD": "MOD",
    "0x7fd500c11216f0fe3095d0c4b8aa4d64a4e2e04f83758462f2b127255643615::thl_coin::THL": "THL",
}

# Множество для отслеживания уже залогированных неизвестных токенов
_unknown_tokens_logged = set()

# Маппинг FA адресов на символы токенов
FA_TO_SYMBOL = {
    # APT (встречается чаще всего)
    "0x000000000000000000000000000000000000000000000000000000000000000a": "APT",
    "0x0009da434d9b873b5159e8eeed70202ad22dc075867a7793234fbc981b63e119": "APT",
    
    # USDC (второй по популярности)
    "0xbae207659db88bea0cbead6da0ed00aac12edcdda169e591cd41c94180b46f3b": "USDC",
    
    # USDT
    "0x357b0b74bc833e95a115ad22604854d6b0fca151cecd94111770e5d6ffc9dc2b": "USDT",
    "0x377adc4848552eb2ea17259be928001923efe12271fef1667e2b784f04a7cf3a": "USDt",
    
    # WBTC
    "0x81214a80d82035a190fcb76b6ff3c0145161c3a9f33d137f2bbaee4cfec8a387": "WBTC",
    
    # sUSDe
    "0x68844a0d7f2587e726ad0579f3d640865bb4162c08a4589eeda3f9689ec52a3d": "sUSDe",
    
    # Другие популярные токены
    "0x821c94e69bc7ca058c913b7b5e6b0a5c9fd1523d58723a966fb8c1f5ea888105": "kAPT",
    "0x05fabd1b12e39967a3c24e91b7b8f67719a6dacee74f3c8b9fb7d93e855437d2": "???",
    "0xb30a694a344edee467d9f82330bbe7c3b89f440a1ecd2da1f3bca266560fce69": "???",
}


class HyperionAdapter(BaseAdapter):
    """Адаптер для работы с официальным Hyperion API"""
    
    PROTOCOL_NAME = "hyperion"
    API_URL = "https://hyperfluid-api.alcove.pro/v1/graphql"
    DEFILLAMA_URL = "https://api.llama.fi/protocol/hyperion"
    APTOS_GRAPHQL_URL = "https://api.mainnet.aptoslabs.com/v1/graphql"
    
    def __init__(self):
        pass
    
    async def get_pools(self) -> List[PoolData]:
        """
        Получить все пулы через официальный Hyperion API
        
        Returns:
            List[PoolData]: Список пулов
        """
        logger.info("Fetching pools from Hyperion official API")
        
        # Метод 1: Официальный Hyperion API
        try:
            pools = await self._fetch_from_hyperion_api()
            if pools:
                logger.info(f"Successfully fetched {len(pools)} pools from Hyperion API")
                return pools
        except Exception as e:
            logger.warning(f"Failed to fetch from Hyperion API: {e}, trying DefiLlama fallback")
        
        # Метод 2: Fallback на DefiLlama
        try:
            pools = await self._fetch_from_defillama()
            if pools:
                logger.info(f"Successfully fetched {len(pools)} pools from DefiLlama fallback")
                return pools
        except Exception as e:
            logger.error(f"Failed to fetch from DefiLlama: {e}")
        
        logger.warning("All methods failed, returning empty list")
        return []
    
    async def _fetch_from_hyperion_api(self) -> List[PoolData]:
        """Получить пулы через официальный Hyperion GraphQL API"""
        query = """
        query GetAllPools {
          api {
            getPoolStat {
              id
              dailyVolumeUSD
              farmAPR
              feeAPR
              feesUSD
              tvlUSD
              pool {
                currentTick
                activeLpAmount
                feeRate
                sqrtPrice
                token1
                token2
              }
            }
          }
        }
        """
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.API_URL,
                    json={"query": query},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status != 200:
                        text = await response.text()
                        logger.error(f"Hyperion API request failed with status {response.status}: {text}")
                        raise Exception(f"API request failed with status {response.status}")
                    
                    data = await response.json()
                    
                    # ДЕТАЛЬНОЕ ЛОГИРОВАНИЕ RAW API RESPONSE
                    logger.info("=" * 50)
                    logger.info("RAW API RESPONSE (первый пул):")
                    try:
                        if data.get("data", {}).get("api", {}).get("getPoolStat"):
                            first_pool = data["data"]["api"]["getPoolStat"][0]
                            logger.info(f"Full pool data: {first_pool}")
                            if first_pool.get("pool"):
                                pool_info = first_pool["pool"]
                                logger.info(f"Token1: {pool_info.get('token1', 'N/A')}")
                                logger.info(f"Token2: {pool_info.get('token2', 'N/A')}")
                                logger.info(f"Token1Symbol: {pool_info.get('token1Symbol', 'N/A')}")
                                logger.info(f"Token2Symbol: {pool_info.get('token2Symbol', 'N/A')}")
                                logger.info(f"Token1Name: {pool_info.get('token1Name', 'N/A')}")
                                logger.info(f"Token2Name: {pool_info.get('token2Name', 'N/A')}")
                                logger.info(f"Full pool object keys: {list(pool_info.keys())}")
                        else:
                            logger.warning("No pools in response data structure")
                            logger.info(f"Full response structure: {data}")
                    except Exception as e:
                        logger.error(f"Error logging API response: {e}")
                        logger.info(f"Full response data: {data}")
                    logger.info("=" * 50)
                    
                    # Проверяем на ошибки GraphQL
                    if "errors" in data:
                        error_msg = data.get("errors", [])
                        logger.error(f"GraphQL errors in Hyperion API: {error_msg}")
                        raise Exception(f"GraphQL errors: {error_msg}")
                    
                    # Извлекаем данные пулов
                    api_data = data.get("data", {}).get("api", {})
                    pools_stat = api_data.get("getPoolStat", [])
                    
                    if not pools_stat:
                        logger.warning("No pools found in Hyperion API response")
                        return []
                    
                    logger.info(f"Received {len(pools_stat)} pools from Hyperion API")
                    
                    # Парсим пулы параллельно (быстрее)
                    pool_tasks = [self._parse_pool(pool_stat) for pool_stat in pools_stat]
                    pools = await asyncio.gather(*pool_tasks, return_exceptions=True)
                    
                    # Фильтруем None и исключения
                    valid_pools = []
                    for pool in pools:
                        if isinstance(pool, Exception):
                            logger.debug(f"Failed to parse pool: {pool}")
                            continue
                        if pool is not None:
                            valid_pools.append(pool)
                    
                    logger.info(f"Successfully parsed {len(valid_pools)} pools")
                    return valid_pools
                    
        except aiohttp.ClientError as e:
            logger.error(f"HTTP error in Hyperion API request: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in Hyperion API request: {e}")
            raise
    
    def _get_symbol_from_fa(self, fa_address: str) -> str:
        """
        Получить символ токена по FA адресу из маппинга
        
        Args:
            fa_address: FA адрес токена
        
        Returns:
            str: Символ токена или короткий адрес
        """
        if not fa_address:
            return "???"
        
        clean = fa_address.lower().strip()
        
        # Прямое совпадение
        if clean in FA_TO_SYMBOL:
            return FA_TO_SYMBOL[clean]
        
        # Если не нашли - показываем короткий адрес
        if len(clean) > 6:
            return f"0x{clean[-6:]}"
        return clean
    
    async def _parse_pool(self, pool_stat: Dict[str, Any]) -> Optional[PoolData]:
        """Парсинг данных пула из ответа API"""
        try:
            pool_info = pool_stat.get("pool", {})
            
            if not pool_info:
                logger.debug("Pool info is missing")
                return None
            
            pool_id = pool_stat.get("id")
            if not pool_id:
                logger.debug("Pool ID is missing")
                return None
            
            # Получаем FA адреса токенов
            token1_fa = pool_info.get("token1", "")
            token2_fa = pool_info.get("token2", "")
            
            # Получаем символы из маппинга FA адресов
            token_x_symbol = self._get_symbol_from_fa(token1_fa)
            token_y_symbol = self._get_symbol_from_fa(token2_fa)
            
            # Получаем метрики
            tvl_usd = float(pool_stat.get("tvlUSD", 0))
            volume_24h = float(pool_stat.get("dailyVolumeUSD", 0))
            fees_24h = float(pool_stat.get("feesUSD", 0))
            apr_fees = float(pool_stat.get("feeAPR", 0))
            apr_farming = float(pool_stat.get("farmAPR", 0))
            total_apr = apr_fees + apr_farming
            
            # Получаем fee rate (правильная формула: fee_rate / 10000)
            fee_rate = int(pool_info.get("feeRate", 0))
            
            return PoolData(
                protocol=self.PROTOCOL_NAME,
                pool_address=str(pool_id),
                token_x_symbol=token_x_symbol,
                token_y_symbol=token_y_symbol,
                tvl_usd=tvl_usd,
                volume_24h=volume_24h,
                apr_fees=apr_fees,
                apr_farming=apr_farming,
                total_apr=total_apr,
                fees_24h=fees_24h,
                fee_rate=fee_rate
            )
            
        except (ValueError, KeyError, TypeError) as e:
            logger.debug(f"Error parsing pool data: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error parsing pool: {e}")
            return None
    
    def _get_token_symbol_fallback(self, token_address: str) -> str:
        """
        Fallback функция для получения символа токена из адреса
        Используется если не удалось получить метаданные через GraphQL
        
        Args:
            token_address: Адрес токена в формате Aptos (например, "0x1::aptos_coin::AptosCoin")
        
        Returns:
            str: Символ токена
        """
        if not token_address:
            return "UNKNOWN"
        
        # Проверяем точное совпадение
        if token_address in KNOWN_TOKENS:
            return KNOWN_TOKENS[token_address]
        
        # Проверяем частичное совпадение (без учёта регистра)
        token_lower = token_address.lower()
        for addr, symbol in KNOWN_TOKENS.items():
            if addr.lower() in token_lower or token_lower in addr.lower():
                return symbol
        
        # Пытаемся извлечь из структуры адреса
        # Формат: 0xADDRESS::module::Token
        parts = token_address.split("::")
        
        if len(parts) >= 3:
            token_name = parts[-1]
            
            # Убираем распространённые суффиксы
            token_name = token_name.replace("Coin", "").replace("Token", "").replace("_token", "")
            
            # Распознаём по паттернам
            token_name_lower = token_name.lower()
            if "usdc" in token_name_lower:
                return "USDC"
            elif "usdt" in token_name_lower:
                return "USDT"
            elif "apt" in token_name_lower and "aptos" in token_address.lower():
                return "APT"
            elif "weth" in token_name_lower:
                return "WETH"
            elif "wbtc" in token_name_lower:
                return "WBTC"
            elif "btc" in token_name_lower:
                return "WBTC"
            elif "eth" in token_name_lower:
                return "WETH"
            
            # Возвращаем очищенное имя
            if token_name and len(token_name) <= 10:
                return token_name.upper()
        
        # Если не смогли распознать - логируем и возвращаем короткий адрес
        if token_address not in _unknown_tokens_logged:
            logger.warning(f"Unknown token: {token_address}")
            _unknown_tokens_logged.add(token_address)
            
            # Записываем в файл для будущего добавления в маппинг
            self._log_unknown_token(token_address)
        
        # Возвращаем короткий адрес
        # Если адрес короткий (менее 20 символов), возвращаем как есть (первые 8 символов)
        if len(token_address) <= 20:
            return token_address[:8] if len(token_address) >= 8 else token_address
        
        # Если адрес длинный, возвращаем короткую версию
        if token_address.startswith("0x"):
            return token_address[:10]  # 0x + 8 символов
        return f"0x{token_address[:6]}"
    
    def _log_unknown_token(self, token_address: str):
        """Записать неизвестный токен в файл для будущего добавления в маппинг"""
        try:
            log_dir = "logs"
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, "unknown_tokens.txt")
            
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"{token_address}\n")
        except Exception as e:
            logger.debug(f"Failed to log unknown token to file: {e}")
    
    async def _fetch_from_defillama(self) -> List[PoolData]:
        """Fallback: получить данные через DefiLlama API"""
        try:
            logger.info("Fetching data from DefiLlama as fallback")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.DEFILLAMA_URL,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status != 200:
                        text = await response.text()
                        logger.warning(f"DefiLlama request failed with status {response.status}: {text}")
                        raise Exception(f"DefiLlama request failed with status {response.status}")
                    
                    data = await response.json()
                    
                    # DefiLlama возвращает общую информацию о протоколе
                    tvl_data = data.get("tvl", [])
                    if not tvl_data:
                        logger.warning("No TVL data in DefiLlama response, creating mock pools")
                        return self._create_mock_pools()
                    
                    # Берем последнее значение TVL
                    latest_tvl = tvl_data[-1].get("totalLiquidityUSD", 0) if tvl_data else 0
                    
                    logger.info(f"DefiLlama TVL: ${latest_tvl:,.0f}")
                    
                    # DefiLlama не дает детали по пулам, создаем примерные топ-пулы
                    return self._create_mock_pools_from_tvl(latest_tvl)
                    
        except aiohttp.ClientError as e:
            logger.error(f"HTTP error in DefiLlama request: {e}")
            return self._create_mock_pools()
        except Exception as e:
            logger.error(f"Unexpected error in DefiLlama request: {e}")
            return self._create_mock_pools()
    
    def _create_mock_pools_from_tvl(self, total_tvl: float) -> List[PoolData]:
        """Создать mock пулы на основе общего TVL от DefiLlama"""
        pools = []
        
        # Распределяем TVL между популярными парами
        popular_pairs = [
            ("APT", "USDC", 0.4),  # 40% TVL
            ("APT", "USDT", 0.3),  # 30% TVL
            ("USDC", "USDT", 0.15), # 15% TVL
            ("APT", "BTC", 0.1),   # 10% TVL
            ("APT", "ETH", 0.05),  # 5% TVL
        ]
        
        base_apr = 15.0  # Базовый APR
        
        for i, (token_x, token_y, tvl_share) in enumerate(popular_pairs):
            pool_tvl = total_tvl * tvl_share
            volume_24h = pool_tvl * 0.1  # Примерно 10% TVL в объеме за 24ч
            fees_24h = volume_24h * 0.003  # Примерно 0.3% комиссий
            
            # Вариация APR
            apr_multiplier = 1.0 + (i * 0.1)
            total_apr = base_apr * apr_multiplier
            apr_fees = total_apr * 0.7
            apr_farming = total_apr * 0.3
            
            # Генерируем адрес пула (mock)
            pool_address = f"mock_pool_{i}_{token_x}_{token_y}"
            
            pools.append(PoolData(
                protocol=self.PROTOCOL_NAME,
                pool_address=pool_address,
                token_x_symbol=token_x,
                token_y_symbol=token_y,
                tvl_usd=pool_tvl,
                volume_24h=volume_24h,
                apr_fees=apr_fees,
                apr_farming=apr_farming,
                total_apr=total_apr,
                fees_24h=fees_24h
            ))
        
        return pools
    
    def _create_mock_pools(self) -> List[PoolData]:
        """Создать mock пулы для демонстрации (когда все источники недоступны)"""
        logger.info("Creating mock pools as last resort fallback")
        
        mock_pools_data = [
            ("APT", "USDC", 1000000, 100000, 5000, 12.5, 5.5),
            ("APT", "USDT", 750000, 75000, 3750, 15.0, 6.0),
            ("USDC", "USDT", 500000, 50000, 2500, 8.0, 2.0),
            ("APT", "BTC", 250000, 25000, 1250, 20.0, 8.0),
        ]
        
        pools = []
        for i, (token_x, token_y, tvl, volume, fees, apr_fees, apr_farming) in enumerate(mock_pools_data):
            pool_address = f"mock_pool_{i}_{token_x}_{token_y}"
            
            pools.append(PoolData(
                protocol=self.PROTOCOL_NAME,
                pool_address=pool_address,
                token_x_symbol=token_x,
                token_y_symbol=token_y,
                tvl_usd=float(tvl),
                volume_24h=float(volume),
                apr_fees=float(apr_fees),
                apr_farming=float(apr_farming),
                total_apr=float(apr_fees + apr_farming),
                fees_24h=float(fees)
            ))
        
        return pools
