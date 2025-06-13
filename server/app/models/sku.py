from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class SKUBase(SQLModel):
    """
    Modelo base para SKU.
    """
    nombre: str = Field(index=True)
    presentacion_g: int = Field(description="Presentación en gramos")
    activo: bool = Field(default=True)

class SKU(SKUBase, table=True):
    """
    Modelo de SKU para la base de datos.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class SKUCreate(SKUBase):
    """
    Modelo para crear un SKU.
    """
    pass

class SKUUpdate(SQLModel):
    """
    Modelo para actualizar un SKU.
    """
    nombre: Optional[str] = None
    presentacion_g: Optional[int] = None
    activo: Optional[bool] = None

class SKURead(SKUBase):
    """
    Modelo para leer un SKU.
    """
    id: int
    created_at: datetime
    updated_at: datetime
