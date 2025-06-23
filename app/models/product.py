        # app/models/product.py
        from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime
        from sqlalchemy.orm import relationship
        from sqlalchemy.sql import func
        from app.db.base import Base

        class Product(Base):
            """
            Modelo de SQLAlchemy for inventory and product management.
            Represents supplies, farm products, etc.
            """
            __tablename__ = "products"

            id = Column(Integer, primary_key=True, index=True)
            name = Column(String, index=True, nullable=False)
            description = Column(String, nullable=True)
            current_stock = Column(Float, default=0.0) # Current quantity in inventory
            minimum_stock_alert = Column(Float, default=0.0) # Threshold for low stock alert
            price_per_unit = Column(Float, nullable=False) # Acquisition or sale price per unit

            # Foreign keys to MasterData for typology and unit of measure
            product_type_id = Column(Integer, ForeignKey("master_data.id"), nullable=False)
            unit_id = Column(Integer, ForeignKey("master_data.id"), nullable=False)

            # Relationships
            # A product has a MasterData type (e.g., "Medication", "Food")
            product_type = relationship("MasterData", foreign_keys=[product_type_id], backref="products_as_type")
            # A product has a MasterData unit of measure (e.g., "Liter", "Kg")
            unit = relationship("MasterData", foreign_keys=[unit_id], backref="products_as_unit")

            # Relationship with Farm (a farm can have many products)
            farm_id = Column(Integer, ForeignKey("farms.id"), nullable=False)
            farm = relationship("Farm", back_populates="products")

            # Audit
            is_active = Column(Boolean, default=True)
            created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
            created_by_user = relationship("User", foreign_populates="products") # Adjust in the User model
            created_at = Column(DateTime(timezone=True), server_default=func.now())
            updated_at = Column(DateTime(timezone=True), onupdate=func.now())
        