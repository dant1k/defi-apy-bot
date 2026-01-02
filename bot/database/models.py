from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)
    username = Column(String, nullable=True)
    min_tvl_filter = Column(Float, default=0.0)
    min_apr_filter = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    watched_pools = relationship("WatchedPool", back_populates="user", cascade="all, delete-orphan")


class Pool(Base):
    __tablename__ = "pools"
    
    id = Column(Integer, primary_key=True, index=True)
    pool_address = Column(String, unique=True, index=True, nullable=False)
    protocol = Column(String, nullable=False)
    token_x_symbol = Column(String, nullable=False)
    token_y_symbol = Column(String, nullable=False)
    tvl_usd = Column(Float, default=0.0)
    volume_24h = Column(Float, default=0.0)
    fees_24h = Column(Float, default=0.0)
    fee_rate = Column(Integer, default=0)  # Fee rate из API (100, 500, 2500, 10000)
    apr_fees = Column(Float, default=0.0)
    apr_farming = Column(Float, default=0.0)
    total_apr = Column(Float, default=0.0)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    watched_by = relationship("WatchedPool", back_populates="pool", cascade="all, delete-orphan")


class WatchedPool(Base):
    __tablename__ = "watched_pools"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    pool_id = Column(Integer, ForeignKey("pools.id"), nullable=False)
    alert_threshold = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="watched_pools")
    pool = relationship("Pool", back_populates="watched_by")

