# app/db/session.py
# Configura el motor de la base de datos y la fábrica de sesiones asíncronas.

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings # Importa la configuración centralizada

# Crea el motor de la base de datos asíncrono.
# Utiliza la URL y las configuraciones del pool de conexiones definidas en settings.
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG, # Habilita/deshabilita el log de SQL dependiendo del modo DEBUG
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_recycle=settings.DB_POOL_RECYCLE,
    pool_pre_ping=settings.DB_POOL_PRE_PING
)

# Configura la fábrica de sesiones asíncronas.
# Esto se usará para crear nuevas sesiones de base de datos.
SessionLocal = async_sessionmaker(
    autocommit=False,       # Deshabilita la confirmación automática
    autoflush=False,        # Deshabilita el vaciado automático (flush)
    bind=engine,            # Asocia las sesiones a nuestro motor
    class_=AsyncSession,    # Usa la clase AsyncSession para operaciones asíncronas
    expire_on_commit=False  # Los objetos no expirarán después de un commit
)

async def get_db() -> AsyncSession:
    """
    Dependencia de FastAPI para obtener una sesión de base de datos asíncrona.
    Asegura que la sesión se cierre correctamente después de su uso.
    """
    async with SessionLocal() as session:
        yield session
