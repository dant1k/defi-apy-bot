"""
Утилиты для работы с Fee Tier
"""
from typing import Optional


def format_fee_tier(fee_rate: int) -> str:
    """
    Конвертирует feeRate в читаемый формат процентов
    
    Args:
        fee_rate: Значение из API (100, 500, 2500, 10000)
        
    Returns:
        str: Форматированный процент (например, "0.25%")
    """
    if not fee_rate:
        return "N/A"
    
    # Формула: fee_rate / 10000
    fee_percentage = float(fee_rate) / 10000
    return f"{fee_percentage:.2f}%"


def get_fee_tier_category(fee_rate: int) -> str:
    """
    Определяет категорию fee tier
    
    Args:
        fee_rate: Значение из API
        
    Returns:
        str: Название категории
    """
    if not fee_rate:
        return "Unknown"
    
    fee_rate_int = int(fee_rate)
    
    # Стандартные Fee Tiers
    if fee_rate_int == 100:
        return "Ultra Low"
    elif fee_rate_int == 500:
        return "Low"
    elif fee_rate_int == 2500:
        return "Medium"
    elif fee_rate_int == 10000:
        return "High"
    elif fee_rate_int < 500:
        return "Ultra Low"
    elif fee_rate_int < 2500:
        return "Low"
    elif fee_rate_int < 10000:
        return "Medium"
    else:
        return "High"


def get_fee_tier_description(fee_rate: int) -> str:
    """
    Получить полное описание fee tier с категорией
    
    Args:
        fee_rate: Значение из API
        
    Returns:
        str: Описание (например, "0.25% (Medium - Standard)")
    """
    category = get_fee_tier_category(fee_rate)
    percentage = format_fee_tier(fee_rate)
    
    descriptions = {
        "Ultra Low": "Stablecoins",
        "Low": "Correlated",
        "Medium": "Standard",
        "High": "Exotic",
    }
    
    description = descriptions.get(category, "")
    if description:
        return f"{percentage} ({category} - {description})"
    return f"{percentage} ({category})"


def calculate_fees_from_volume(volume_24h: float, fee_rate: int) -> float:
    """
    Вычисляет fees из volume и fee rate
    
    Args:
        volume_24h: Объем за 24 часа в USD
        fee_rate: Fee rate из API
        
    Returns:
        float: Fees за 24 часа в USD
    """
    if not fee_rate or not volume_24h:
        return 0.0
    
    fee_percentage = float(fee_rate) / 10000
    return volume_24h * fee_percentage

