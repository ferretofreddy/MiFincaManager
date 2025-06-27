# app/api/v1/endpoints/auth.py 

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app import schemas, models, crud
from app.api import deps 
from app.core.security import create_access_token, verify_password 
from app.core.config import settings

router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
    responses={404: {"description": "Not found"}},
)

@router.post("/login", response_model=schemas.Token, summary="Obtener token de acceso JWT")
async def login_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: AsyncSession = Depends(deps.get_db)
):
    """
    OAuth2 login para obtener un token de acceso JWT.
    Verifica las credenciales del usuario y emite un token si son válidas.
    """
    user = await crud.user.get_by_email(db, email=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password): 
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

