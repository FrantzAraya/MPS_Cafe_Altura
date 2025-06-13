from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import date, datetime
from app.models.sku import SKU

class VentaBase(SQLModel):
    """
    Modelo base para Venta.
    """
    sku_id: int = Field(foreign_key="sku.id")
    fecha: date = Field()
    unidades: int = Field(gt=0)
    semana_iso: Optional[int] = Field(default=None)
    año_iso: Optional[int] = Field(default=None)

class Venta(VentaBase, table=True):
    """
    Modelo de Venta para la base de datos.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # Relación con SKU
    sku: Optional[SKU] = Relationship()

class VentaCreate(VentaBase):
    """
    Modelo para crear una Venta.
    """
    pass

class VentaUpdate(SQLModel):
    """
    Modelo para actualizar una Venta.
    """
    fecha: Optional[date] = None
    unidades: Optional[int] = None

class VentaRead(VentaBase):
    """
    Modelo para leer una Venta.
    """
    id: int
    created_at: datetime
    updated_at: datetime
