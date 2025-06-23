# app/core/security.py
from datetime import datetime, timedelta, timezone
from typing import Union, Any

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings # Importa la configuración centralizada

# Configuración para el contexto de hashing de contraseñas (bcrypt es un buen estándar)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica si una contraseña en texto plano coincide con su hash.
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Genera el hash de una contraseña.
    """
    return pwd_context.hash(password)

def create_access_token(
    data: dict, expires_delta: Union[timedelta, None] = None
) -> str:
    """
    Crea un token de acceso JWT.
    data: Diccionario con los claims a incluir en el token (ej. {"sub": user_id}).
    expires_delta: Opcional. Tiempo de vida del token. Si no se especifica, usa el valor por defecto de settings.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire}) # Añade la expiración al payload
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt

def decode_access_token(token: str) -> Union[dict, None]:
    """
    Decodifica un token JWT y verifica su firma y expiración.
    Retorna los claims del token si es válido, None en caso contrario.
    """
    try:
        decoded_token = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return decoded_token
    except jwt.JWTError:
        # Esto captura errores de firma inválida, expiración, etc.
        return None
