from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class ParametroBase(SQLModel):
    """
    Modelo base para Parámetro.
    """
    nombre: str = Field(primary_key=True)
    valor: str = Field()
    descripcion: Optional[str] = Field(default=None)

class Parametro(ParametroBase, table=True):
    """
    Modelo de Parámetro para la base de datos.
    """
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class ParametroUpdate(SQLModel):
    """
    Modelo para actualizar un Parámetro.
    """
    valor: str

class ParametroRead(ParametroBase):
    """
    Modelo para leer un Parámetro.
    """
    created_at: datetime
    updated_at: datetime
