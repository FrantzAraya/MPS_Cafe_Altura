from sqlmodel import Session, select
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.models.parametro import Parametro, ParametroUpdate
from app.core.config import settings

def get_parametros(db: Session) -> List[Parametro]:
    """
    Obtiene todos los parámetros.
    
    Args:
        db: Sesión de base de datos
    
    Returns:
        Lista de parámetros
    """
    return db.exec(select(Parametro)).all()

def get_parametro(db: Session, nombre: str) -> Optional[Parametro]:
    """
    Obtiene un parámetro por su nombre.
    
    Args:
        db: Sesión de base de datos
        nombre: Nombre del parámetro
    
    Returns:
        Parámetro o None si no existe
    """
    return db.get(Parametro, nombre)

def update_parametro(db: Session, nombre: str, parametro: ParametroUpdate) -> Optional[Parametro]:
    """
    Actualiza un parámetro existente.
    
    Args:
        db: Sesión de base de datos
        nombre: Nombre del parámetro a actualizar
        parametro: Datos actualizados del parámetro
    
    Returns:
        Parámetro actualizado o None si no existe
    """
    db_parametro = get_parametro(db, nombre)
    if not db_parametro:
        return None
    
    # Actualizar valor
    db_parametro.valor = parametro.valor
    
    # Actualizar timestamp
    db_parametro.updated_at = datetime.now()
    
    db.add(db_parametro)
    db.commit()
    db.refresh(db_parametro)
    return db_parametro

def inicializar_parametros(db: Session) -> None:
    """
    Inicializa los parámetros por defecto si no existen.
    
    Args:
        db: Sesión de base de datos
    """
    # Definir parámetros por defecto
    parametros_default = [
        {
            "nombre": "nivel_servicio",
            "valor": str(settings.NIVEL_SERVICIO),
            "descripcion": "Nivel de servicio para cálculo de stock de seguridad (0-1)"
        },
        {
            "nombre": "capacidad_semanal",
            "valor": str(settings.CAPACIDAD_SEMANAL),
            "descripcion": "Capacidad de producción semanal en kg de café verde"
        },
        {
            "nombre": "dias_inventario_objetivo",
            "valor": str(settings.DIAS_INVENTARIO_OBJETIVO),
            "descripcion": "Objetivo de días de inventario para KPI"
        },
        {
            "nombre": "objetivo_cumplimiento_plan",
            "valor": str(settings.OBJETIVO_CUMPLIMIENTO_PLAN),
            "descripcion": "Objetivo de cumplimiento del plan para KPI (0-1)"
        },
        {
            "nombre": "objetivo_otd",
            "valor": str(settings.OBJETIVO_OTD),
            "descripcion": "Objetivo de On-Time Delivery para KPI (0-1)"
        },
        {
            "nombre": "objetivo_rechazos",
            "valor": str(settings.OBJETIVO_RECHAZOS),
            "descripcion": "Objetivo de tasa de rechazos para KPI (0-1)"
        }
    ]
    
    # Verificar y crear parámetros
    for param in parametros_default:
        db_param = get_parametro(db, param["nombre"])
        if not db_param:
            db_param = Parametro(**param)
            db.add(db_param)
    
    db.commit()
