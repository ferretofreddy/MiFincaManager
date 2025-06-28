# app/crud/user_roles.py 
from typing import Optional, List, Union, Dict, Any 
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError as DBIntegrityError 

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

    async def create(self, db: AsyncSession, *, obj_in: UserRoleCreate) -> UserRole:
        """
        Asigna un rol a un usuario, creando una nueva asociación UserRole.
        Lanza AlreadyExistsError si la asociación ya existe.
        """
        # Verificación temprana de existencia para lanzar un error específico
        existing_association = await self.get(db, user_id=obj_in.user_id, role_id=obj_in.role_id)
        if existing_association:
            raise AlreadyExistsError(f"Role {obj_in.role_id} is already assigned to user {obj_in.user_id}.")

        # Opcional: Validar que user_id, role_id y assigned_by_user_id realmente existen en la DB
        # Esto ya lo hacemos en el endpoint, así que no es estrictamente necesario aquí si siempre se usa el endpoint
        # pero es una buena capa de seguridad si el CRUD se llama directamente.
        
        # db_user_q = await db.execute(select(User).filter(User.id == obj_in.user_id))
        # db_user = db_user_q.scalars().first()
        # if not db_user:
        #     raise NotFoundError(f"User with ID {obj_in.user_id} not found.")

        # db_role_q = await db.execute(select(Role).filter(Role.id == obj_in.role_id))
        # db_role = db_role_q.scalars().first()
        # if not db_role:
        #     raise NotFoundError(f"Role with ID {obj_in.role_id} not found.")

        # db_assigner_q = await db.execute(select(User).filter(User.id == obj_in.assigned_by_user_id))
        # db_assigner = db_assigner_q.scalars().first()
        # if not db_assigner:
        #     raise NotFoundError(f"Assigning user with ID {obj_in.assigned_by_user_id} not found.")


        db_obj = UserRole(
            user_id=obj_in.user_id,
            role_id=obj_in.role_id,
            assigned_by_user_id=obj_in.assigned_by_user_id,
            assigned_at=datetime.utcnow() # Establecer la fecha de asignación
        )
        try:
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj) # Recargar el objeto para tener las relaciones cargadas
            return db_obj
        except DBIntegrityError as e:
            await db.rollback()
            # Esta excepción es útil si por alguna razón la verificación previa no bastó (concurrencia)
            # o si hay una FK que falla.
            raise AlreadyExistsError(f"Database integrity error: Association already exists or foreign key constraint failed. Detail: {e}")
        except Exception as e:
            await db.rollback()
            raise CRUDException(f"Error creating UserRole association: {str(e)}") from e

    async def remove_role_from_user(self, db: AsyncSession, *, user_id: uuid.UUID, role_id: uuid.UUID) -> Dict[str, str]:
        """
        Elimina una asociación de rol de un usuario.
        """
        # Primero, verifica si la asociación existe
        existing_association = await self.get(db, user_id=user_id, role_id=role_id)
        if not existing_association:
            raise NotFoundError(f"User Role association for User {user_id} and Role {role_id} not found.")

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
        return result.scalars().unique().all()

# Crea una instancia de la clase CRUDUserRole que se puede importar
# Esta línea es la que faltaba o estaba comentada.
user_role = CRUDUserRole(UserRole) 

