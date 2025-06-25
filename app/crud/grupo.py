# app/crud/grupo.py
from typing import Optional, List, Union, Dict, Any # Añadido Union, Dict, Any
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError as DBIntegrityError # Importa la excepción de integridad de SQLAlchemy

# Importa el modelo Grupo y los esquemas de grupo
from app.models.grupo import Grupo
from app.models.master_data import MasterData # Importado para validación
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
        existing_grupo_q = await db.execute(
            select(Grupo).filter(
                and_(Grupo.name == obj_in.name, Grupo.created_by_user_id == created_by_user_id)
            )
        )
        if existing_grupo_q.scalar_one_or_none():
            raise AlreadyExistsError(f"Group with name '{obj_in.name}' already exists for this user.")

        try:
            # Validar purpose_id si se proporciona
            if obj_in.purpose_id:
                purpose_md_q = await db.execute(select(MasterData).filter(MasterData.id == obj_in.purpose_id))
                purpose_md = purpose_md_q.scalar_one_or_none()
                if not purpose_md:
                    raise NotFoundError(f"MasterData with ID {obj_in.purpose_id} for purpose not found.")
                # Opcional: Validar categoría del MasterData si es necesario
                # if purpose_md.category != "purpose_category_expected":
                #     raise CRUDException("Invalid category for purpose_id.")

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
        except DBIntegrityError as e: # Captura errores de integridad de la DB
            await db.rollback()
            raise AlreadyExistsError(f"Error de integridad al crear Grupo: {e}") from e
        except Exception as e:
            await db.rollback()
            if isinstance(e, NotFoundError) or isinstance(e, AlreadyExistsError):
                raise e
            raise CRUDException(f"Error creating Grupo: {str(e)}") from e

    async def get(self, db: AsyncSession, id: uuid.UUID) -> Optional[Grupo]: # Cambiado grupo_id a id
        """
        Obtiene un grupo por su ID, cargando las relaciones con el propósito y el usuario creador.
        """
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.purpose),
                selectinload(self.model.created_by_user)
            )
            .filter(self.model.id == id) # Cambiado grupo_id a id
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

    async def update(self, db: AsyncSession, *, db_obj: Grupo, obj_in: Union[GrupoUpdate, Dict[str, Any]]) -> Grupo: # Añadido Union, Dict, Any
        """
        Actualiza un grupo existente.
        Después de la actualización, recarga el objeto con las relaciones necesarias.
        """
        try:
            # Si obj_in es un Pydantic model, conviértelo a dict y excluye unset
            if isinstance(obj_in, dict):
                update_data = obj_in
            else:
                update_data = obj_in.model_dump(exclude_unset=True)

            # Si el nombre se está actualizando, verifica unicidad por usuario
            if "name" in update_data and update_data["name"] != db_obj.name:
                existing_grupo_q = await db.execute(
                    select(Grupo).filter(
                        and_(Grupo.name == update_data["name"], Grupo.created_by_user_id == db_obj.created_by_user_id, Grupo.id != db_obj.id)
                    )
                )
                if existing_grupo_q.scalar_one_or_none():
                    raise AlreadyExistsError(f"Group with name '{update_data['name']}' already exists for this user.")
            
            # Validar purpose_id si se proporciona y es diferente
            if "purpose_id" in update_data and update_data["purpose_id"] != db_obj.purpose_id:
                purpose_md_q = await db.execute(select(MasterData).filter(MasterData.id == update_data["purpose_id"]))
                if not purpose_md_q.scalar_one_or_none():
                    raise NotFoundError(f"MasterData with ID {update_data['purpose_id']} for new purpose not found.")

            updated_grupo = await super().update(db, db_obj=db_obj, obj_in=update_data)
            if updated_grupo:
                result = await db.execute(
                    select(self.model)
                    .options(
                        selectinload(self.model.purpose),
                        selectinload(self.model.created_by_user)
                    )
                    .filter(self.model.id == updated_grupo.id)
                )
                return result.scalars().first()
            return updated_grupo
        except Exception as e:
            await db.rollback()
            if isinstance(e, NotFoundError) or isinstance(e, AlreadyExistsError) or isinstance(e, CRUDException):
                raise e
            raise CRUDException(f"Error updating Grupo: {str(e)}") from e
    
    async def remove(self, db: AsyncSession, *, id: uuid.UUID) -> Optional[Grupo]:
        """
        Elimina un grupo por su ID.
        """
        db_obj = await self.get(db, id)
        if not db_obj:
            raise NotFoundError(f"Grupo with id {id} not found.")
        
        try:
            await db.delete(db_obj)
            await db.commit()
            return db_obj
        except Exception as e:
            await db.rollback()
            raise CRUDException(f"Error deleting Grupo: {str(e)}") from e


# Crea una instancia de CRUDGrupo que se puede importar y usar en los routers
grupo = CRUDGrupo(Grupo)
