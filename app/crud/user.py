# app/crud/user.py
from typing import Optional, List
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

# Importa el modelo User y los esquemas de user
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate

# Importa la CRUDBase, get_password_hash y las excepciones
from app.crud.base import CRUDBase
from app.crud.exceptions import NotFoundError, AlreadyExistsError, CRUDException
from app.core.security import get_password_hash 

class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    """
    Clase CRUD específica para el modelo User.
    Hereda la mayoría de las operaciones de CRUDBase.
    Implementa métodos específicos para User que requieren lógica adicional.
    """

    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """
        Obtiene un usuario por su dirección de correo electrónico.
        """
        result = await db.execute(
            select(self.model)
            .filter(self.model.email == email)
        )
        return result.scalar_one_or_none()

    async def create(self, db: AsyncSession, *, obj_in: UserCreate) -> User:
        """
        Crea un nuevo usuario con la contraseña hasheada.
        """
        # Verifica si ya existe un usuario con el mismo email
        existing_user = await self.get_by_email(db, email=obj_in.email)
        if existing_user:
            raise AlreadyExistsError(f"User with email '{obj_in.email}' already exists.")

        try:
            hashed_password = get_password_hash(obj_in.password)
            db_obj = self.model(
                email=obj_in.email,
                hashed_password=hashed_password,
                first_name=obj_in.first_name,
                last_name=obj_in.last_name,
                phone_number=obj_in.phone_number,
                address=obj_in.address,
                country=obj_in.country,
                city=obj_in.city
            )
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj) # Recarga el objeto para obtener el id, created_at, etc.
            return db_obj
        except Exception as e:
            await db.rollback()
            raise CRUDException(f"Error creating User: {str(e)}") from e

    async def update(self, db: AsyncSession, *, db_obj: User, obj_in: UserUpdate) -> User:
        """
        Actualiza un usuario existente, manejando el hashing de la contraseña si se proporciona.
        """
        # Si la contraseña se proporciona en obj_in, hashearla
        if obj_in.password:
            obj_in_data = obj_in.model_dump(exclude_unset=True)
            obj_in_data["hashed_password"] = get_password_hash(obj_in.password)
            # Elimina la contraseña en texto plano de obj_in_data
            del obj_in_data["password"]
            updated_user = await super().update(db, db_obj=db_obj, obj_in=obj_in_data)
        else:
            updated_user = await super().update(db, db_obj=db_obj, obj_in=obj_in)
        return updated_user

# Crea una instancia de CRUDUser que se puede importar y usar en los routers
user = CRUDUser(User)
