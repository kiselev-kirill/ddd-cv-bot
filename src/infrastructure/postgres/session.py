from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncEngine

from src.config import settings

# Подключение к БД с настройками пула соединений
engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Проверка соединения перед использованием
    echo=True,  # Логирование SQL-запросов
    echo_pool="debug",  # Логирование событий пула соединений
    pool_size=5,  # Размер пула соединений
    max_overflow=10,  # Допустимое превышение пула
    pool_timeout=30,  # Время ожидания соединения
    pool_recycle=1800,  # Перезапуск соединений после простоя
)

session_factory: async_sessionmaker = async_sessionmaker(
    bind=engine,
    autoflush=settings.DATABASE_AUTO_FLUSH,
    expire_on_commit=settings.DATABASE_EXPIRE_ON_COMMIT
)