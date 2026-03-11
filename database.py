from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, BigInteger, Float, String, select
from config import DATABASE_URL

# Correzione per URL Postgres di Railway/Heroku (iniziano con postgres:// ma SQLAlchemy vuole postgresql://)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)

# Setup Motore Database
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

# --- Modello Utente ---
class User(Base):
    __tablename__ = 'users'
    
    id = Column(BigInteger, primary_key=True)  # ID Telegram
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    fuel_type = Column(String, default="2-1")  # Default Diesel

# --- Funzioni Helper ---

async def init_db():
    """Crea le tabelle se non esistono"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_user(user_id: int):
    """Recupera un utente dal DB"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        return result.scalars().first()

async def create_or_get_user(user_id: int):
    """Recupera l'utente o lo crea se non esiste"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()
        
        if not user:
            user = User(id=user_id)
            session.add(user)
            await session.commit()
            await session.refresh(user)
            
        return user

async def update_user_location(user_id: int, lat: float, lon: float):
    """Aggiorna la posizione dell'utente"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()
        
        if not user:
            user = User(id=user_id, latitude=lat, longitude=lon)
            session.add(user)
        else:
            user.latitude = lat
            user.longitude = lon
            
        await session.commit()

async def update_user_fuel(user_id: int, fuel_type: str):
    """Aggiorna il tipo di carburante preferito"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()
        
        if not user:
            user = User(id=user_id, fuel_type=fuel_type)
            session.add(user)
        else:
            user.fuel_type = fuel_type
            
        await session.commit()