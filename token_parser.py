"""
Token Parser для Hyperion Pools Bot
Парсинг символов токенов из Move адресов
"""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Импортируем реестр если доступен
try:
    from token_registry import TOKEN_REGISTRY
except ImportError:
    TOKEN_REGISTRY = {}


# Паттерны для автоматического распознавания токенов
TOKEN_PATTERNS = [
    # Aptos Native
    (r'::aptos_coin::AptosCoin$', 'APT'),
    
    # LayerZero Assets
    (r'::asset::USDC$', 'USDC'),
    (r'::asset::USDT$', 'USDT'),
    (r'::asset::WETH$', 'WETH'),
    (r'::asset::WBTC$', 'WBTC'),
    (r'::asset::DAI$', 'DAI'),
    
    # Celer Bridge
    (r'UsdcCoin$', 'ceUSDC'),
    (r'UsdtCoin$', 'ceUSDT'),
    (r'WethCoin$', 'ceWETH'),
    (r'WbtcCoin$', 'ceWBTC'),
    (r'DaiCoin$', 'ceDAI'),
    
    # Liquid Staking
    (r'AmnisApt$', 'amAPT'),
    (r'StakedAptosCoin$', 'stAPT'),
    (r'StakedAptos$', 'stAPT'),
    (r'TortugaStakedAptos$', 'tAPT'),
    
    # Wormhole (если есть ::coin:: в середине)
    (r'::coin::USDC$', 'whUSDC'),
    (r'::coin::USDT$', 'whUSDT'),
    (r'::coin::WETH$', 'whWETH'),
    (r'::coin::T$', 'WETH'),  # Часто встречается
    
    # DEX tokens
    (r'CakeOFT$', 'CAKE'),
    (r'::mod_coin::MOD$', 'MOD'),
    (r'::thl_coin::THL$', 'THL'),
]


def parse_token_symbol_from_address(address: str) -> str:
    """
    Извлекает символ токена из Move адреса
    
    Формат Move адреса: 0xADDRESS::module::Type
    
    Примеры:
        0x1::aptos_coin::AptosCoin -> APT
        0xf22bede...::asset::USDC -> USDC
        0x111ae3e5...::amapt_token::AmnisApt -> amAPT
        
    Args:
        address: Полный Move адрес токена
        
    Returns:
        str: Символ токена или укороченный адрес
    """
    if not address:
        return "UNKNOWN"
    
    # Удаляем пробелы
    address = address.strip()
    
    # Разделяем по ::
    parts = address.split('::')
    
    if len(parts) >= 3:
        # Последняя часть обычно содержит имя типа
        module = parts[-2]  # Модуль (например, asset, aptos_coin)
        type_name = parts[-1]  # Тип (например, USDC, AptosCoin)
        
        # ===== СПЕЦИАЛЬНЫЕ СЛУЧАИ =====
        
        # Aptos Native Coin
        if type_name == 'AptosCoin':
            return 'APT'
        
        # LayerZero assets - берем название из type_name
        if module == 'asset':
            # asset::USDC -> USDC
            # asset::WETH -> WETH
            return type_name.upper()
        
        # Coin type (обычно это wrapped tokens)
        if module == 'coin' and type_name == 'T':
            # Попытка определить по адресу
            addr_part = parts[0]
            if '5e156f1207d0ebfa' in addr_part:
                return 'WETH'  # Известный адрес WETH
            return 'COIN'
        
        # Staked tokens
        if 'Staked' in type_name:
            if 'Amnis' in type_name:
                return 'amAPT'
            elif 'Tortuga' in type_name:
                return 'tAPT'
            else:
                return 'stAPT'
        
        # Liquid staking tokens
        if type_name == 'AmnisApt':
            return 'amAPT'
        
        # Celer Bridge Coins (UsdcCoin, WethCoin, etc.)
        if type_name.endswith('Coin') and len(type_name) > 4:
            # UsdcCoin -> USDC
            # WethCoin -> WETH
            base = type_name[:-4]  # Убираем Coin
            
            # Специальные случаи
            if base.upper() in ['USDC', 'USDT', 'WETH', 'WBTC', 'DAI']:
                return f"ce{base.upper()}"  # Префикс ce для Celer
            
            return base.upper()
        
        # DEX токены
        if type_name == 'CakeOFT':
            return 'CAKE'
        
        if module == 'mod_coin':
            return 'MOD'
        
        if module == 'thl_coin':
            return 'THL'
        
        # ===== ОБЩИЕ ПРАВИЛА =====
        
        # Если в имени есть известные токены
        type_upper = type_name.upper()
        for known_token in ['USDC', 'USDT', 'WETH', 'WBTC', 'DAI', 'APT']:
            if known_token in type_upper:
                return known_token
        
        # Если ничего не подошло, возвращаем последнюю часть (максимум 8 символов)
        return type_name[:8].upper()
    
    # Если не смогли распарсить структуру, возвращаем укороченный адрес
    if address.startswith('0x'):
        return f"0x{address[2:8]}"
    
    return address[:10]


