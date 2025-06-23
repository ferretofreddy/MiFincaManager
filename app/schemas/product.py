        # app/schemas/product.py
        from typing import Optional, List
        from datetime import datetime
        from pydantic import BaseModel, Field

        class ProductBase(BaseModel):
            """
            Base schema for a product, containing common fields.
            """
            name: str = Field(..., description="Name of the product or input")
            description: Optional[str] = Field(None, description="Detailed description of the product")
            current_stock: float = Field(0.0, description="Current quantity in inventory")
            minimum_stock_alert: float = Field(0.0, description="Minimum threshold for low stock alert")
            price_per_unit: float = Field(..., gt=0, description="Price per unit of the product")
            product_type_id: int = Field(..., description="ID of the product type (from MasterData)")
            unit_id: int = Field(..., description="ID of the unit of measure (from MasterData)")
            farm_id: int = Field(..., description="ID of the farm to which the product belongs")
            is_active: Optional[bool] = Field(True, description="Indicates if the product is active")

        class ProductCreate(ProductBase):
            """
            Schema for creating a new product.
            """
            # created_by_user_id will be assigned from the authentication token
            pass

        class ProductUpdate(ProductBase):
            """
            Schema for updating an existing product. All fields are optional.
            """
            name: Optional[str] = Field(None, description="Name of the product or input")
            price_per_unit: Optional[float] = Field(None, gt=0, description="Price per unit of the product")
            product_type_id: Optional[int] = Field(None, description="ID of the product type (from MasterData)")
            unit_id: Optional[int] = Field(None, description="ID of the unit of measure (from MasterData)")
            farm_id: Optional[int] = Field(None, description="ID of the farm to which the product belongs")

        class ProductInDB(ProductBase):
            """
            Schema to represent a product as stored in the database,
            including IDs and timestamps.
            """
            id: int
            created_by_user_id: int
            created_at: datetime
            updated_at: Optional[datetime] = None

            class Config:
                orm_mode = True # Enables ORM compatibility (SQLAlchemy)
        