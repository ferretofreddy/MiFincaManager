    # app/api/v1/endpoints/auth.py
    from datetime import timedelta
    from typing import Any
    from fastapi import APIRouter, Depends, HTTPException, status
    from fastapi.security import OAuth2PasswordRequestForm
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.core.security import create_access_token, verify_password
    from app.core.config import settings
    from app.api import deps # Importa deps para get_db
    from app import schemas, crud # Importa schemas y crud para acceder al crud.user

    router = APIRouter()

    @router.post("/login/access-token", response_model=schemas.Token)
    async def login_access_token(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: AsyncSession = Depends(deps.get_db)
    ) -> Any:
        """
        OAuth2 login para obtener un token de acceso JWT.
        """
        user = await crud.user.get_by_email(db, email=form_data.username)
        if not user or not verify_password(form_data.password, user.password_hash):
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

    