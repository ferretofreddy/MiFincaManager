# app/crud/animal_group.py
from typing import Optional, List, Union, Dict, Any
import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError as DBIntegrityError

from app.models.animal_group import AnimalGroup
from app.schemas.animal_group import AnimalGroupCreate, AnimalGroupUpdate

from app.crud.base import CRUDBase
from app.crud.exceptions import NotFoundError, AlreadyExistsError, CRUDException

class CRUDAnimalGroup(CRUDBase[AnimalGroup, AnimalGroupCreate, AnimalGroupUpdate]):
    """
    Clase CRUD específica para el modelo AnimalGroup.
    Gestiona la asociación de animales a grupos.
    """
    async def create(self, db: AsyncSession, *, obj_in: AnimalGroupCreate, created_by_user_id: uuid.UUID) -> AnimalGroup:
        """
        Crea una nueva asociación de animal a grupo.
        Puedes añadir lógica aquí para asegurar que no haya superposiciones de fechas
        o si un animal no puede estar en múltiples asociaciones activas
        (removed_at is NULL) con el mismo grupo al mismo tiempo.
        """
        # Opcional: Verificar si el animal ya tiene una asociación *activa* con este grupo
        # o si el animal ya está en *cualquier* grupo activo si esa es la regla de negocio.
        # Si la combinación (animal_id, group_id, removed_at is NULL) debe ser única:
        existing_active_association = await db.execute(
            select(AnimalGroup).filter(
                and_(
                    AnimalGroup.animal_id == obj_in.animal_id,
                    AnimalGroup.group_id == obj_in.group_id,
                    AnimalGroup.removed_at.is_(None)
                )
            )
        )
        if existing_active_association.scalar_one_or_none():
            raise AlreadyExistsError(f"Animal '{obj_in.animal_id}' is already in an active association with group '{obj_in.group_id}'.")

        try:
            # Si assigned_at no se proporciona en obj_in, se usa el default_factory del modelo
            db_obj = self.model(**obj_in.model_dump(), created_by_user_id=created_by_user_id)
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            
            # Recarga la asociación con las relaciones
            result = await db.execute(
                select(AnimalGroup)
                .options(
                    selectinload(AnimalGroup.animal),
                    selectinload(AnimalGroup.grupo),
                    selectinload(AnimalGroup.created_by_user)
                )
                .filter(AnimalGroup.id == db_obj.id)
            )
            return result.scalar_one_or_none()
        except DBIntegrityError as e:
            await db.rollback()
            raise AlreadyExistsError(f"Error de integridad al crear AnimalGroup: {e}") from e
        except Exception as e:
            await db.rollback()
            raise CRUDException(f"Error creating AnimalGroup: {str(e)}") from e

    async def get(self, db: AsyncSession, id: uuid.UUID) -> Optional[AnimalGroup]:
        """
        Obtiene una asociación AnimalGroup por su ID, cargando las relaciones.
        """
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.animal),
                selectinload(self.model.grupo),
                selectinload(self.model.created_by_user)
            )
            .filter(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_compound_keys(self, db: AsyncSession, animal_id: uuid.UUID, group_id: uuid.UUID, assigned_at: datetime) -> Optional[AnimalGroup]:
        """
        Obtiene una asociación AnimalGroup por sus claves compuestas (animal_id, group_id, assigned_at).
        Útil si aún necesitas esta forma de búsqueda.
        """
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.animal),
                selectinload(self.model.grupo),
                selectinload(self.model.created_by_user)
            )
            .filter(
                and_(
                    self.model.animal_id == animal_id,
                    self.model.group_id == group_id,
                    self.model.assigned_at == assigned_at
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_multi_by_animal_id(self, db: AsyncSession, animal_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[AnimalGroup]:
        """
        Obtiene todas las asociaciones de grupo para un animal específico.
        """
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.animal),
                selectinload(self.model.grupo),
                selectinload(self.model.created_by_user)
            )
            .filter(self.model.animal_id == animal_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_multi_by_group_id(self, db: AsyncSession, group_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[AnimalGroup]:
        """
        Obtiene todas las asociaciones de animales para un grupo específico.
        """
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.animal),
                selectinload(self.model.grupo),
                selectinload(self.model.created_by_user)
            )
            .filter(self.model.group_id == group_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def update(self, db: AsyncSession, *, db_obj: AnimalGroup, obj_in: Union[AnimalGroupUpdate, Dict[str, Any]]) -> AnimalGroup:
        """
        Actualiza una asociación AnimalGroup existente.
        Se usa principalmente para establecer 'removed_at'.
        """
        try:
            # Si obj_in es un Pydantic model, conviértelo a dict y excluye unset
            if isinstance(obj_in, dict):
                update_data = obj_in
            else:
                update_data = obj_in.model_dump(exclude_unset=True)

            updated_animal_group = await super().update(db, db_obj=db_obj, obj_in=update_data)
            if updated_animal_group:
                result = await db.execute(
                    select(self.model)
                    .options(
                        selectinload(self.model.animal),
                        selectinload(self.model.grupo),
                        selectinload(self.model.created_by_user)
                    )
                    .filter(self.model.id == updated_animal_group.id)
                )
                return result.scalars().first()
            return updated_animal_group
        except Exception as e:
            await db.rollback()
            raise CRUDException(f"Error updating AnimalGroup: {str(e)}") from e

    async def remove(self, db: AsyncSession, *, id: uuid.UUID) -> Optional[AnimalGroup]:
        """
        Elimina una asociación AnimalGroup por su ID.
        """
        db_obj = await self.get(db, id)
        if not db_obj:
            raise NotFoundError(f"AnimalGroup association with id {id} not found.")
        
        try:
            await db.delete(db_obj)
            await db.commit()
            return db_obj
        except Exception as e:
            await db.rollback()
            raise CRUDException(f"Error deleting AnimalGroup association: {str(e)}") from e


# Crea una instancia de CRUDAnimalGroup que se puede importar y usar en los routers
animal_group = CRUDAnimalGroup(AnimalGroup)