def get_token_symbol(address: str, use_cache: bool = True) -> str:
    """
    Универсальная функция получения символа токена
    
    Порядок проверки:
    1. Реестр известных токенов (TOKEN_REGISTRY)
    2. Паттерны (TOKEN_PATTERNS)
    3. Парсинг из адреса
    
    Args:
        address: Move адрес токена
        use_cache: Использовать кэширование в реестре
        
    Returns:
        str: Символ токена
    """
    if not address:
        return "UNKNOWN"
    
    # 1. Проверяем в реестре
    if address in TOKEN_REGISTRY:
        return TOKEN_REGISTRY[address]
    
    # 2. Проверяем паттерны
    for pattern, symbol in TOKEN_PATTERNS:
        if re.search(pattern, address):
            # Кэшируем для будущих вызовов
            if use_cache:
                TOKEN_REGISTRY[address] = symbol
            return symbol
    
    # 3. Парсим из адреса
    symbol = parse_token_symbol_from_address(address)
    
    # Логируем неизвестные токены для добавления в реестр
    if symbol.startswith('0x'):
        logger.info(f"🔍 Unknown token: {address} -> {symbol}")
    
    return symbol


def get_pool_name(token1_address: str, token2_address: str) -> str:
    """
    Получает название пула из адресов токенов
    
    Args:
        token1_address: Адрес первого токена
        token2_address: Адрес второго токена
        
    Returns:
        str: Название пула в формате "TOKEN1-TOKEN2"
    """
    token1 = get_token_symbol(token1_address)
    token2 = get_token_symbol(token2_address)
    
    return f"{token1}-{token2}"


def is_stablecoin_pair(token1_address: str, token2_address: str) -> bool:
    """
    Проверяет является ли пара стейблкоинами
    
    Args:
        token1_address: Адрес первого токена
        token2_address: Адрес второго токена
        
    Returns:
        bool: True если оба токена стейблкоины
    """
    stablecoins = ['USDC', 'USDT', 'DAI', 'ceUSDC', 'ceUSDT', 'whUSDC', 'whUSDT']
    
    token1 = get_token_symbol(token1_address)
    token2 = get_token_symbol(token2_address)
    
    return token1 in stablecoins and token2 in stablecoins


def get_token_category(address: str) -> str:
    """
    Определяет категорию токена
    
    Returns:
        str: Категория (stablecoin, wrapped, staked, native, dex, unknown)
    """
    symbol = get_token_symbol(address)
    
    stablecoins = ['USDC', 'USDT', 'DAI', 'ceUSDC', 'ceUSDT', 'whUSDC', 'whUSDT']
    wrapped = ['WETH', 'WBTC', 'ceWETH', 'ceWBTC', 'whWETH']
    staked = ['amAPT', 'stAPT', 'tAPT', 'thAPT']
    dex = ['CAKE', 'MOD', 'THL']
    
    if symbol in stablecoins:
        return 'stablecoin'
    elif symbol in wrapped:
        return 'wrapped'
    elif symbol in staked:
        return 'staked'
    elif symbol == 'APT':
        return 'native'
    elif symbol in dex:
        return 'dex'
    else:
        return 'unknown'


# ===== ТЕСТИРОВАНИЕ =====

if __name__ == "__main__":
    # Тестовые адреса
    test_addresses = [
        ('0x1::aptos_coin::AptosCoin', 'APT'),
        ('0xf22bede237a07e121b56d91a491eb7bcdfd1f5907926a9e58338f964a01b17fa::asset::USDC', 'USDC'),
        ('0xf22bede237a07e121b56d91a491eb7bcdfd1f5907926a9e58338f964a01b17fa::asset::USDT', 'USDT'),
        ('0x8d87a65ba30e09357fa2edea2c80dbac296e5dec2b18287113500b902942929d::celer_coin_manager::UsdcCoin', 'ceUSDC'),
        ('0x111ae3e5bc816a5e63c2da97d0aa3886519e0cd5e4b046659fa35796bd11542a::amapt_token::AmnisApt', 'amAPT'),
        ('0x84d7aeef42d38a5ffc3ccef853e1b82e4958659d16a7de736a29c55fbbeb0114::staked_aptos_coin::StakedAptosCoin', 'stAPT'),
        ('0x5e156f1207d0ebfa19a9eeff00d62a282278fb8719f4fab3a586a0a2c0fffbea::coin::T', 'WETH'),
    ]
    
    print("🧪 Testing token parser...\n")
    
    for address, expected in test_addresses:
        result = get_token_symbol(address)
        status = "✅" if result == expected else "❌"
        print(f"{status} {address[:50]}...")
        print(f"   Expected: {expected}, Got: {result}\n")
    
    # Тест pool name
    print("\n🏊 Testing pool names...")
    token1 = '0x1::aptos_coin::AptosCoin'
    token2 = '0xf22bede237a07e121b56d91a491eb7bcdfd1f5907926a9e58338f964a01b17fa::asset::USDC'
    pool_name = get_pool_name(token1, token2)
    print(f"Pool: {pool_name}")
    print(f"Is stablecoin pair: {is_stablecoin_pair(token1, token2)}")
    
    # Тест категорий
    print("\n📊 Testing categories...")
    for addr, _ in test_addresses[:5]:
        symbol = get_token_symbol(addr)
        category = get_token_category(addr)
        print(f"{symbol}: {category}")
