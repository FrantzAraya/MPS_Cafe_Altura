from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime
from app.models.sku import SKU

class ProduccionBase(SQLModel):
    """
    Modelo base para Producción.
    """
    sku_id: int = Field(foreign_key="sku.id")
    semana_iso: int = Field()
    año_iso: int = Field()
    kg_verde: float = Field(gt=0)
    unidades_producidas: int = Field(gt=0)
    scrap: Optional[float] = Field(default=None)

class Produccion(ProduccionBase, table=True):
    """
    Modelo de Producción para la base de datos.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # Relación con SKU
    sku: Optional[SKU] = Relationship()

class ProduccionCreate(ProduccionBase):
    """
    Modelo para crear un registro de Producción.
    """
    pass

class ProduccionUpdate(SQLModel):
    """
    Modelo para actualizar un registro de Producción.
    """
    semana_iso: Optional[int] = None
    año_iso: Optional[int] = None
    kg_verde: Optional[float] = None
    unidades_producidas: Optional[int] = None
    scrap: Optional[float] = None

class ProduccionRead(ProduccionBase):
    """
    Modelo para leer un registro de Producción.
    """
    id: int
    created_at: datetime
    updated_at: datetime
