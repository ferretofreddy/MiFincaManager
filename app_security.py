# app_security.py
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from typing import Union, Any
from jose import jwt

# Configuración de hashing de contraseñas
PWD_CONTEXT = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configuración de JWT
SECRET_KEY = "tu_super_secreto_jwt_aqui_cambialo_en_produccion" # ¡CAMBIA ESTO EN PRODUCCIÓN!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 # Tiempo de expiración del token de acceso en minutos

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si una contraseña plana coincide con su hash."""
    return PWD_CONTEXT.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Genera el hash de una contraseña."""
    return PWD_CONTEXT.hash(password)

def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None) -> str:
    """Crea un token de acceso JWT."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Opcional: Función para decodificar tokens, útil para depuración o si necesitas validación manual
def decode_access_token(token: str) -> Union[dict, None]:
    """Decodifica un token de acceso JWT."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None # Token expirado
    except jwt.JWTError:
        return None # Error de validación del token

