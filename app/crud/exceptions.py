# app/crud/exceptions.py 
# Define excepciones personalizadas para operaciones CRUD.

class CRUDException(Exception):
    """Excepción base para operaciones CRUD."""
    pass

class NotFoundError(CRUDException):
    """Se lanza cuando un recurso solicitado no se encuentra."""
    pass

class AlreadyExistsError(CRUDException):
    """Se lanza cuando se intenta crear un recurso que ya existe."""
    pass

class IntegrityError(CRUDException):
    """Se lanza cuando ocurre un error de integridad de la base de datos (ej. violación de FK o UNIQUE)."""
    pass

class NotAuthorizedError(CRUDException):
    """Se lanza cuando el usuario no tiene autorización para realizar una operación."""
    pass
