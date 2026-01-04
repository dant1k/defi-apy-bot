"""
Движок поиска по токенам через все блокчейны и протоколы
"""
from typing import List, Dict, Optional
from dataclasses import dataclass
from loguru import logger

from bot.utils.hyperion_enhanced import HyperionAPI
from bot.utils.bluefin_enhanced import BluefinAPI


@dataclass
class ProtocolResult:
    """Результат для одного протокола"""
    protocol_id: str
    protocol_name: str
    protocol_emoji: str
    pool_count: int
    total_tvl: float
    best_apr: float
    pools: List[Dict]


@dataclass
class BlockchainResult:
    """Результат для одного блокчейна"""
    chain_id: str
    chain_name: str
    chain_emoji: str
    pool_count: int
    total_tvl: float
    protocols: List[ProtocolResult]
    best_apr: float


@dataclass
class TokenSearchResult:
    """Результат поиска токена"""
    token: str
    total_pools: int
    blockchains: List[BlockchainResult]


class TokenSearchEngine:
    """Движок поиска по токенам через все блокчейны и протоколы"""
    
    def __init__(self):
        # Регистрируем все протоколы
        self.protocols = {
            'aptos': {
                'hyperion': {
                    'api': HyperionAPI(),
                    'name': 'Hyperion',
                    'emoji': '🌊',
                },
            },
            'sui': {
                'bluefin': {
                    'api': BluefinAPI(),
                    'name': 'Bluefin Exchange',
                    'emoji': '🐋',
                },
            },
        }
    
    async def search_token(self, query: str) -> TokenSearchResult:
        """
        Поиск токена или пары через все блокчейны
        
        Args:
            query: "APT" или "APT-USDT" или "APT/USDT"
            
        Returns:
            TokenSearchResult с агрегированными данными
        """
        # Нормализуем query
        query = query.upper().replace('/', '-').strip()
        
        # Определяем тип поиска
        is_pair = '-' in query
        
        if is_pair:
            tokens = query.split('-')
            if len(tokens) != 2:
                raise ValueError("Invalid pair format")
            token_a, token_b = tokens
        else:
            token_a = query
            token_b = None
        
        logger.info(f"Searching for token: {token_a}, pair: {token_b}")
        
        # Ищем во всех блокчейнах
        blockchain_results = []
        
        for chain_id, protocols in self.protocols.items():
            try:
                chain_result = await self._search_in_blockchain(
                    chain_id, 
                    protocols, 
                    token_a, 
                    token_b
                )
                
                if chain_result and chain_result.pool_count > 0:
                    blockchain_results.append(chain_result)
            except Exception as e:
                logger.error(f"Error searching in {chain_id}: {e}")
                continue
        
        # Сортируем блокчейны по TVL
        blockchain_results = sorted(
            blockchain_results, 
            key=lambda x: x.total_tvl, 
            reverse=True
        )
        
        total_pools = sum(b.pool_count for b in blockchain_results)
        
        return TokenSearchResult(
            token=query,
            total_pools=total_pools,
            blockchains=blockchain_results
        )
    
    async def _search_in_blockchain(
        self, 
        chain_id: str,
        protocols: Dict,
        token_a: str,
        token_b: Optional[str] = None
    ) -> Optional[BlockchainResult]:
        """Поиск в одном блокчейне"""
        
        protocol_results = []
        
        for protocol_id, protocol_info in protocols.items():
            try:
                api = protocol_info['api']
                
                # Получаем пулы (используем существующие методы)
                if hasattr(api, 'get_all_pools'):
                    pools = await api.get_all_pools()
                elif hasattr(api, 'get_all_markets'):
                    # Для Bluefin (если еще не переделано)
                    markets = await api.get_all_markets()
                    pools = markets  # Временно
                else:
                    continue
                
                # Фильтруем пулы
                filtered = self._filter_pools(pools, token_a, token_b)
                
                if filtered:
                    # Поддержка разных форматов полей (tvlUSD для Hyperion, tvl_usd для Bluefin)
                    total_tvl = sum(float(p.get('tvlUSD', p.get('tvl_usd', 0))) for p in filtered)
                    best_apr = max((float(p.get('total_apr', 0)) for p in filtered), default=0.0)
                    
                    protocol_results.append(ProtocolResult(
                        protocol_id=protocol_id,
                        protocol_name=protocol_info['name'],
                        protocol_emoji=protocol_info['emoji'],
                        pool_count=len(filtered),
                        total_tvl=total_tvl,
                        best_apr=best_apr,
                        pools=filtered
                    ))
            except Exception as e:
                logger.error(f"Error searching in {chain_id}/{protocol_id}: {e}")
                continue
        
        if not protocol_results:
            return None
        
        # Метаданные блокчейна
        chain_info = {
            'aptos': ('Aptos', '🔷'),
            'sui': ('Sui', '🔵'),
            'bsc': ('BSC', '🔶'),
            'ethereum': ('Ethereum', '🔷'),
            'solana': ('Solana', '🟢'),
        }
        
        chain_name, chain_emoji = chain_info.get(chain_id, (chain_id.capitalize(), '🔷'))
        
        return BlockchainResult(
            chain_id=chain_id,
            chain_name=chain_name,
            chain_emoji=chain_emoji,
            pool_count=sum(p.pool_count for p in protocol_results),
            total_tvl=sum(p.total_tvl for p in protocol_results),
            protocols=protocol_results,
            best_apr=max((p.best_apr for p in protocol_results), default=0.0)
        )
    
    def _filter_pools(
        self, 
        pools: List[Dict], 
        token_a: str, 
        token_b: Optional[str] = None
    ) -> List[Dict]:
        """Фильтрует пулы по токенам"""
        
        filtered = []
        
        for pool in pools:
            pool_token_a = pool.get('token_a', '').upper()
            pool_token_b = pool.get('token_b', '').upper()
            
            if token_b:
                # Поиск конкретной пары
                if ((pool_token_a == token_a and pool_token_b == token_b) or
                    (pool_token_a == token_b and pool_token_b == token_a)):
                    filtered.append(pool)
            else:
                # Поиск любых пулов с токеном
                if token_a in [pool_token_a, pool_token_b]:
                    filtered.append(pool)
        
        # Сортируем по TVL (поддержка разных форматов полей)
        return sorted(filtered, key=lambda x: float(x.get('tvlUSD', x.get('tvl_usd', 0))), reverse=True)


# Singleton
token_search = TokenSearchEngine()

