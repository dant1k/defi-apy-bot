"""
Token Registry for Hyperion Pools Bot
Маппинг адресов токенов на их символы для Aptos blockchain
"""

# Реестр известных токенов
# Формат: 'полный_адрес_токена': 'SYMBOL'
TOKEN_REGISTRY = {
    # ==================== APTOS NATIVE ====================
    '0x1::aptos_coin::AptosCoin': 'APT',
    
    # ==================== LAYERZERO STABLECOINS ====================
    # USDC
    '0xf22bede237a07e121b56d91a491eb7bcdfd1f5907926a9e58338f964a01b17fa::asset::USDC': 'USDC',
    '0x5e156f1207d0ebfa19a9eeff00d62a282278fb8719f4fab3a586a0a2c0fffbea::coin::T': 'USDC',
    
    # USDT
    '0xf22bede237a07e121b56d91a491eb7bcdfd1f5907926a9e58338f964a01b17fa::asset::USDT': 'USDT',
    
    # DAI
    '0xf22bede237a07e121b56d91a491eb7bcdfd1f5907926a9e58338f964a01b17fa::asset::DAI': 'DAI',
    
    # ==================== WRAPPED ASSETS ====================
    # WETH
    '0xf22bede237a07e121b56d91a491eb7bcdfd1f5907926a9e58338f964a01b17fa::asset::WETH': 'WETH',
    '0xae478ff7d83ed072dbc5e264250e67ef58f57c99d89b447efd8a0a2e8b2be76e::coin::T': 'WETH',
    
    # WBTC
    '0xf22bede237a07e121b56d91a491eb7bcdfd1f5907926a9e58338f964a01b17fa::asset::WBTC': 'WBTC',
    '0xae478ff7d83ed072dbc5e264250e67ef58f57c99d89b447efd8a0a2e8b2be76e::wbtc::WBTC': 'WBTC',
    
    # ==================== STAKED/LIQUID STAKING ====================
    # Amnis Finance - amAPT
    '0x111ae3e5bc816a5e63c2da97d0aa3886519e0cd5e4b046659fa35796bd11542a::amapt_token::AmnisApt': 'amAPT',
    
    # Tortuga - tAPT
    '0x84d7aeef42d38a5ffc3ccef853e1b82e4958659d16a7de736a29c55fbbeb0114::staked_aptos_coin::StakedAptosCoin': 'stAPT',
    
    # Ditto - stAPT  
    '0xd11107bdf0d6d7040c6c0bfbdecb6545191fdf13e8d8d259952f53e1713f61b5::staked_coin::StakedAptos': 'stAPT',
    
    # Thala - thAPT
    '0xfaf4e633ae9eb31366c9ca24214231760926576c7b625313b3688b5e900731f6::staked_aptos_coin::StakedAptosCoin': 'thAPT',
    
    # ==================== CELER BRIDGE ====================
    '0x8d87a65ba30e09357fa2edea2c80dbac296e5dec2b18287113500b902942929d::celer_coin_manager::UsdcCoin': 'ceUSDC',
    '0x8d87a65ba30e09357fa2edea2c80dbac296e5dec2b18287113500b902942929d::celer_coin_manager::UsdtCoin': 'ceUSDT',
    '0x8d87a65ba30e09357fa2edea2c80dbac296e5dec2b18287113500b902942929d::celer_coin_manager::WethCoin': 'ceWETH',
    '0x8d87a65ba30e09357fa2edea2c80dbac296e5dec2b18287113500b902942929d::celer_coin_manager::WbtcCoin': 'ceWBTC',
    
    # ==================== WORMHOLE ====================
    '0x5e156f1207d0ebfa19a9eeff00d62a282278fb8719f4fab3a586a0a2c0fffbea::coin::USDC': 'whUSDC',
    '0x5e156f1207d0ebfa19a9eeff00d62a282278fb8719f4fab3a586a0a2c0fffbea::coin::USDT': 'whUSDT',
    '0x5e156f1207d0ebfa19a9eeff00d62a282278fb8719f4fab3a586a0a2c0fffbea::coin::WETH': 'whWETH',
    
    # ==================== DEX TOKENS ====================
    # PancakeSwap
    '0x159df6b7689437016108a019fd5bef736bac692b6d4a1f10c941f6fbb9a74ca6::oft::CakeOFT': 'CAKE',
    
    # Thala
    '0x6f986d146e4a90b828d8c12c14b6f4e003fdff11a8eecceceb63744363eaac01::mod_coin::MOD': 'MOD',
    '0x7fd500c11216f0fe3095d0c4b8aa4d64a4e2e04f83758462f2b127255643615::thl_coin::THL': 'THL',
    
    # Aries Markets
    '0x9770fa9c725cbd97eb50b2be5f7416efdfd1f1554beb0750d4dae4c64e860da3::reserve::LP': 'amAPT-APT',
    
    # ==================== MEME/COMMUNITY TOKENS ====================
    # GUI
    '0xe4ccb6d39136469f376242c31b34d10515c8eaaa38092f804db8e08a8f53c5b2::assets_v1::EchoCoin002': 'GUI',
    
    # ABEL
    '0x7c0322595a73b3fc53bb166f5783470afeb1ed9f46e83d9e0cf27e3f15c40e3::abel_coin::AbelCoin': 'ABEL',
    
    # ==================== FALLBACK TOKENS ====================
    # Добавляйте новые токены сюда по мере обнаружения
}


