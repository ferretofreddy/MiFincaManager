# app/crud/base.py
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func # Importa func para funciones SQL como lower, count, etc.

from app.db.base import Base # Importa la clase Base de tu configuración

# Define T como un TypeVar para representar un modelo de SQLAlchemy (Base)
ModelType = TypeVar("ModelType", bound=Base)
# Define CreateSchemaType como un TypeVar para los esquemas de creación de Pydantic
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
# Define UpdateSchemaType como un TypeVar para los esquemas de actualización de Pydantic
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Clase base para las operaciones CRUD (Crear, Leer, Actualizar, Eliminar) en modelos de SQLAlchemy.
    Proporciona métodos genéricos para interactuar con la base de datos.
    """

    def __init__(self, model: Type[ModelType]):
        """
        Constructor de la clase CRUDBase.

        Args:
            model (Type[ModelType]): El modelo de SQLAlchemy al que esta instancia CRUD está asociada.
                                     Ejemplo: `CRUDBase(User)` para operaciones con el modelo User.
        """
        self.model = model

    async def get(self, db: AsyncSession, id: UUID) -> Optional[ModelType]:
        """
        Obtiene un registro por su ID.

        Args:
            db (AsyncSession): La sesión asíncrona de la base de datos.
            id (UUID): El UUID del registro a obtener.

        Returns:
            Optional[ModelType]: El objeto del modelo si se encuentra, de lo contrario, None.
        """
        # Crea una consulta para seleccionar el registro por su ID
        query = select(self.model).where(self.model.id == id)
        # Ejecuta la consulta y obtiene el resultado
        result = await db.execute(query)
        # Retorna el primer (y único) resultado, o None si no se encuentra
        return result.scalars().first()

    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """
        Obtiene múltiples registros.

        Args:
            db (AsyncSession): La sesión asíncrona de la base de datos.
            skip (int): Número de registros a omitir (para paginación).
            limit (int): Número máximo de registros a devolver (para paginación).

        Returns:
            List[ModelType]: Una lista de objetos del modelo.
        """
        # Crea una consulta para seleccionar todos los registros, aplicando skip y limit
        query = select(self.model).offset(skip).limit(limit)
        # Ejecuta la consulta
        result = await db.execute(query)
        # Retorna todos los resultados como una lista
        return result.scalars().all()

    async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType) -> ModelType:
        """
        Crea un nuevo registro en la base de datos.

        Args:
            db (AsyncSession): La sesión asíncrona de la base de datos.
            obj_in (CreateSchemaType): Un objeto Pydantic con los datos para la creación.

        Returns:
            ModelType: El objeto del modelo creado y persistido.
        """
        # Convierte el objeto Pydantic a un diccionario, excluyendo campos unset si los hay
        obj_in_data = jsonable_encoder(obj_in)
        # Crea una instancia del modelo con los datos
        db_obj = self.model(**obj_in_data)
        # Añade el objeto a la sesión
        db.add(db_obj)
        # Confirma los cambios en la base de datos
        await db.commit()
        # Refresca el objeto para cargar los datos generados por la DB (ej. ID, created_at)
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """
        Actualiza un registro existente en la base de datos.

        Args:
            db (AsyncSession): La sesión asíncrona de la base de datos.
            db_obj (ModelType): La instancia del objeto del modelo a actualizar (obtenida de la DB).
            obj_in (Union[UpdateSchemaType, Dict[str, Any]]): Un objeto Pydantic con los datos de actualización
                                                                o un diccionario de campos a actualizar.

        Returns:
            ModelType: El objeto del modelo actualizado.
        """
        # Convierte el objeto existente a un diccionario
        obj_data = jsonable_encoder(db_obj)

        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            # Si es un esquema Pydantic, convierte a diccionario y filtra campos unset
            update_data = obj_in.model_dump(exclude_unset=True)

        # Itera sobre los datos de actualización y actualiza el objeto de la base de datos
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])

        # Confirma los cambios y refresca el objeto
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def remove(self, db: AsyncSession, *, id: UUID) -> Optional[ModelType]:
        """
        Elimina un registro por su ID.

        Args:
            db (AsyncSession): La sesión asíncrona de la base de datos.
            id (UUID): El UUID del registro a eliminar.

        Returns:
            Optional[ModelType]: El objeto del modelo eliminado si se encuentra, de lo contrario, None.
        """
        # Busca el objeto por ID
        query = select(self.model).where(self.model.id == id)
        result = await db.execute(query)
        obj = result.scalars().first()

        if obj:
            # Si el objeto existe, lo elimina
            await db.delete(obj)
            await db.commit()
            return obj
        return None

    async def count(self, db: AsyncSession) -> int:
        """
        Cuenta el número total de registros para el modelo.

        Args:
            db (AsyncSession): La sesión asíncrona de la base de datos.

        Returns:
            int: El número total de registros.
        """
        # Crea una consulta para contar los registros
        result = await db.execute(select(func.count(self.model.id)))
        return result.scalar_one()

