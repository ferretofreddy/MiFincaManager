# app/crud/base.py
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func # Importa func para funciones SQL como lower, count, etc.
from sqlalchemy.exc import IntegrityError as DBIntegrityError # Importa la excepción de integridad de SQLAlchemy

from app.db.base import Base # Importa la clase Base de tu configuración
from app.crud.exceptions import CRUDException, NotFoundError, AlreadyExistsError, IntegrityError # Importa las excepciones personalizadas


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
        try:
            # Crea una consulta para seleccionar el registro por su ID
            query = select(self.model).where(self.model.id == id)
            # Ejecuta la consulta y obtiene el resultado
            result = await db.execute(query)
            # Retorna el primer (y único) resultado, o None si no se encuentra
            return result.scalars().first()
        except Exception as e:
            raise CRUDException(f"Error retrieving record with ID {id} from {self.model.__tablename__}: {str(e)}") from e

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
        try:
            # Crea una consulta para seleccionar todos los registros, aplicando skip y limit
            query = select(self.model).offset(skip).limit(limit)
            # Ejecuta la consulta
            result = await db.execute(query)
            # Retorna todos los resultados como una lista
            return result.scalars().all()
        except Exception as e:
            raise CRUDException(f"Error retrieving multiple records from {self.model.__tablename__}: {str(e)}") from e


    async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType) -> ModelType:
        """
        Crea un nuevo registro en la base de datos.

        Args:
            db (AsyncSession): La sesión asíncrona de la base de datos.
            obj_in (CreateSchemaType): Un objeto Pydantic con los datos para la creación.

        Returns:
            ModelType: El objeto del modelo creado y persistido.
        """
        try:
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
        except DBIntegrityError as e:
            await db.rollback()
            # Intenta determinar si es un error de clave duplicada o similar
            # Esto puede requerir un análisis más profundo del mensaje de error o del contexto
            # Por simplicidad, se generaliza como AlreadyExistsError si hay un IntegrityError
            raise AlreadyExistsError(f"Integrity constraint violated during creation in {self.model.__tablename__}: {str(e)}") from e
        except Exception as e:
            await db.rollback()
            raise CRUDException(f"Error creating record in {self.model.__tablename__}: {str(e)}") from e


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
        try:
            # Convierte el objeto existente a un diccionario
            # obj_data = jsonable_encoder(db_obj) # No siempre necesario si solo actualizamos desde obj_in

            if isinstance(obj_in, dict):
                update_data = obj_in
            else:
                # Si es un esquema Pydantic, convierte a diccionario y filtra campos unset
                update_data = obj_in.model_dump(exclude_unset=True)

            # Itera sobre los datos de actualización y actualiza el objeto de la base de datos
            for field in update_data: # Itera solo sobre los campos que se desean actualizar
                setattr(db_obj, field, update_data[field])

            # Confirma los cambios y refresca el objeto
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            return db_obj
        except DBIntegrityError as e:
            await db.rollback()
            raise IntegrityError(f"Integrity constraint violated during update in {self.model.__tablename__}: {str(e)}") from e
        except Exception as e:
            await db.rollback()
            raise CRUDException(f"Error updating record in {self.model.__tablename__}: {str(e)}") from e


    async def remove(self, db: AsyncSession, *, id: UUID) -> Optional[ModelType]:
        """
        Elimina un registro por su ID.

        Args:
            db (AsyncSession): La sesión asíncrona de la base de datos.
            id (UUID): El UUID del registro a eliminar.

        Returns:
            Optional[ModelType]: El objeto del modelo eliminado si se encuentra, de lo contrario, None.
        """
        try:
            # Busca el objeto por ID
            query = select(self.model).where(self.model.id == id)
            result = await db.execute(query)
            obj = result.scalars().first()

            if obj:
                # Si el objeto existe, lo elimina
                await db.delete(obj)
                await db.commit()
                return obj
            # Si no se encuentra, podrías lanzar NotFoundError aquí o manejarlo en el router
            return None # Devolver None si no se encuentra es consistente con el tipo de retorno
        except Exception as e:
            await db.rollback()
            raise CRUDException(f"Error deleting record with ID {id} from {self.model.__tablename__}: {str(e)}") from e


    async def count(self, db: AsyncSession) -> int:
        """
        Cuenta el número total de registros para el modelo.

        Args:
            db (AsyncSession): La sesión asíncrona de la base de datos.

        Returns:
            int: El número total de registros.
        """
        try:
            # Crea una consulta para contar los registros
            result = await db.execute(select(func.count(self.model.id)))
            return result.scalar_one()
        except Exception as e:
            raise CRUDException(f"Error counting records in {self.model.__tablename__}: {str(e)}") from e

