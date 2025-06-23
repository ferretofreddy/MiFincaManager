        # app/crud/products.py
        from typing import Type, TypeVar, Any, Generic, Optional, List
        from sqlalchemy.ext.asyncio import AsyncSession
        from sqlalchemy.future import select
        from app.crud.base import CRUDBase
        from app.models.product import Product
        from app.schemas.product import ProductCreate, ProductUpdate

        class CRUDProduct(CRUDBase[Product, ProductCreate, ProductUpdate]):
            """
            CRUD class for operations on the Product model.
            """
            async def get_by_farm_id(self, db: AsyncSession, farm_id: int) -> List[Product]:
                """
                Gets all products associated with a specific farm.
                """
                result = await db.execute(select(self.model).filter(self.model.farm_id == farm_id))
                return result.scalars().all()

        product = CRUDProduct(Product)
        