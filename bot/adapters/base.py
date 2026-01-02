from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class PoolData:
    """Модель данных пула"""
    protocol: str
    pool_address: str
    token_x_symbol: str
    token_y_symbol: str
    tvl_usd: float
    volume_24h: float
    apr_fees: float
    apr_farming: float
    total_apr: float
    fees_24h: float = 0.0  # Комиссии за 24 часа (реальные fees из API, учитывают fee tier пула)
    fee_rate: int = 0  # Fee rate из API (100, 500, 2500, 10000) - используется для определения fee tier
    
    def to_dict(self) -> dict:
        """Преобразовать в словарь для сохранения в БД"""
        return {
            "protocol": self.protocol,
            "pool_address": self.pool_address,
            "token_x_symbol": self.token_x_symbol,
            "token_y_symbol": self.token_y_symbol,
            "tvl_usd": self.tvl_usd,
            "volume_24h": self.volume_24h,
            "fees_24h": self.fees_24h,
            "fee_rate": self.fee_rate,
            "apr_fees": self.apr_fees,
            "apr_farming": self.apr_farming,
            "total_apr": self.total_apr,
        }


class BaseAdapter(ABC):
    """Базовый класс адаптера для получения данных о пулах"""
    
    @abstractmethod
    async def get_pools(self) -> List[PoolData]:
        """
        Получить список пулов
        
        Returns:
            List[PoolData]: Список пулов
        """
        pass

