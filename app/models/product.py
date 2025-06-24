        # app/models/product.py
        import uuid
        from datetime import datetime
        from sqlalchemy import Column, String, Float, Boolean, ForeignKey, DateTime
        from sqlalchemy.dialects.postgresql import UUID # Para usar UUID en claves primarias y foráneas
        from sqlalchemy.orm import relationship, Mapped
        from typing import Optional

        # Importa BaseModel de nuestro módulo app/db/base.py
        from app.db.base import BaseModel

        # Importa los modelos relacionados directamente (para tipo de Mapped)
        from .user import User
        from .master_data import MasterData
        from .farm import Farm

        class Product(BaseModel): # Hereda de BaseModel para id, created_at, updated_at (UUIDs)
            """
            Modelo de SQLAlchemy para la gestión de productos e inventario.
            Representa insumos, productos de la finca, etc.
            """
            __tablename__ = "products"

            # id, created_at, updated_at son heredados de BaseModel con UUID.

            name = Column(String, index=True, nullable=False)
            description = Column(String, nullable=True)
            current_stock = Column(Float, default=0.0, nullable=False) # Cantidad actual en inventario
            minimum_stock_alert = Column(Float, default=0.0, nullable=False) # Umbral para alerta de bajo stock
            price_per_unit = Column(Float, nullable=False) # Precio de adquisición o venta por unidad

            # Claves foráneas a MasterData para tipología y unidad de medida
            product_type_id = Column(UUID(as_uuid=True), ForeignKey("master_data.id"), nullable=False)
            unit_id = Column(UUID(as_uuid=True), ForeignKey("master_data.id"), nullable=False)

            # Relación con Farm (una finca puede tener muchos productos)
            farm_id = Column(UUID(as_uuid=True), ForeignKey("farms.id"), nullable=False)

            # Auditoría
            is_active = Column(Boolean, default=True, nullable=False)
            created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

            # Relaciones ORM
            product_type: Mapped["MasterData"] = relationship("MasterData", foreign_keys=[product_type_id], back_populates="products_as_type")
            unit: Mapped["MasterData"] = relationship("MasterData", foreign_keys=[unit_id], back_populates="products_as_unit")
            farm: Mapped["Farm"] = relationship("Farm", back_populates="products")
            created_by_user: Mapped["User"] = relationship("User", back_populates="products_created") # Ajustaremos esto en el modelo User
        