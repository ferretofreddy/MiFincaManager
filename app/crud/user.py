# app/crud/user.py
from typing import Optional, List, Union, Dict, Any 
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError as DBIntegrityError 

# Importa el modelo User y los esquemas de user
from app.models.user import User
# Asegúrate de que UserCreate ahora espera 'password'
from app.schemas.user import UserCreate, UserUpdate 

# Importa la CRUDBase, get_password_hash y las excepciones
from app.crud.base import CRUDBase
from app.crud.exceptions import NotFoundError, AlreadyExistsError, CRUDException
from app.core.security import get_password_hash # Esta función se usará aquí para hashear

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
        Crea un nuevo usuario, hasheando la contraseña antes de guardar.
        obj_in.password ahora es el texto plano.
        """
        existing_user = await self.get_by_email(db, email=obj_in.email)
        if existing_user:
            raise AlreadyExistsError(f"User with email '{obj_in.email}' already exists.")

        try:
            # === ¡CORRECCIÓN CLAVE AQUÍ! Hashear la contraseña recibida en texto plano ===
            hashed_password = get_password_hash(obj_in.password)
            
            db_obj = self.model(
                email=obj_in.email,
                hashed_password=hashed_password, # Asigna el hash al campo hashed_password del modelo
                first_name=obj_in.first_name,
                last_name=obj_in.last_name,
                phone_number=obj_in.phone_number,
                address=obj_in.address,
                country=obj_in.country,
                city=obj_in.city,
                is_superuser=obj_in.is_superuser,
                is_active=obj_in.is_active
            )
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj) 
            return db_obj
        except DBIntegrityError as e:
            await db.rollback()
            raise AlreadyExistsError(f"Error de integridad al crear User: {e}") from e
        except Exception as e:
            await db.rollback()
            if isinstance(e, AlreadyExistsError): 
                raise e
            raise CRUDException(f"Error creating User: {str(e)}") from e

    async def update(self, db: AsyncSession, *, db_obj: User, obj_in: Union[UserUpdate, Dict[str, Any]]) -> User: 
        """
        Actualiza un usuario existente, manejando el hashing de la contraseña si se proporciona.
        obj_in puede tener 'password' o 'hashed_password' para actualización.
        """
        try:
            if isinstance(obj_in, dict):
                update_data = obj_in
            else:
                update_data = obj_in.model_dump(exclude_unset=True)

            # Si 'password' se proporciona en la actualización, se hashea y se usa para hashed_password
            if "password" in update_data and update_data["password"]:
                update_data["hashed_password"] = get_password_hash(update_data["password"])
                del update_data["password"] # Elimina el campo de texto plano de la actualización
            # Si 'hashed_password' se proporciona directamente (ej. por otra fuente que ya lo tiene hasheado)
            elif "hashed_password" in update_data:
                # No se necesita hashear, ya viene hasheada. Se mantiene.
                pass
            
            if "email" in update_data and update_data["email"] != db_obj.email:
                existing_user = await self.get_by_email(db, email=update_data["email"])
                if existing_user and existing_user.id != db_obj.id: 
                    raise AlreadyExistsError(f"User with email '{update_data['email']}' already exists.")

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

user = CRUDUser(User)
