# app/crud/grupos.py
from typing import Optional, List
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import and_ # Importa 'and_' para combinaciones de filtros

# Importa el modelo Grupo y los esquemas de grupo
from app.models.grupo import Grupo
from app.schemas.grupo import GrupoCreate, GrupoUpdate

# Importa la CRUDBase y las excepciones
from app.crud.base import CRUDBase
from app.crud.exceptions import NotFoundError, AlreadyExistsError, CRUDException

class CRUDGrupo(CRUDBase[Grupo, GrupoCreate, GrupoUpdate]):
    """
    Clase CRUD específica para el modelo Grupo.
    Hereda la mayoría de las operaciones de CRUDBase.
    Implementa métodos específicos para Grupo que requieren lógica adicional.
    """

    async def create(self, db: AsyncSession, *, obj_in: GrupoCreate, created_by_user_id: uuid.UUID) -> Grupo:
        """
        Crea un nuevo grupo.
        created_by_user_id es un parámetro adicional.
        Verifica la unicidad del nombre del grupo por usuario.
        """
        # Verifica si ya existe un grupo con el mismo nombre creado por el mismo usuario
        existing_grupo = await db.execute(
            select(Grupo).filter(
                and_(Grupo.name == obj_in.name, Grupo.created_by_user_id == created_by_user_id)
            )
        )
        if existing_grupo.scalar_one_or_none():
            raise AlreadyExistsError(f"Group with name '{obj_in.name}' already exists for this user.")

        try:
            db_obj = self.model(**obj_in.model_dump(), created_by_user_id=created_by_user_id)
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj) # Obtiene el ID, created_at, updated_at
            
            # Recarga el grupo con sus relaciones para la respuesta
            result = await db.execute(
                select(Grupo)
                .options(
                    selectinload(Grupo.purpose),
                    selectinload(Grupo.created_by_user)
                )
                .filter(Grupo.id == db_obj.id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            await db.rollback()
            raise CRUDException(f"Error creating Grupo: {str(e)}") from e

    async def get(self, db: AsyncSession, grupo_id: uuid.UUID) -> Optional[Grupo]:
        """
        Obtiene un grupo por su ID, cargando las relaciones con el propósito y el usuario creador.
        """
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.purpose),
                selectinload(self.model.created_by_user)
            )
            .filter(self.model.id == grupo_id)
        )
        return result.scalar_one_or_none()
    
    async def get_multi_by_created_by_user_id(self, db: AsyncSession, created_by_user_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[Grupo]:
        """
        Obtiene una lista de grupos creados por un usuario específico.
        """
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.purpose),
                selectinload(self.model.created_by_user)
            )
            .filter(self.model.created_by_user_id == created_by_user_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def update(self, db: AsyncSession, *, db_obj: Grupo, obj_in: GrupoUpdate) -> Grupo:
        """
        Actualiza un grupo existente.
        Después de la actualización, recarga el objeto con las relaciones necesarias.
        """
        updated_grupo = await super().update(db, db_obj=db_obj, obj_in=obj_in)
        if updated_grupo:
            result = await db.execute(
                select(self.model)
                .options(
                    selectinload(self.model.purpose),
                    selectinload(self.model.created_by_user)
                )
                .filter(self.model.id == updated_grupo.id)
            )
            return result.scalar_one_or_none()
        return updated_grupo

# Crea una instancia de CRUDGrupo que se puede importar y usar en los routers
grupo = CRUDGrupo(Grupo)
