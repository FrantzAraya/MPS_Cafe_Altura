from sqlmodel import Session, select
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta
import pandas as pd
from app.models.venta import Venta, VentaCreate, VentaUpdate
from app.utils.iso_weeks import fecha_a_semana_iso

def get_ventas(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    sku_id: Optional[int] = None,
    fecha_inicio: Optional[date] = None,
    fecha_fin: Optional[date] = None,
    semana_iso: Optional[int] = None,
    año_iso: Optional[int] = None
) -> List[Venta]:
    """
    Obtiene la lista de ventas con filtros opcionales.
    
    Args:
        db: Sesión de base de datos
        skip: Número de registros a omitir
        limit: Número máximo de registros a devolver
        sku_id: Filtrar por SKU
        fecha_inicio: Filtrar por fecha de inicio
        fecha_fin: Filtrar por fecha de fin
        semana_iso: Filtrar por semana ISO
        año_iso: Filtrar por año ISO
    
    Returns:
        Lista de ventas
    """
    query = select(Venta)
    
    # Aplicar filtros
    if sku_id is not None:
        query = query.where(Venta.sku_id == sku_id)
    
    if fecha_inicio is not None:
        query = query.where(Venta.fecha >= fecha_inicio)
    
    if fecha_fin is not None:
        query = query.where(Venta.fecha <= fecha_fin)
    
    if semana_iso is not None:
        query = query.where(Venta.semana_iso == semana_iso)
    
    if año_iso is not None:
        query = query.where(Venta.año_iso == año_iso)
    
    # Ordenar por fecha descendente
    query = query.order_by(Venta.fecha.desc())
    
    return db.exec(query.offset(skip).limit(limit)).all()

def get_venta(db: Session, venta_id: int) -> Optional[Venta]:
    """
    Obtiene una venta por su ID.
    
    Args:
        db: Sesión de base de datos
        venta_id: ID de la venta
    
    Returns:
        Venta o None si no existe
    """
    return db.get(Venta, venta_id)

def create_venta(db: Session, venta: VentaCreate) -> Venta:
    """
    Crea una nueva venta.
    
    Args:
        db: Sesión de base de datos
        venta: Datos de la venta a crear
    
    Returns:
        Venta creada
    """
    # Calcular semana ISO si no se proporciona
    if venta.semana_iso is None or venta.año_iso is None:
        año_iso, semana_iso = fecha_a_semana_iso(venta.fecha)
        venta_dict = venta.dict()
        venta_dict["semana_iso"] = semana_iso
        venta_dict["año_iso"] = año_iso
        db_venta = Venta(**venta_dict)
    else:
        db_venta = Venta.from_orm(venta)
    
    db.add(db_venta)
    db.commit()
    db.refresh(db_venta)
    return db_venta

def update_venta(db: Session, venta_id: int, venta: VentaUpdate) -> Optional[Venta]:
    """
    Actualiza una venta existente.
    
    Args:
        db: Sesión de base de datos
        venta_id: ID de la venta a actualizar
        venta: Datos actualizados de la venta
    
    Returns:
        Venta actualizada o None si no existe
    """
    db_venta = get_venta(db, venta_id)
    if not db_venta:
        return None
    
    # Actualizar campos
    venta_data = venta.dict(exclude_unset=True)
    
    # Si se actualiza la fecha, recalcular semana ISO
    if "fecha" in venta_data:
        año_iso, semana_iso = fecha_a_semana_iso(venta_data["fecha"])
        venta_data["semana_iso"] = semana_iso
        venta_data["año_iso"] = año_iso
    
    for key, value in venta_data.items():
        setattr(db_venta, key, value)
    
    # Actualizar timestamp
    db_venta.updated_at = datetime.now()
    
    db.add(db_venta)
    db.commit()
    db.refresh(db_venta)
    return db_venta

def delete_venta(db: Session, venta_id: int) -> bool:
    """
    Elimina una venta.
    
    Args:
        db: Sesión de base de datos
        venta_id: ID de la venta a eliminar
    
    Returns:
        True si se eliminó correctamente, False en caso contrario
    """
    db_venta = get_venta(db, venta_id)
    if not db_venta:
        return False
    
    db.delete(db_venta)
    db.commit()
    return True

def get_ventas_semanales(db: Session) -> List[Dict[str, Any]]:
    """
    Obtiene las ventas consolidadas por semana.
    
    Args:
        db: Sesión de base de datos
    
    Returns:
        Lista de ventas semanales
    """
    # Obtener todas las ventas
    ventas = db.exec(select(Venta)).all()
    
    if not ventas:
        return []
    
    # Convertir a DataFrame para facilitar la agrupación
    ventas_df = pd.DataFrame([{
        "id": v.id,
        "sku_id": v.sku_id,
        "fecha": v.fecha,
        "unidades": v.unidades,
        "semana_iso": v.semana_iso,
        "año_iso": v.año_iso
    } for v in ventas])
    
    # Agrupar por semana y SKU
    ventas_semanales = ventas_df.groupby(["año_iso", "semana_iso", "sku_id"]).agg({
        "unidades": "sum"
    }).reset_index()
    
    # Renombrar columnas
    ventas_semanales = ventas_semanales.rename(columns={"unidades": "unidades_total"})
    
    # Convertir a lista de diccionarios
    return ventas_semanales.to_dict(orient="records")
