# app/schemas/user_farm_access.py
import uuid
from datetime import datetime
from typing import Optional, List, ForwardRef
from pydantic import BaseModel, Field, ConfigDict

# Definiciones de ForwardRef para evitar importaciones circulares con User y Farm
UserReduced = ForwardRef("UserReduced")
FarmReduced = ForwardRef("FarmReduced")

class UserFarmAccessBase(BaseModel):
    """
    Clase base para los esquemas de UserFarmAccess.
    Contiene los campos comunes para la creación y actualización.
    """
    user_id: uuid.UUID = Field(..., description="ID del usuario al que se le otorga acceso.")
    farm_id: uuid.UUID = Field(..., description="ID de la granja a la que se le da acceso.")
    access_level_id: uuid.UUID = Field(..., description="ID del nivel de acceso (desde MasterData).")
    is_active: Optional[bool] = Field(True, description="Indica si el acceso está activo.")
    assigned_by_user_id: uuid.UUID = Field(..., description="ID del usuario que asignó el acceso.")
    notes: Optional[str] = Field(None, description="Notas adicionales sobre el acceso.")

    model_config = ConfigDict(from_attributes=True) # Permite la asignación desde atributos ORM

class UserFarmAccessCreate(UserFarmAccessBase):
    """
    Esquema para la creación de un nuevo registro de acceso de usuario a granja.
    Hereda de UserFarmAccessBase.
    """
    pass

class UserFarmAccessUpdate(UserFarmAccessBase):
    """
    Esquema para la actualización de un registro existente de acceso de usuario a granja.
    Todos los campos son opcionales para permitir actualizaciones parciales.
    """
    user_id: Optional[uuid.UUID] = None
    farm_id: Optional[uuid.UUID] = None
    access_level_id: Optional[uuid.UUID] = None
    is_active: Optional[bool] = None
    assigned_by_user_id: Optional[uuid.UUID] = None
    notes: Optional[str] = None

class UserFarmAccessReduced(BaseModel):
    """
    Esquema para representar una versión reducida de UserFarmAccess,
    útil para relaciones anidadas donde no se necesitan todos los detalles.
    """
    id: uuid.UUID
    user_id: uuid.UUID
    farm_id: uuid.UUID
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

class UserFarmAccess(UserFarmAccessBase):
    """
    Esquema completo para la lectura de un registro de acceso de usuario a granja,
    incluyendo campos generados por la base de datos y relaciones.
    """
    id: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Relaciones Pydantic para incluir datos relacionados
    user: "UserReduced"
    farm: "FarmReduced"
    assigned_by_user: "UserReduced"
    # No incluimos MasterData aquí directamente para evitar circularidad profunda
    # access_level: MasterDataReduced # Si se necesita, importarla o ForwardRef

    model_config = ConfigDict(from_attributes=True)

