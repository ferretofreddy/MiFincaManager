        # app/schemas/product.py
        from typing import Optional, List
        from datetime import datetime
        from pydantic import BaseModel, Field, ConfigDict
        import uuid # Importa uuid para tipos de ID

        # Importa schemas reducidos de las relaciones (para la respuesta completa)
        from app.schemas.master_data import MasterDataReduced
        from app.schemas.farm import FarmReduced
        from app.schemas.user import UserReduced

        class ProductBase(BaseModel):
            """
            Esquema base para un producto, conteniendo los campos comunes.
            """
            name: str = Field(..., description="Name of the product or input")
            description: Optional[str] = Field(None, description="Detailed description of the product")
            current_stock: float = Field(0.0, description="Current quantity in inventory")
            minimum_stock_alert: float = Field(0.0, description="Minimum threshold for low stock alert")
            price_per_unit: float = Field(..., gt=0, description="Price per unit of the product")
            
            product_type_id: uuid.UUID = Field(..., description="ID of the product type (from MasterData)")
            unit_id: uuid.UUID = Field(..., description="ID of the unit of measure (from MasterData)")
            farm_id: uuid.UUID = Field(..., description="ID of the farm to which the product belongs")
            is_active: Optional[bool] = Field(True, description="Indicates if the product is active")

            model_config = ConfigDict(from_attributes=True)

        class ProductCreate(ProductBase):
            """
            Esquema para crear un nuevo producto.
            """
            pass # created_by_user_id se asignará desde el token de autenticación

        class ProductUpdate(ProductBase):
            """
            Esquema para actualizar un producto existente. Todos los campos son opcionales.
            """
            name: Optional[str] = Field(None, description="Name of the product or input")
            description: Optional[str] = Field(None, description="Detailed description of the product")
            current_stock: Optional[float] = Field(None, description="Current quantity in inventory") # Puede ser actualizado directamente para ajustar inventario
            minimum_stock_alert: Optional[float] = Field(None, description="Minimum threshold for low stock alert")
            price_per_unit: Optional[float] = Field(None, gt=0, description="Price per unit of the product")
            product_type_id: Optional[uuid.UUID] = Field(None, description="ID of the product type (from MasterData)")
            unit_id: Optional[uuid.UUID] = Field(None, description="ID of the unit of measure (from MasterData)")
            farm_id: Optional[uuid.UUID] = Field(None, description="ID of the farm to which the product belongs")
            is_active: Optional[bool] = Field(None, description="Indicates if the product is active")


        class ProductReduced(BaseModel):
            """
            Esquema reducido para el producto, útil en relaciones inversas.
            """
            id: uuid.UUID
            name: str
            current_stock: float
            farm_id: uuid.UUID
            model_config = ConfigDict(from_attributes=True)

        class Product(ProductBase):
            """
            Esquema completo para representar un producto, incluyendo IDs, marcas de tiempo
            y relaciones ORM cargadas.
            """
            id: uuid.UUID # Heredado de BaseModel, pero lo declaramos explícitamente para claridad
            created_by_user_id: uuid.UUID
            created_at: datetime
            updated_at: Optional[datetime] = None

            # Relaciones cargadas para la respuesta
            product_type: Optional[MasterDataReduced] = None
            unit: Optional[MasterDataReduced] = None
            farm: Optional[FarmReduced] = None
            created_by_user: Optional[UserReduced] = None

            model_config = ConfigDict(from_attributes=True)

        # Reconstruir los modelos para resolver ForwardRefs (si los hubiera)
        ProductReduced.model_rebuild()
        Product.model_rebuild()
        