def get_token_symbol(address: str) -> str:
    """
    Получает символ токена по адресу
    
    Args:
        address: Полный адрес токена (например, 0x1::aptos_coin::AptosCoin)
        
    Returns:
        str: Символ токена (например, APT) или укороченный адрес если неизвестен
    """
    # Проверяем в реестре
    if address in TOKEN_REGISTRY:
        return TOKEN_REGISTRY[address]
    
    # Если токен неизвестен, возвращаем укороченный адрес
    if address.startswith('0x'):
        # Берем первые 6 символов после 0x
        return f"0x{address[2:8]}"
    
    # Если формат нестандартный
    return address[:10] if len(address) > 10 else address


def add_token(address: str, symbol: str) -> None:
    """
    Добавляет новый токен в реестр во время выполнения
    
    Args:
        address: Адрес токена
        symbol: Символ токена
    """
    TOKEN_REGISTRY[address] = symbol
    print(f"✅ Added token: {symbol} -> {address}")


def get_all_tokens() -> dict:
    """Возвращает весь реестр токенов"""
    return TOKEN_REGISTRY.copy()


def get_token_count() -> int:
    """Возвращает количество зарегистрированных токенов"""
    return len(TOKEN_REGISTRY)


# Для удобства - обратный маппинг (символ -> адрес)
SYMBOL_TO_ADDRESS = {v: k for k, v in TOKEN_REGISTRY.items()}


def get_token_address(symbol: str) -> str:
    """
    Получает адрес токена по символу
    
    Args:
        symbol: Символ токена (например, APT, USDC)
        
    Returns:
        str: Адрес токена или None если не найден
    """
    return SYMBOL_TO_ADDRESS.get(symbol.upper())


# Категории токенов для фильтрации
TOKEN_CATEGORIES = {
    'stablecoins': ['USDC', 'USDT', 'DAI', 'ceUSDC', 'ceUSDT', 'whUSDC', 'whUSDT'],
    'wrapped': ['WETH', 'WBTC', 'ceWETH', 'ceWBTC', 'whWETH'],
    'staked': ['amAPT', 'stAPT', 'thAPT'],
    'native': ['APT'],
    'dex': ['CAKE', 'MOD', 'THL'],
}


def get_tokens_by_category(category: str) -> list:
    """
    Получает токены определенной категории
    
    Args:
        category: Категория (stablecoins, wrapped, staked, native, dex)
        
    Returns:
        list: Список символов токенов в категории
    """
    return TOKEN_CATEGORIES.get(category.lower(), [])


def is_stablecoin(symbol: str) -> bool:
    """Проверяет является ли токен стейблкоином"""
    return symbol.upper() in TOKEN_CATEGORIES['stablecoins']


if __name__ == "__main__":
    # Тестирование
    print(f"📊 Total tokens registered: {get_token_count()}")
    print(f"\n✅ APT address: {get_token_symbol('0x1::aptos_coin::AptosCoin')}")
    print(f"✅ USDC address: {get_token_symbol('0xf22bede237a07e121b56d91a491eb7bcdfd1f5907926a9e58338f964a01b17fa::asset::USDC')}")
    print(f"✅ Unknown token: {get_token_symbol('0xunknown123456')}")
    
    print(f"\n💵 Stablecoins: {get_tokens_by_category('stablecoins')}")
    print(f"🔒 Staked tokens: {get_tokens_by_category('staked')}")
