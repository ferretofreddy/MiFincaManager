        # app/crud/products.py
        from typing import Optional, List
        import uuid # Importa uuid
        from datetime import datetime

        from sqlalchemy.ext.asyncio import AsyncSession
        from sqlalchemy.future import select
        from sqlalchemy.orm import selectinload
        from sqlalchemy import and_

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

            async def _validate_foreign_keys(self, db: AsyncSession, obj_in: ProductCreate | ProductUpdate):
                """
                Valida que los IDs foráneos de MasterData y Farm existan.
                """
                # Validar product_type_id
                if obj_in.product_type_id:
                    md_type = await db.execute(select(MasterData).filter(MasterData.id == obj_in.product_type_id))
                    if not md_type.scalar_one_or_none():
                        raise NotFoundError(f"MasterData with ID {obj_in.product_type_id} (product_type_id) not found.")
                    if md_type.scalar_one().category != "product_type":
                        raise CRUDException(f"MasterData with ID {obj_in.product_type_id} is not of category 'product_type'.")
                
                # Validar unit_id
                if obj_in.unit_id:
                    md_unit = await db.execute(select(MasterData).filter(MasterData.id == obj_in.unit_id))
                    if not md_unit.scalar_one_or_none():
                        raise NotFoundError(f"MasterData with ID {obj_in.unit_id} (unit_id) not found.")
                    if md_unit.scalar_one().category != "unit_of_measure": # Asumiendo esta categoría para unidades
                        raise CRUDException(f"MasterData with ID {obj_in.unit_id} is not of category 'unit_of_measure'.")
                
                # Validar farm_id
                if obj_in.farm_id:
                    farm = await db.execute(select(Farm).filter(Farm.id == obj_in.farm_id))
                    if not farm.scalar_one_or_none():
                        raise NotFoundError(f"Farm with ID {obj_in.farm_id} not found.")

            async def create(self, db: AsyncSession, *, obj_in: ProductCreate, created_by_user_id: uuid.UUID) -> Product:
                """
                Crea un nuevo registro de producto.
                """
                try:
                    # Validar todas las claves foráneas
                    await self._validate_foreign_keys(db, obj_in)

                    # Opcional: Verificar unicidad del nombre del producto por finca (o globalmente)
                    existing_product = await db.execute(
                        select(Product).filter(and_(
                            Product.name == obj_in.name,
                            Product.farm_id == obj_in.farm_id # Unicidad por finca
                        ))
                    )
                    if existing_product.scalar_one_or_none():
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
                except Exception as e:
                    await db.rollback()
                    if isinstance(e, (NotFoundError, AlreadyExistsError, CRUDException)): # Relanzar errores que ya controlamos
                        raise e
                    raise CRUDException(f"Error creating Product record: {str(e)}") from e

            async def get(self, db: AsyncSession, product_id: uuid.UUID) -> Optional[Product]:
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
                    .filter(self.model.id == product_id)
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

            async def update(self, db: AsyncSession, *, db_obj: Product, obj_in: ProductUpdate) -> Product:
                """
                Actualiza un registro de producto existente.
                """
                try:
                    # Validar claves foráneas si se proporcionan en la actualización
                    await self._validate_foreign_keys(db, obj_in)

                    # Si se intenta cambiar el nombre y la finca, verificar unicidad
                    if obj_in.name is not None and obj_in.name != db_obj.name:
                        farm_id_to_check = obj_in.farm_id if obj_in.farm_id is not None else db_obj.farm_id
                        existing_product = await db.execute(
                            select(Product).filter(and_(
                                Product.name == obj_in.name,
                                Product.farm_id == farm_id_to_check,
                                Product.id != db_obj.id # Excluir el propio objeto
                            ))
                        )
                        if existing_product.scalar_one_or_none():
                            raise AlreadyExistsError(f"Product with name '{obj_in.name}' already exists in farm {farm_id_to_check}.")


                    updated_product = await super().update(db, db_obj=db_obj, obj_in=obj_in)
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
                        return result.scalar_one_or_none()
                    return updated_product
                except Exception as e:
                    await db.rollback()
                    if isinstance(e, (NotFoundError, AlreadyExistsError, CRUDException)):
                        raise e
                    raise CRUDException(f"Error updating Product record: {str(e)}") from e

            async def delete(self, db: AsyncSession, *, id: uuid.UUID) -> Product:
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
        