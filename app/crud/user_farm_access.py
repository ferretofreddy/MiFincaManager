# app/crud/user_farm_access.py
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from app.crud.base import CRUDBase
from app.models.user_farm_access import UserFarmAccess # Importa el modelo ORM
from app.schemas.user_farm_access import UserFarmAccessCreate, UserFarmAccessUpdate # Importa los esquemas Pydantic

class CRUDUserFarmAccess(CRUDBase[UserFarmAccess, UserFarmAccessCreate, UserFarmAccessUpdate]):
    """
    Clase que implementa las operaciones CRUD para el modelo UserFarmAccess.
    Hereda de CRUDBase para obtener funcionalidades básicas.
    """
    # Puedes añadir métodos específicos aquí si las operaciones para UserFarmAccess
    # requieren lógica adicional más allá de lo que proporciona CRUDBase.

    def get_by_user_and_farm(
        self, db: Session, *, user_id: uuid.UUID, farm_id: uuid.UUID
    ) -> Optional[UserFarmAccess]:
        """
        Obtiene un registro de UserFarmAccess por user_id y farm_id.
        """
        return db.query(self.model).filter(
            self.model.user_id == user_id,
            self.model.farm_id == farm_id
        ).first()

    def get_user_farm_accesses(
        self, db: Session, *, user_id: uuid.UUID
    ) -> List[UserFarmAccess]:
        """
        Obtiene todos los registros de acceso de una granja para un usuario específico.
        """
        return db.query(self.model).filter(self.model.user_id == user_id).all()

    def get_farm_user_accesses(
        self, db: Session, *, farm_id: uuid.UUID
    ) -> List[UserFarmAccess]:
        """
        Obtiene todos los registros de acceso de los usuarios a una granja específica.
        """
        return db.query(self.model).filter(self.model.farm_id == farm_id).all()


user_farm_access = CRUDUserFarmAccess(UserFarmAccess)
