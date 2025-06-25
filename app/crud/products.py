# app/crud/products.py
from typing import Optional, List, Union, Dict, Any # Añadido Union, Dict, Any
import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError as DBIntegrityError # Importa la excepción de integridad de SQLAlchemy


# Importa el modelo Product y los esquemas
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate

# Importa modelos para validación de IDs foráneos
from app.models.master_data import MasterData
from app.models.farm import Farm

# Importa la CRUDBase y las excepciones
from app.crud.base import CRUDBase
from app.crud.exceptions import NotFoundError, AlreadyExistsError, CRUDException

class CRUDProduct(CRUDBase[Product, ProductCreate, ProductUpdate]):
    """
    Clase CRUD específica para el modelo Product.
    Gestiona los registros de productos e inventario.
    """

    async def _validate_foreign_keys(self, db: AsyncSession, obj_in: Union[ProductCreate, ProductUpdate]):
        """
        Valida que los IDs foráneos de MasterData y Farm existan.
        """
        # Validar product_type_id
        if obj_in.product_type_id:
            md_type_q = await db.execute(select(MasterData).filter(MasterData.id == obj_in.product_type_id))
            md_type = md_type_q.scalar_one_or_none()
            if not md_type:
                raise NotFoundError(f"MasterData with ID {obj_in.product_type_id} (product_type_id) not found.")
            if md_type.category != "product_type": # Asumiendo que "product_type" es la categoría esperada
                raise CRUDException(f"MasterData with ID {obj_in.product_type_id} is not of category 'product_type'.")
        
        # Validar unit_id
        if obj_in.unit_id:
            md_unit_q = await db.execute(select(MasterData).filter(MasterData.id == obj_in.unit_id))
            md_unit = md_unit_q.scalar_one_or_none()
            if not md_unit:
                raise NotFoundError(f"MasterData with ID {obj_in.unit_id} (unit_id) not found.")
            if md_unit.category != "unit_of_measure": # Asumiendo que "unit_of_measure" es la categoría esperada
                raise CRUDException(f"MasterData with ID {obj_in.unit_id} is not of category 'unit_of_measure'.")
        
        # Validar farm_id
        if obj_in.farm_id:
            farm_q = await db.execute(select(Farm).filter(Farm.id == obj_in.farm_id))
            if not farm_q.scalar_one_or_none():
                raise NotFoundError(f"Farm with ID {obj_in.farm_id} not found.")

    async def create(self, db: AsyncSession, *, obj_in: ProductCreate, created_by_user_id: uuid.UUID) -> Product:
        """
        Crea un nuevo registro de producto.
        """
        try:
            # Validar todas las claves foráneas
            await self._validate_foreign_keys(db, obj_in)

            # Opcional: Verificar unicidad del nombre del producto por finca (o globalmente)
            existing_product_q = await db.execute(
                select(Product).filter(and_(
                    Product.name == obj_in.name,
                    Product.farm_id == obj_in.farm_id # Unicidad por finca
                ))
            )
            if existing_product_q.scalar_one_or_none():
                raise AlreadyExistsError(f"Product with name '{obj_in.name}' already exists in farm {obj_in.farm_id}.")

            db_product = self.model(**obj_in.model_dump(), created_by_user_id=created_by_user_id)
            db.add(db_product)
            await db.commit()
            await db.refresh(db_product)
            
            # Recargar el producto con las relaciones para la respuesta
            result = await db.execute(
                select(Product)
                .options(
                    selectinload(Product.product_type),
                    selectinload(Product.unit),
                    selectinload(Product.farm),
                    selectinload(Product.created_by_user)
                )
                .filter(Product.id == db_product.id)
            )
            return result.scalar_one_or_none()
        except DBIntegrityError as e: # Captura errores de integridad de la DB
            await db.rollback()
            raise AlreadyExistsError(f"Error de integridad al crear Product record: {e}") from e
        except Exception as e:
            await db.rollback()
            if isinstance(e, (NotFoundError, AlreadyExistsError, CRUDException)):
                raise e
            raise CRUDException(f"Error creating Product record: {str(e)}") from e

    async def get(self, db: AsyncSession, id: uuid.UUID) -> Optional[Product]: # Cambiado product_id a id
        """
        Obtiene un registro de producto por su ID, cargando las relaciones.
        """
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.product_type),
                selectinload(self.model.unit),
                selectinload(self.model.farm),
                selectinload(self.model.created_by_user)
            )
            .filter(self.model.id == id) # Cambiado product_id a id
        )
        return result.scalar_one_or_none()

    async def get_multi_by_farm_id(self, db: AsyncSession, farm_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[Product]:
        """
        Obtiene todos los productos asociados a una finca específica.
        """
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.product_type),
                selectinload(self.model.unit),
                selectinload(self.model.farm),
                selectinload(self.model.created_by_user)
            )
            .filter(self.model.farm_id == farm_id)
            .order_by(self.model.name)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def update(self, db: AsyncSession, *, db_obj: Product, obj_in: Union[ProductUpdate, Dict[str, Any]]) -> Product: # Añadido Union, Dict, Any
        """
        Actualiza un registro de producto existente.
        """
        try:
            # Si obj_in es un Pydantic model, conviértelo a dict y excluye unset
            if isinstance(obj_in, dict):
                update_data = obj_in
            else:
                update_data = obj_in.model_dump(exclude_unset=True)

            # Validar claves foráneas si se proporcionan en la actualización
            # Crea un objeto temporal ProductCreate/Update para usar en _validate_foreign_keys
            # Asegúrate de pasar solo los campos que se están actualizando o los actuales de db_obj
            temp_obj_in = ProductUpdate(
                product_type_id=update_data.get("product_type_id", db_obj.product_type_id),
                unit_id=update_data.get("unit_id", db_obj.unit_id),
                farm_id=update_data.get("farm_id", db_obj.farm_id)
            )
            await self._validate_foreign_keys(db, temp_obj_in)

            # Si se intenta cambiar el nombre y/o la finca, verificar unicidad
            name_changed = "name" in update_data and update_data["name"] != db_obj.name
            farm_changed = "farm_id" in update_data and update_data["farm_id"] != db_obj.farm_id

            if name_changed or farm_changed:
                target_name = update_data.get("name", db_obj.name)
                target_farm_id = update_data.get("farm_id", db_obj.farm_id)
                
                existing_product_q = await db.execute(
                    select(Product).filter(and_(
                        Product.name == target_name,
                        Product.farm_id == target_farm_id,
                        Product.id != db_obj.id # Excluir el propio objeto
                    ))
                )
                if existing_product_q.scalar_one_or_none():
                    raise AlreadyExistsError(f"Product with name '{target_name}' already exists in farm {target_farm_id}.")

            updated_product = await super().update(db, db_obj=db_obj, obj_in=update_data)
            if updated_product:
                result = await db.execute(
                    select(self.model)
                    .options(
                        selectinload(self.model.product_type),
                        selectinload(self.model.unit),
                        selectinload(self.model.farm),
                        selectinload(self.model.created_by_user)
                    )
                    .filter(self.model.id == updated_product.id)
                )
                return result.scalars().first()
            return updated_product
        except Exception as e:
            await db.rollback()
            if isinstance(e, (NotFoundError, AlreadyExistsError, CRUDException)):
                raise e
            raise CRUDException(f"Error updating Product record: {str(e)}") from e

    async def remove(self, db: AsyncSession, *, id: uuid.UUID) -> Optional[Product]: # Cambiado delete a remove
        """
        Elimina un registro de producto por su ID.
        """
        db_obj = await self.get(db, id) # Primero obtenemos el objeto para asegurar que existe y para devolverlo
        if not db_obj:
            raise NotFoundError(f"Product record with id {id} not found.")
        
        try:
            await db.delete(db_obj)
            await db.commit()
            return db_obj # Retorna el objeto eliminado
        except Exception as e:
            await db.rollback()
            raise CRUDException(f"Error deleting Product record: {str(e)}") from e

product = CRUDProduct(Product)
