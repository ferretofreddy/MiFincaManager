# MiFincaManager/app/__init__.py

# Estas líneas hacen que los módulos crud, schemas, models y api sean accesibles
# directamente bajo el paquete 'app'.
from . import crud
from . import schemas
from . import models
from . import api
from . import enums # También re-exportar enums para un acceso fácil si se desea
