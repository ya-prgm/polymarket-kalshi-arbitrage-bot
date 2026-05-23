import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Float, JSON, DateTime, Integer, Boolean
from datetime import datetime

DB_PATH = r"C:\arbitrage.db"


os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"

engine = create_async_engine(DATABASE_URL)
async_session = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class Setting(Base):

    __tablename__ = "settings"
    key: Mapped[str] = mapped_column(String, primary_key=True)
    value: Mapped[str] = mapped_column(String)

class ScanSession(Base):

    __tablename__ = "scans"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    status: Mapped[str] = mapped_column(String, default="pending") 
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    total_poly: Mapped[int] = mapped_column(Integer, default=0)
    total_kalshi: Mapped[int] = mapped_column(Integer, default=0)
    total_matches: Mapped[int] = mapped_column(Integer, default=0)
    total_deals: Mapped[int] = mapped_column(Integer, default=0)
    start_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=True)

class Deal(Base):
    __tablename__ = "deals"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scan_id: Mapped[str] = mapped_column(String)
    poly_question: Mapped[str] = mapped_column(String)
    kalshi_question: Mapped[str] = mapped_column(String)
    profit_percent: Mapped[float] = mapped_column(Float)
    data: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

async def init_db():

    async with engine.begin() as conn:

        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session() as session:
        defaults = {
            "TOTAL_LIMIT": "5000",           # Лимит рынков с каждой биржи
            "MIN_PROFIT": "-100.0",          # Сохраняем всё, даже минусовые вилки (для истории и UI фильтров)
            "MAX_PROFIT": "1000.0",          # Максимальный порог
            "BANKROLL": "1000",              # Сумма для расчета ставок
            "AI_THRESHOLD": "0.63",          # Порог сходства для HybridMatcher
            "MIN_PRICE_THRESHOLD": "0.001",  # Минимальная цена исхода (почти от 0)
            "MAX_PRICE_THRESHOLD": "0.999",  # Максимальная цена исхода (почти до 1)
            "POLY_SORT_BY": "volume24hr",    # Сортировка Poly: volume24hr, endDate или false
            "KALSHI_SORT_BY": "trending",    # Сортировка Kalshi: trending, closing или false
            "DEBUG_MODE": "false",           # Сохранять ли JSON дампы в папку debug
            "DEEPSEEK_KEY": "" # API ключ DeepSeek
        }
        
        for k, v in defaults.items():

            res = await session.get(Setting, k)
            if not res:
                session.add(Setting(key=k, value=v))
        
        await session.commit()