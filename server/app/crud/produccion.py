from sqlmodel import Session, select
from typing import List, Optional, Dict, Any
from datetime import datetime
import pandas as pd
from app.models.produccion import Produccion, ProduccionCreate, ProduccionUpdate
from app.models.sku import SKU

def get_producciones(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    sku_id: Optional[int] = None,
    semana_iso: Optional[int] = None,
    año_iso: Optional[int] = None
) -> List[Produccion]:
    """
    Obtiene la lista de producciones con filtros opcionales.
    
    Args:
        db: Sesión de base de datos
        skip: Número de registros a omitir
        limit: Número máximo de registros a devolver
        sku_id: Filtrar por SKU
        semana_iso: Filtrar por semana ISO
        año_iso: Filtrar por año ISO
    
    Returns:
        Lista de producciones
    """
    query = select(Produccion)
    
    # Aplicar filtros
    if sku_id is not None:
        query = query.where(Produccion.sku_id == sku_id)
    
    if semana_iso is not None:
        query = query.where(Produccion.semana_iso == semana_iso)
    
    if año_iso is not None:
        query = query.where(Produccion.año_iso == año_iso)
    
    # Ordenar por año y semana descendente
    query = query.order_by(Produccion.año_iso.desc(), Produccion.semana_iso.desc())
    
    return db.exec(query.offset(skip).limit(limit)).all()

def get_produccion(db: Session, produccion_id: int) -> Optional[Produccion]:
    """
    Obtiene una producción por su ID.
    
    Args:
        db: Sesión de base de datos
        produccion_id: ID de la producción
    
    Returns:
        Producción o None si no existe
    """
    return db.get(Produccion, produccion_id)

def create_produccion(db: Session, produccion: ProduccionCreate) -> Produccion:
    """
    Crea un nuevo registro de producción.
    
    Args:
        db: Sesión de base de datos
        produccion: Datos de la producción a crear
    
    Returns:
        Producción creada
    """
    # Calcular scrap si no se proporciona
    if produccion.scrap is None:
        # Obtener presentación del SKU
        sku = db.get(SKU, produccion.sku_id)
        if sku:
            # Convertir kg a g
            g_verde = produccion.kg_verde * 1000
            # Calcular gramos teóricos en producto terminado
            g_producto = produccion.unidades_producidas * sku.presentacion_g
            # Calcular scrap
            if g_verde > 0:
                scrap = 1 - (g_producto / g_verde)
                # Limitar entre 0 y 1
                scrap = max(0, min(1, scrap))
            else:
                scrap = 0
            
            produccion_dict = produccion.dict()
            produccion_dict["scrap"] = scrap
            db_produccion = Produccion(**produccion_dict)
        else:
            db_produccion = Produccion.from_orm(produccion)
    else:
        db_produccion = Produccion.from_orm(produccion)
    
    db.add(db_produccion)
    db.commit()
    db.refresh(db_produccion)
    return db_produccion

def update_produccion(db: Session, produccion_id: int, produccion: ProduccionUpdate) -> Optional[Produccion]:
    """
    Actualiza un registro de producción existente.
    
    Args:
        db: Sesión de base de datos
        produccion_id: ID de la producción a actualizar
        produccion: Datos actualizados de la producción
    
    Returns:
        Producción actualizada o None si no existe
    """
    db_produccion = get_produccion(db, produccion_id)
    if not db_produccion:
        return None
    
    # Actualizar campos
    produccion_data = produccion.dict(exclude_unset=True)
    
    # Recalcular scrap si se actualizan kg_verde o unidades_producidas
    if "kg_verde" in produccion_data or "unidades_producidas" in produccion_data:
        # Obtener valores actualizados
        kg_verde = produccion_data.get("kg_verde", db_produccion.kg_verde)
        unidades_producidas = produccion_data.get("unidades_producidas", db_produccion.unidades_producidas)
        
        # Obtener presentación del SKU
        sku = db.get(SKU, db_produccion.sku_id)
        if sku:
            # Convertir kg a g
            g_verde = kg_verde * 1000
            # Calcular gramos teóricos en producto terminado
            g_producto = unidades_producidas * sku.presentacion_g
            # Calcular scrap
            if g_verde > 0:
                scrap = 1 - (g_producto / g_verde)
                # Limitar entre 0 y 1
                scrap = max(0, min(1, scrap))
            else:
                scrap = 0
            
            produccion_data["scrap"] = scrap
    
    for key, value in produccion_data.items():
        setattr(db_produccion, key, value)
    
    # Actualizar timestamp
    db_produccion.updated_at = datetime.now()
    
    db.add(db_produccion)
    db.commit()
    db.refresh(db_produccion)
    return db_produccion

def delete_produccion(db: Session, produccion_id: int) -> bool:
    """
    Elimina un registro de producción.
    
    Args:
        db: Sesión de base de datos
        produccion_id: ID de la producción a eliminar
    
    Returns:
        True si se eliminó correctamente, False en caso contrario
    """
    db_produccion = get_produccion(db, produccion_id)
    if not db_produccion:
        return False
    
    db.delete(db_produccion)
    db.commit()
    return True

def get_scrap_promedio(
    db: Session,
    sku_id: Optional[int] = None,
    ultimas_semanas: Optional[int] = None
) -> float:
    """
    Calcula el scrap promedio para un SKU.
    
    Args:
        db: Sesión de base de datos
        sku_id: ID del SKU (opcional)
        ultimas_semanas: Número de semanas a considerar (opcional)
    
    Returns:
        Scrap promedio
    """
    query = select(Produccion)
    
    if sku_id is not None:
        query = query.where(Produccion.sku_id == sku_id)
    
    producciones = db.exec(query).all()
    
    if not producciones:
        return 0.05  # Valor por defecto si no hay datos
    
    # Convertir a DataFrame para facilitar el análisis
    prod_df = pd.DataFrame([{
        "id": p.id,
        "sku_id": p.sku_id,
        "semana_iso": p.semana_iso,
        "año_iso": p.año_iso,
        "scrap": p.scrap
    } for p in producciones])
    
    # Crear columna de fecha para ordenar
    prod_df["fecha"] = pd.to_datetime(prod_df["año_iso"].astype(str) + "-" + prod_df["semana_iso"].astype(str) + "-1", format="%Y-%W-%w")
    
    # Ordenar por fecha descendente
    prod_df = prod_df.sort_values("fecha", ascending=False)
    
    # Filtrar por últimas semanas si se especifica
    if ultimas_semanas is not None:
        prod_df = prod_df.head(ultimas_semanas)
    
    # Calcular promedio
    scrap_promedio = prod_df["scrap"].mean()
    
    return scrap_promedio if not pd.isna(scrap_promedio) else 0.05
