# dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from database import get_db
import crud
import models
import schemas 
from app_security import ALGORITHM, SECRET_KEY 


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/token")

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    """
    Dependencia que obtiene el usuario actual autenticado a partir del token JWT.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str: str = payload.get("sub") # Obtener como string del payload JWT
        if user_id_str is None:
            raise credentials_exception
        # Convertir a UUID solo una vez aquí si schemas.TokenData espera UUID
        token_data = schemas.TokenData(user_id=uuid.UUID(user_id_str)) 
    except JWTError:
        raise credentials_exception
    except ValueError: # Añadir manejo de error si user_id_str no es un UUID válido
        raise credentials_exception
    
    # Aquí user_id ya es un objeto UUID, no necesita conversión adicional
    user = await crud.get_user(db, user_id=token_data.user_id) 
    if user is None:
        raise credentials_exception
    return user

