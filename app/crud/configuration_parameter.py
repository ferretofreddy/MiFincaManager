# app/crud/configuration_parameter.py
from typing import Optional, List, Union, Dict, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload # Para cargar relaciones

from app.models.configuration_parameter import ConfigurationParameter # Importa el modelo
from app.schemas.configuration_parameter import ConfigurationParameterCreate, ConfigurationParameterUpdate # Importa los esquemas

from app.crud.base import CRUDBase # Importa la clase base CRUD
from app.crud.exceptions import NotFoundError, AlreadyExistsError, CRUDException

class CRUDConfigurationParameter(CRUDBase[ConfigurationParameter, ConfigurationParameterCreate, ConfigurationParameterUpdate]):
    """
    Clase CRUD específica para el modelo ConfigurationParameter.
    Implementa métodos específicos para ConfigurationParameter que requieren lógica adicional.
    """

    async def get_by_name(self, db: AsyncSession, name: str) -> Optional[ConfigurationParameter]:
        """
        Obtiene un parámetro de configuración por su nombre, cargando sus relaciones.
        """
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.data_type), # Carga la relación 'data_type' con MasterData
                selectinload(self.model.created_by_user) # Carga la relación 'created_by_user'
            )
            .filter(self.model.name == name)
        )
        return result.scalars().first()

    async def create(self, db: AsyncSession, *, obj_in: ConfigurationParameterCreate, created_by_user_id: UUID) -> ConfigurationParameter:
        """
        Crea un nuevo parámetro de configuración.
        Añade el created_by_user_id automáticamente.
        """
        # Asegúrate de que no exista otro parámetro con el mismo nombre
        existing_param = await self.get_by_name(db, name=obj_in.name)
        if existing_param:
            raise AlreadyExistsError(f"Configuration parameter with name '{obj_in.name}' already exists.")
        
        try:
            # Crea el objeto con los datos del esquema y el created_by_user_id
            db_obj = self.model(**obj_in.model_dump(), created_by_user_id=created_by_user_id)
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)

            # Recarga el objeto para asegurar que las relaciones estén cargadas si es necesario
            result = await db.execute(
                select(self.model)
                .options(
                    selectinload(self.model.data_type),
                    selectinload(self.model.created_by_user)
                )
                .filter(self.model.id == db_obj.id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            await db.rollback()
            raise CRUDException(f"Error creating ConfigurationParameter: {str(e)}") from e

    async def get(self, db: AsyncSession, id: UUID) -> Optional[ConfigurationParameter]:
        """
        Obtiene un parámetro de configuración por su ID, cargando sus relaciones.
        """
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.data_type),
                selectinload(self.model.created_by_user)
            )
            .filter(self.model.id == id)
        )
        return result.scalars().first()

    async def get_multi(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[ConfigurationParameter]:
        """
        Obtiene múltiples parámetros de configuración, cargando sus relaciones.
        """
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.data_type),
                selectinload(self.model.created_by_user)
            )
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def update(self, db: AsyncSession, *, db_obj: ConfigurationParameter, obj_in: Union[ConfigurationParameterUpdate, Dict[str, Any]]) -> ConfigurationParameter:
        """
        Actualiza un parámetro de configuración existente.
        """
        # Convierte obj_in a diccionario si es un esquema Pydantic para manejar los 'unset'
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        # Si el nombre se está actualizando, verifica unicidad
        if "name" in update_data and update_data["name"] != db_obj.name:
            existing_param = await self.get_by_name(db, name=update_data["name"])
            if existing_param and existing_param.id != db_obj.id:
                raise AlreadyExistsError(f"Configuration parameter with name '{update_data['name']}' already exists.")

        try:
            # Aplica la actualización usando el método base
            updated_param = await super().update(db, db_obj=db_obj, obj_in=update_data)

            # Recarga el objeto actualizado con las relaciones para la respuesta
            result = await db.execute(
                select(self.model)
                .options(
                    selectinload(self.model.data_type),
                    selectinload(self.model.created_by_user)
                )
                .filter(self.model.id == updated_param.id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            await db.rollback()
            raise CRUDException(f"Error updating ConfigurationParameter: {str(e)}") from e

    async def remove(self, db: AsyncSession, *, id: UUID) -> Optional[ConfigurationParameter]:
        """
        Elimina un parámetro de configuración por su ID.
        """
        db_obj = await self.get(db, id) # Primero obtenemos el objeto para asegurar que existe y para devolverlo
        if not db_obj:
            raise NotFoundError(f"ConfigurationParameter with id {id} not found.")
        
        try:
            await db.delete(db_obj)
            await db.commit()
            return db_obj # Retorna el objeto eliminado
        except Exception as e:
            await db.rollback()
            raise CRUDException(f"Error deleting ConfigurationParameter: {str(e)}") from e

# Instancia de la clase CRUD para ConfigurationParameter que se puede importar y usar en los routers
configuration_parameter = CRUDConfigurationParameter(ConfigurationParameter)

