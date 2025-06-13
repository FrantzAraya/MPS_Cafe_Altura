from sqlmodel import SQLModel, create_engine, Session
from app.core.config import settings
import os

# Crear motor de base de datos
engine = create_engine(
    settings.DATABASE_URL,
    echo=False,  # Establecer en True para ver las consultas SQL
    connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {},
)

def get_session():
    """
    Generador de sesiones de base de datos.
    """
    with Session(engine) as session:
        yield session

def create_db_and_tables():
    """
    Crea la base de datos y las tablas si no existen.
    """
    # Importar modelos para que SQLModel los registre
    from app.models.sku import SKU
    from app.models.venta import Venta
    from app.models.produccion import Produccion
    from app.models.parametro import Parametro
    
    # Crear tablas
    SQLModel.metadata.create_all(engine)
    
    # Inicializar parámetros por defecto
    with Session(engine) as session:
        from app.crud.parametros import inicializar_parametros
        inicializar_parametros(session)
