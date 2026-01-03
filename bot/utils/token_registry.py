"""
Реестр известных токенов на Aptos/Hyperion
Обновляется по мере добавления новых токенов
"""
import re
from loguru import logger

# Множество для отслеживания уже залогированных неизвестных токенов
_logged_unknown_tokens = set()

# Паттерны для автоматического распознавания токенов
TOKEN_PATTERNS = [
    (r'::aptos_coin::AptosCoin$', 'APT'),
    (r'::asset::USDC$', 'USDC'),
    (r'::asset::USDT$', 'USDT'),
    (r'::asset::WETH$', 'WETH'),
    (r'::asset::WBTC$', 'WBTC'),
    (r'::asset::DAI$', 'DAI'),
    (r'UsdcCoin$', 'USDC'),
    (r'UsdtCoin$', 'USDT'),
    (r'WethCoin$', 'WETH'),
    (r'WbtcCoin$', 'WBTC'),
    (r'AmnisApt$', 'amAPT'),
    (r'StakedAptosCoin$', 'stAPT'),
    (r'StakedAptos$', 'stAPT'),
]

TOKEN_REGISTRY = {
    # Aptos Native
    '0x1::aptos_coin::AptosCoin': 'APT',
    
    # LayerZero Stablecoins
    '0xf22bede237a07e121b56d91a491eb7bcdfd1f5907926a9e58338f964a01b17fa::asset::USDC': 'USDC',
    '0xf22bede237a07e121b56d91a491eb7bcdfd1f5907926a9e58338f964a01b17fa::asset::USDT': 'USDT',
    '0xf22bede237a07e121b56d91a491eb7bcdfd1f5907926a9e58338f964a01b17fa::asset::WETH': 'WETH',
    '0xf22bede237a07e121b56d91a491eb7bcdfd1f5907926a9e58338f964a01b17fa::asset::WBTC': 'WBTC',
    
    # Wrapped/Staked APT
    '0x111ae3e5bc816a5e63c2da97d0aa3886519e0cd5e4b046659fa35796bd11542a::amapt_token::AmnisApt': 'amAPT',
    '0xa259be733b6a759909f92815927fa213904df6540519568692caf0b068fe8e62::amapt_token::AmnisApt': 'amAPT',  # Альтернативный контракт amAPT
    '0x84d7aeef42d38a5ffc3ccef853e1b82e4958659d16a7de736a29c55fbbeb0114::staked_aptos_coin::StakedAptosCoin': 'stAPT',
    '0xd11107bdf0d6d7040c6c0bfbdecb6545191fdf13e8d8d259952f53e1713f61b5::staked_coin::StakedAptos': 'stAPT',
    
    # DEX Tokens
    '0x5e156f1207d0ebfa19a9eeff00d62a282278fb8719f4fab3a586a0a2c0fffbea::coin::T': 'USDC',
    '0x8d87a65ba30e09357fa2edea2c80dbac296e5dec2b18287113500b902942929d::celer_coin_manager::UsdcCoin': 'ceUSDC',
    
    # FA адреса (из существующего кода)
    '0x000000000000000000000000000000000000000000000000000000000000000a': 'APT',
    '0x0009da434d9b873b5159e8eeed70202ad22dc075867a7793234fbc981b63e119': 'APT',
    '0xbae207659db88bea0cbead6da0ed00aac12edcdda169e591cd41c94180b46f3b': 'USDC',
    '0x357b0b74bc833e95a115ad22604854d6b0fca151cecd94111770e5d6ffc9dc2b': 'USDT',
    '0x377adc4848552eb2ea17259be928001923efe12271fef1667e2b784f04a7cf3a': 'USDt',
    '0x81214a80d82035a190fcb76b6ff3c0145161c3a9f33d137f2bbaee4cfec8a387': 'xBTC',  # xBTC токен
    '0x68844a0d7f2587e726ad0579f3d640865bb4162c08a4589eeda3f9689ec52a3d': 'WBTC',  # WBTC токен
    '0xb30a694a344edee467d9f82330bbe7c3b89f440a1ecd2da1f3bca266560fce69': 'sUSDe',  # sUSDe токен
    '0x821c94e69bc7ca058c913b7b5e6b0a5c9fd1523d58723a966fb8c1f5ea888105': 'kAPT',
    '0x05fabd1b12e39967a3c24e91b7b8f67719a6dacee74f3c8b9fb7d93e855437d2': 'USD1',  # USD1 токен
}


def parse_token_symbol_from_address(address: str) -> str:
    """
    Извлекает символ токена из Move адреса
    
    Args:
        address: Move адрес токена
        
    Returns:
        str: Символ токена
        
    Примеры:
    0x1::aptos_coin::AptosCoin -> APT
    0xf22bede...::asset::USDC -> USDC
    0x111ae3e5...::amapt_token::AmnisApt -> amAPT
    """
    # Удаляем пробелы
    address = address.strip()
    
    # Разделяем по ::
    parts = address.split('::')
    
    if len(parts) >= 3:
        # Последняя часть обычно содержит имя
        last_part = parts[-1]
        
        # Обработка стандартных паттернов
        if last_part == 'AptosCoin':
            return 'APT'
        elif last_part.endswith('Coin'):
            # UsdcCoin -> USDC, WethCoin -> WETH
            symbol = last_part.replace('Coin', '').upper()
            return symbol
        elif 'USDC' in last_part.upper():
            return 'USDC'
        elif 'USDT' in last_part.upper():
            return 'USDT'
        elif 'WETH' in last_part.upper():
            return 'WETH'
        elif 'WBTC' in last_part.upper():
            return 'WBTC'
        elif last_part == 'AmnisApt':
            return 'amAPT'
        elif last_part == 'StakedAptosCoin':
            return 'stAPT'
        elif last_part == 'StakedAptos':
            return 'stAPT'
        else:
            # Возвращаем как есть если не распознали
            return last_part[:8]
    
    # Если не смогли распарсить, возвращаем укороченный адрес
    if address.startswith('0x'):
        return f"0x{address[2:8]}"
    
    return address[:10]


def get_token_symbol(token_address: str) -> str:
    """
    Универсальная функция получения символа токена
    
    Порядок:
    1. Проверка в реестре (TOKEN_REGISTRY)
    2. Проверка по паттернам (TOKEN_PATTERNS)
    3. Парсинг из адреса (parse_token_symbol_from_address)
    
    Args:
        token_address: Адрес токена (полный или FA адрес)
        
    Returns:
        str: Символ токена или укороченный адрес
    """
    if not token_address:
        return "???"
    
    # Нормализуем адрес
    normalized = token_address.lower().strip()
    
    # 1. Проверка в реестре (точное совпадение)
    if normalized in TOKEN_REGISTRY:
        return TOKEN_REGISTRY[normalized]
    
    # Проверяем частичное совпадение (для FA адресов)
    for addr, symbol in TOKEN_REGISTRY.items():
        if addr.lower().strip() == normalized:
            return symbol
    
    # 2. Проверка по паттернам (регулярные выражения)
    for pattern, symbol in TOKEN_PATTERNS:
        if re.search(pattern, token_address, re.IGNORECASE):
            # Кэшируем в реестр для следующих вызовов (опционально)
            # TOKEN_REGISTRY[token_address] = symbol
            return symbol
    
    # 3. Парсинг из адреса
    symbol = parse_token_symbol_from_address(token_address)
    
    # Логируем неизвестные токены (один раз)
    if normalized not in _logged_unknown_tokens:
        logger.info(f"Unknown token: {token_address[:50]}... -> parsed as {symbol}")
        _logged_unknown_tokens.add(normalized)
    
    return symbol

