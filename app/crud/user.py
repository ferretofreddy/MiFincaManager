# app/crud/user.py
from typing import Optional, List, Union, Dict, Any 
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload 
from sqlalchemy.exc import IntegrityError as DBIntegrityError 

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

    # Helper para cargar todas las relaciones del usuario
    def _get_user_with_relationships_query(self):
        return select(self.model).options(
            selectinload(self.model.farms_owned),
            selectinload(self.model.animals_owned),
            selectinload(self.model.farm_accesses),
            selectinload(self.model.accesses_assigned),
            selectinload(self.model.master_data_created),
            selectinload(self.model.health_events_administered),
            selectinload(self.model.reproductive_events_administered),
            selectinload(self.model.offspring_born),
            selectinload(self.model.weighings_recorded),
            selectinload(self.model.feedings_recorded),
            selectinload(self.model.transactions_recorded),
            selectinload(self.model.batches_created),
            selectinload(self.model.grupos_created),
            selectinload(self.model.animal_groups_created),
            selectinload(self.model.animal_location_history_created),
            selectinload(self.model.products_created),
            selectinload(self.model.roles_assigned_to_user),
            selectinload(self.model.user_roles_associations),
            selectinload(self.model.assigned_roles),
            selectinload(self.model.configuration_parameters_created),
            selectinload(self.model.roles_created) 
        )

    async def get(self, db: AsyncSession, id: uuid.UUID) -> Optional[User]:
        """
        Obtiene un usuario por su ID, cargando todas sus relaciones.
        """
        result = await db.execute(
            self._get_user_with_relationships_query().filter(self.model.id == id)
        )
        return result.scalars().first()

    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """
        Obtiene un usuario por su dirección de correo electrónico, cargando todas sus relaciones.
        """
        result = await db.execute(
            self._get_user_with_relationships_query().filter(self.model.email == email)
        )
        return result.scalars().first()


    async def get_multi(self, db: AsyncSession, *, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Obtiene múltiples registros de usuario con paginación, cargando todas las relaciones.
        """
        result = await db.execute(
            self._get_user_with_relationships_query()
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().unique().all()


    async def create(self, db: AsyncSession, *, obj_in: UserCreate) -> User:
        """
        Crea un nuevo usuario, hasheando la contraseña antes de guardar.
        Después de la creación, recarga el objeto con todas las relaciones.
        """
        existing_user = await self.get_by_email(db, email=obj_in.email) # get_by_email ya carga relaciones
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
                city=obj_in.city,
                is_superuser=obj_in.is_superuser,
                is_active=obj_in.is_active
            )
            db.add(db_obj)
            await db.commit()
            
            # Recarga el objeto con todas las relaciones
            return await self.get(db, db_obj.id) # Reutiliza el método get para cargar
            
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

            if "password" in update_data and update_data["password"]:
                update_data["hashed_password"] = get_password_hash(update_data["password"])
                del update_data["password"] 
            elif "hashed_password" in update_data:
                pass
            
            if "email" in update_data and update_data["email"] != db_obj.email:
                existing_user = await self.get_by_email(db, email=update_data["email"]) # get_by_email ya carga relaciones
                if existing_user and existing_user.id != db_obj.id: 
                    raise AlreadyExistsError(f"User with email '{update_data['email']}' already exists.")

            updated_user = await super().update(db, db_obj=db_obj, obj_in=update_data)
            
            # Recarga el objeto para asegurar que todas las relaciones estén cargadas para la respuesta
            return await self.get(db, updated_user.id) # Reutiliza el método get para cargar

        except Exception as e:
            await db.rollback()
            if isinstance(e, AlreadyExistsError) or isinstance(e, NotFoundError) or isinstance(e, CRUDException):
                raise e
            raise CRUDException(f"Error updating User: {str(e)}") from e

    async def remove(self, db: AsyncSession, *, id: uuid.UUID) -> Optional[User]:
        """
        Elimina un usuario por su ID.
        """
        db_obj = await self.get(db, id) # get ahora carga relaciones
        if not db_obj:
            raise NotFoundError(f"User with id {id} not found.")
        
        try:
            await db.delete(db_obj)
            await db.commit()
            return db_obj # Retorna el objeto eliminado, sus relaciones ya deberían estar cargadas si se obtuvo con get()
        except Exception as e:
            await db.rollback()
            raise CRUDException(f"Error deleting User: {str(e)}") from e

user = CRUDUser(User)
