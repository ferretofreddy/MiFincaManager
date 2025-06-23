# database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
import os

# Base de datos Neon
# ¡IMPORTANTE! Esta es tu URL de conexión REAL a tu base de datos en Neon.
# Se ha corregido según tu entrada.
DATABASE_URL = "postgresql+asyncpg://neondb_owner:npg_3BEZc8LhybAR@ep-sweet-mud-a8icnhkj-pooler.eastus2.azure.neon.tech/neondb"

# Configurar el motor de la base de datos asíncrono
# echo=True es útil para ver las consultas SQL generadas en el log durante el desarrollo
engine = create_async_engine(
    DATABASE_URL, 
    echo=False, # Mantener en True para depuración si es necesario, o cambiar a False en producción
    pool_size=10, 
    max_overflow=20, 
    pool_recycle=3600, 
    pool_pre_ping=True 
) 

# Configurar el sessionmaker asíncrono.
# autoflush=False es comúnmente usado para controlar explícitamente cuando los cambios se envían a la DB.
# expire_on_commit=False es CRÍTICO para evitar que los objetos se "desvinculen" de la sesión 
# después de un commit y causen errores MissingGreenlet cuando intentas acceder a relaciones lazy.
AsyncSessionLocal = async_sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine, 
    class_=AsyncSession,
    expire_on_commit=False # ¡IMPORTANTE: Mantiene los objetos asociados a la sesión después del commit!
)

Base = declarative_base()

async def get_db():
    """
    Dependencia que proporciona una sesión de base de datos asíncrona.
    La sesión se cierra automáticamente después de la solicitud.
    """
    db: AsyncSession = AsyncSessionLocal()
    try:
        yield db
    finally:
        # Asegurarse de que la sesión se cierre correctamente.
        # Esta línea DEBE ejecutarse para cada solicitud.
        await db.close()

# Función para inicializar la base de datos y crear las tablas (solo si no existen)
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
