# app/db/session.py
# Configura el motor de la base de datos y la fábrica de sesiones asíncronas.

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings # ¡Ahora esto sí funcionará correctamente!

# Asegúrate de que settings se cargue antes de usarlo.
# Esto es más bien una práctica de asegurar que el módulo settings
# ya ha sido inicializado con las variables de entorno.
# En un entorno FastAPI, esto se maneja con la inicialización de la app,
# pero en un script independiente, a veces es útil forzarlo si no se hace implícitamente.
_ = settings.DATABASE_URL # Acceder a una propiedad para forzar la carga si no está ya cargada

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

# Exportamos SessionLocal para que sea usado en los puntos de entrada y dependencias
async_sessionmaker = SessionLocal # Asumiendo que quieres exportarlo con este nombre también

async def get_db() -> AsyncSession:
    """
    Dependencia de FastAPI para obtener una sesión de base de datos asíncrona.
    """
    async with SessionLocal() as session:
        yield session

