# app/crud/user_roles.py 
from typing import Optional, List, Union, Dict, Any # Añadido Union, Dict, Any
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError as DBIntegrityError # Importa la excepción de integridad de SQLAlchemy

# Importa el modelo UserRole y los esquemas
from app.models.user_role import UserRole
from app.schemas.user_role import UserRoleCreate

# Importa los modelos necesarios para validación (User y Role)
from app.models.user import User
from app.models.role import Role

from app.crud.exceptions import NotFoundError, AlreadyExistsError, CRUDException

class CRUDUserRole:
    """
    Clase CRUD específica para la asociación UserRole.
    Gestiona la asignación y revocación de roles a usuarios.
    """
    def __init__(self, model):
        self.model = model

    async def get(self, db: AsyncSession, user_id: uuid.UUID, role_id: uuid.UUID) -> Optional[UserRole]:
        """
        Obtiene una asociación UserRole específica por IDs de usuario y rol,
        cargando los objetos User y Role asociados.
        """
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.user),
                selectinload(self.model.role),
                selectinload(self.model.assigned_by_user)
            )
            .filter(self.model.user_id == user_id, self.model.role_id == role_id)
        )
        return result.scalar_one_or_none()

    async def assign_role_to_user(self, db: AsyncSession, user_id: uuid.UUID, role_id: uuid.UUID, assigned_by_user_id: uuid.UUID) -> UserRole:
        """
        Asigna un rol a un usuario.
        Verifica si la asociación ya existe antes de crearla.
        """
        # Validar que el user_id, role_id y assigned_by_user_id existen
        user_exists_q = await db.execute(select(User).filter(User.id == user_id))
        if not user_exists_q.scalar_one_or_none():
            raise NotFoundError(f"User with ID {user_id} not found.")

        role_exists_q = await db.execute(select(Role).filter(Role.id == role_id))
        if not role_exists_q.scalar_one_or_none():
            raise NotFoundError(f"Role with ID {role_id} not found.")
        
        assigned_by_user_exists_q = await db.execute(select(User).filter(User.id == assigned_by_user_id))
        if not assigned_by_user_exists_q.scalar_one_or_none():
            raise NotFoundError(f"Assigned by user with ID {assigned_by_user_id} not found.")

        existing_association = await self.get(db, user_id, role_id)
        if existing_association:
            raise AlreadyExistsError(f"Role {role_id} is already assigned to user {user_id}.")

        try:
            # Crea una instancia del modelo UserRole
            db_obj = self.model(user_id=user_id, role_id=role_id, assigned_by_user_id=assigned_by_user_id)
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj) # Recarga para obtener assigned_at

            # Recargar con relaciones si la respuesta necesita más detalles
            reloaded_obj = await self.get(db, user_id, role_id)
            return reloaded_obj if reloaded_obj else db_obj

        except DBIntegrityError as e:
            await db.rollback()
            raise AlreadyExistsError(f"Error de integridad al asignar rol {role_id} a usuario {user_id}: {e}") from e
        except Exception as e:
            await db.rollback()
            if isinstance(e, (NotFoundError, AlreadyExistsError)):
                raise e
            raise CRUDException(f"Error assigning role {role_id} to user {user_id}: {str(e)}") from e
    
    async def remove_role_from_user(self, db: AsyncSession, user_id: uuid.UUID, role_id: uuid.UUID):
        """
        Remueve un rol de un usuario.
        """
        db_obj = await self.get(db, user_id, role_id)
        if not db_obj:
            raise NotFoundError(f"Role {role_id} is not assigned to user {user_id}.")

        try:
            await db.execute(
                delete(self.model).where(
                    self.model.user_id == user_id,
                    self.model.role_id == role_id
                )
            )
            await db.commit()
            return {"message": "Association removed successfully."}
        except Exception as e:
            await db.rollback()
            raise CRUDException(f"Error removing role {role_id} from user {user_id}: {str(e)}") from e
    
    async def get_roles_for_user(self, db: AsyncSession, user_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[UserRole]:
        """
        Obtiene todas las asociaciones de roles para un usuario específico,
        cargando los objetos Role y User asociados.
        """
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.role), # Carga el objeto Role asociado
                selectinload(self.model.user), # Carga el objeto User asociado (opcional, ya lo sabes)
                selectinload(self.model.assigned_by_user) # Carga el objeto de quien asignó
            )
            .filter(self.model.user_id == user_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

# Crea una instancia de CRUDUserRole que se puede importar y usar en los routers
user_role = CRUDUserRole(UserRole)
