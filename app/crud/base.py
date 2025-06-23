# app/crud/base.py
# Define una clase CRUDBase genérica para operaciones CRUD comunes.

from typing import Type, TypeVar, Any, Generic, Optional, List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, and_ # Importa 'and_' para combinar filtros

from pydantic import BaseModel

from app.crud.exceptions import CRUDException, NotFoundError, AlreadyExistsError, IntegrityError

# Define tipos genéricos para el modelo de SQLAlchemy, el esquema de creación y el esquema de actualización.
ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Clase base genérica para operaciones CRUD (Crear, Leer, Actualizar, Eliminar).
    Proporciona métodos estándar para interactuar con un modelo de base de datos.
    """
    def __init__(self, model: Type[ModelType]):
        """
        Constructor de CRUDBase.
        model: La clase del modelo de SQLAlchemy (ej. models.User).
        """
        self.model = model

    async def get(self, db: AsyncSession, id: Any) -> Optional[ModelType]:
        """
        Obtiene un registro por su ID.
        db: La sesión de la base de datos.
        id: El ID del registro.
        Retorna el objeto del modelo o None si no se encuentra.
        """
        result = await db.execute(select(self.model).filter(self.model.id == id))
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None # Soporte para filtros dinámicos
    ) -> List[ModelType]:
        """
        Obtiene una lista de registros.
        db: La sesión de la base de datos.
        skip: Número de registros a omitir.
        limit: Número máximo de registros a retornar.
        filters: Opcional. Diccionario de filtros a aplicar (ej. {"name": "Test"}).
        Retorna una lista de objetos del modelo.
        """
        query = select(self.model)

        if filters:
            conditions = []
            for field, value in filters.items():
                # Asegura que el campo exista en el modelo antes de intentar filtrar
                if hasattr(self.model, field):
                    conditions.append(getattr(self.model, field) == value)
            if conditions:
                query = query.where(and_(*conditions)) # Aplica todos los filtros con AND

        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType) -> ModelType:
        """
        Crea un nuevo registro en la base de datos.
        db: La sesión de la base de datos.
        obj_in: Objeto Pydantic con los datos para crear el registro.
        Retorna el objeto del modelo creado.
        Lanza CRUDException en caso de error.
        """
        try:
            # Convierte el esquema Pydantic a un diccionario para inicializar el modelo SQLAlchemy
            obj_in_data = obj_in.model_dump()
            db_obj = self.model(**obj_in_data)
            
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj) # Recarga el objeto para obtener los valores generados por la DB (ej. ID, created_at)
            return db_obj
        except Exception as e:
            await db.rollback() # Revierte la transacción en caso de error
            # Si el error es por una restricción única, puedes lanzar AlreadyExistsError
            # Esto puede requerir un análisis más profundo del tipo de excepción de la DB (ej. IntegrityError para PostgreSQL)
            if "duplicate key value" in str(e).lower() or "unique constraint" in str(e).lower():
                raise AlreadyExistsError(f"{self.model.__name__} already exists or unique constraint violated.") from e
            if "violates foreign key" in str(e).lower():
                raise IntegrityError(f"Integrity error when creating {self.model.__name__}: {str(e)}") from e
            raise CRUDException(f"Error creating {self.model.__name__}: {str(e)}") from e

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,          # Instancia del modelo existente para actualizar
        obj_in: UpdateSchemaType | Dict[str, Any] # Datos de actualización (esquema Pydantic o diccionario)
    ) -> ModelType:
        """
        Actualiza un registro existente.
        db: La sesión de la base de datos.
        db_obj: La instancia del modelo de SQLAlchemy a actualizar.
        obj_in: Objeto Pydantic con los datos de actualización (solo los campos que deben cambiarse).
        Retorna el objeto del modelo actualizado.
        Lanza CRUDException en caso de error.
        """
        try:
            if isinstance(obj_in, dict):
                update_data = obj_in
            else:
                # model_dump(exclude_unset=True) para actualizar solo los campos proporcionados
                update_data = obj_in.model_dump(exclude_unset=True)

            for field, value in update_data.items():
                # Actualiza solo si el campo existe en el modelo
                if hasattr(db_obj, field):
                    setattr(db_obj, field, value)

            await db.commit()
            await db.refresh(db_obj) # Recarga el objeto para obtener los valores actualizados (ej. updated_at)
            return db_obj
        except Exception as e:
            await db.rollback()
            raise CRUDException(f"Error updating {self.model.__name__}: {str(e)}") from e

    async def remove(self, db: AsyncSession, *, id: Any) -> bool:
        """
        Elimina un registro por su ID.
        db: La sesión de la base de datos.
        id: El ID del registro a eliminar.
        Retorna True si se eliminó, lanza NotFoundError si no se encuentra.
        Lanza CRUDException en caso de otros errores.
        """
        db_obj = await self.get(db, id)
        if not db_obj:
            raise NotFoundError(f"{self.model.__name__} with ID {id} not found")

        try:
            await db.delete(db_obj)
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            # Podrías querer manejar IntegrityError si la eliminación causa problemas de FK
            if "violates foreign key" in str(e).lower():
                raise IntegrityError(f"Cannot delete {self.model.__name__} due to existing related records: {str(e)}") from e
            raise CRUDException(f"Error deleting {self.model.__name__}: {str(e)}") from e

    async def count(self, db: AsyncSession, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Cuenta el número de registros, opcionalmente aplicando filtros.
        db: La sesión de la base de datos.
        filters: Opcional. Diccionario de filtros a aplicar.
        Retorna el número total de registros.
        """
        query = select(func.count()).select_from(self.model)

        if filters:
            conditions = []
            for field, value in filters.items():
                if hasattr(self.model, field):
                    conditions.append(getattr(self.model, field) == value)
            if conditions:
                query = query.where(and_(*conditions))

        result = await db.execute(query)
        return result.scalar_one()
