# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

# Clase que define la configuración de la aplicación.
# Hereda de BaseSettings para cargar variables de entorno automáticamente.
class Settings(BaseSettings):
    # Configuración de Pydantic para manejar el archivo .env
    model_config = SettingsConfigDict(
        env_file=".env",            # Especifica el archivo de entorno
        case_sensitive=True         # Las variables de entorno son sensibles a mayúsculas/minúsculas
    )

    # --- Configuración de la Base de Datos ---
    # DATABASE_URL: La cadena de conexión a la base de datos (ej. PostgreSQL)
    # Se espera que sea un DSN (Data Source Name), que Pydantic puede validar.
    DATABASE_URL: str
    DB_POOL_SIZE: int = 10          # Número máximo de conexiones activas en el pool
    DB_MAX_OVERFLOW: int = 20       # Número de conexiones adicionales que se pueden crear
    DB_POOL_RECYCLE: int = 3600     # Tiempo en segundos después del cual una conexión inactiva será reciclada
    DB_POOL_PRE_PING: bool = True   # Habilita el "pre-ping" para verificar la conexión antes de usarla

    # --- Configuración de Seguridad (JWT) ---
    SECRET_KEY: str = "MiFincaManager"  # Clave secreta para firmar los tokens JWT
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30 # Tiempo de expiración del token de acceso en minutos
    ALGORITHM: str = "HS256"        # Algoritmo de cifrado para JWT (ej. HS256, RS256)

    # --- Configuración General de la Aplicación ---
    DEBUG: bool = False             # Modo de depuración (True para desarrollo, False para producción)
    PROJECT_NAME: str = "MiFincaManager" # Nombre del proyecto
    API_V1_STR: str = "/api/v1"     # Prefijo para las rutas de la API v1

# Crea una instancia global de la configuración.
# Esto cargará las variables de entorno al iniciar la aplicación.
settings = Settings()
