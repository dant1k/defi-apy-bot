from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from typing import Optional, List
from datetime import datetime

from bot.database.models import Base, User, Pool, WatchedPool
from config.settings import settings

# Создаем async engine
engine = create_async_engine(settings.DATABASE_URL, echo=False)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """Создание всех таблиц в базе данных"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_or_create_user(telegram_id: int, username: Optional[str] = None) -> User:
    """Получить пользователя или создать нового"""
    async with async_session_maker() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        
        if user is None:
            user = User(telegram_id=telegram_id, username=username)
            session.add(user)
            await session.commit()
            await session.refresh(user)
        elif username and user.username != username:
            user.username = username
            await session.commit()
            await session.refresh(user)
        
        return user


async def upsert_pool(pool_data: dict) -> Pool:
    """Создать или обновить пул"""
    async with async_session_maker() as session:
        result = await session.execute(
            select(Pool).where(Pool.pool_address == pool_data["pool_address"])
        )
        pool = result.scalar_one_or_none()
        
        if pool is None:
            pool = Pool(**pool_data)
            session.add(pool)
        else:
            for key, value in pool_data.items():
                setattr(pool, key, value)
            pool.last_updated = datetime.utcnow()
        
        await session.commit()
        await session.refresh(pool)
        return pool


async def get_top_pools(min_tvl: float = 0.0, min_apr: float = 0.0, limit: int = 10) -> List[Pool]:
    """Получить топ пулов по APR с фильтрами"""
    async with async_session_maker() as session:
        query = (
            select(Pool)
            .where(Pool.tvl_usd >= min_tvl)
            .where(Pool.total_apr >= min_apr)
            .order_by(desc(Pool.total_apr))
            .limit(limit)
        )
        result = await session.execute(query)
        return list(result.scalars().all())


async def get_pool_by_address(pool_address: str) -> Optional[Pool]:
    """Получить пул по адресу"""
    async with async_session_maker() as session:
        result = await session.execute(
            select(Pool).where(Pool.pool_address == pool_address)
        )
        return result.scalar_one_or_none()


async def get_pools_by_fee_rate(fee_rate: int) -> List[Pool]:
    """Получить пулы по fee rate"""
    async with async_session_maker() as session:
        query = (
            select(Pool)
            .where(Pool.fee_rate == fee_rate)
            .order_by(desc(Pool.tvl_usd))
        )
        result = await session.execute(query)
        return list(result.scalars().all())


async def get_all_pools() -> List[Pool]:
    """Получить все пулы, отсортированные по TVL"""
    async with async_session_maker() as session:
        query = (
            select(Pool)
            .order_by(desc(Pool.tvl_usd))
        )
        result = await session.execute(query)
        return list(result.scalars().all())


async def add_watched_pool(telegram_id: int, pool_address: str, alert_threshold: Optional[float] = None) -> WatchedPool:
    """Добавить пул в отслеживаемые для пользователя"""
    async with async_session_maker() as session:
        # Получаем или создаем пользователя в этой же сессии
        user_result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = user_result.scalar_one_or_none()
        if not user:
            user = User(telegram_id=telegram_id)
            session.add(user)
            await session.flush()  # Получаем ID без commit
        
        # Получаем пул
        pool_result = await session.execute(
            select(Pool).where(Pool.pool_address == pool_address)
        )
        pool = pool_result.scalar_one_or_none()
        if not pool:
            raise ValueError(f"Pool {pool_address} not found")
        
        # Проверяем, не отслеживается ли уже
        watched_result = await session.execute(
            select(WatchedPool).where(
                WatchedPool.user_id == user.id,
                WatchedPool.pool_id == pool.id
            )
        )
        watched = watched_result.scalar_one_or_none()
        
        if watched is None:
            watched = WatchedPool(
                user_id=user.id,
                pool_id=pool.id,
                alert_threshold=alert_threshold
            )
            session.add(watched)
            await session.commit()
            await session.refresh(watched)
        else:
            await session.commit()
        
        return watched


async def get_user_watched_pools(telegram_id: int) -> List[WatchedPool]:
    """Получить все отслеживаемые пулы пользователя"""
    async with async_session_maker() as session:
        result = await session.execute(
            select(WatchedPool)
            .join(User)
            .where(User.telegram_id == telegram_id)
            .options(selectinload(WatchedPool.pool))
        )
        return list(result.scalars().all())
