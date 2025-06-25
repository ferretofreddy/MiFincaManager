# app/crud/user.py
from typing import Optional, List, Union, Dict, Any # Añadido Union, Dict, Any
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError as DBIntegrityError # Importa la excepción de integridad de SQLAlchemy

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
        except DBIntegrityError as e:
            await db.rollback()
            raise AlreadyExistsError(f"Error de integridad al crear User: {e}") from e
        except Exception as e:
            await db.rollback()
            if isinstance(e, AlreadyExistsError): # Si es una AlreadyExistsError, relanzarla directamente
                raise e
            raise CRUDException(f"Error creating User: {str(e)}") from e

    async def update(self, db: AsyncSession, *, db_obj: User, obj_in: Union[UserUpdate, Dict[str, Any]]) -> User: # Añadido Union, Dict, Any
        """
        Actualiza un usuario existente, manejando el hashing de la contraseña si se proporciona.
        """
        try:
            # Si obj_in es un Pydantic model, conviértelo a dict y excluye unset
            if isinstance(obj_in, dict):
                update_data = obj_in
            else:
                update_data = obj_in.model_dump(exclude_unset=True)

            # Si la contraseña se proporciona en obj_in, hashearla
            if "password" in update_data and update_data["password"]:
                update_data["hashed_password"] = get_password_hash(update_data["password"])
                del update_data["password"] # Elimina la contraseña en texto plano
            
            # Si el email se está actualizando, verificar unicidad
            if "email" in update_data and update_data["email"] != db_obj.email:
                existing_user = await self.get_by_email(db, email=update_data["email"])
                if existing_user and existing_user.id != db_obj.id: # Asegurarse de que no sea el mismo usuario
                    raise AlreadyExistsError(f"User with email '{update_data['email']}' already exists.")

            # Utiliza el método update de la clase base
            updated_user = await super().update(db, db_obj=db_obj, obj_in=update_data)
            return updated_user
        except Exception as e:
            await db.rollback()
            if isinstance(e, AlreadyExistsError) or isinstance(e, NotFoundError) or isinstance(e, CRUDException):
                raise e
            raise CRUDException(f"Error updating User: {str(e)}") from e

    async def remove(self, db: AsyncSession, *, id: uuid.UUID) -> Optional[User]:
        """
        Elimina un usuario por su ID.
        """
        db_obj = await self.get(db, id)
        if not db_obj:
            raise NotFoundError(f"User with id {id} not found.")
        
        try:
            await db.delete(db_obj)
            await db.commit()
            return db_obj
        except Exception as e:
            await db.rollback()
            raise CRUDException(f"Error deleting User: {str(e)}") from e


# Crea una instancia de CRUDUser que se puede importar y usar en los routers
user = CRUDUser(User)
