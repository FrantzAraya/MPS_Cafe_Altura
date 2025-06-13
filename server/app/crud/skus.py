from sqlmodel import Session, select
from typing import List, Optional
from app.models.sku import SKU, SKUCreate, SKUUpdate

def get_skus(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    activo: Optional[bool] = None
) -> List[SKU]:
    """
    Obtiene la lista de SKUs.
    
    Args:
        db: Sesión de base de datos
        skip: Número de registros a omitir
        limit: Número máximo de registros a devolver
        activo: Filtrar por estado activo
    
    Returns:
        Lista de SKUs
    """
    query = select(SKU)
    
    if activo is not None:
        query = query.where(SKU.activo == activo)
    
    return db.exec(query.offset(skip).limit(limit)).all()

def get_sku(db: Session, sku_id: int) -> Optional[SKU]:
    """
    Obtiene un SKU por su ID.
    
    Args:
        db: Sesión de base de datos
        sku_id: ID del SKU
    
    Returns:
        SKU o None si no existe
    """
    return db.get(SKU, sku_id)

def create_sku(db: Session, sku: SKUCreate) -> SKU:
    """
    Crea un nuevo SKU.
    
    Args:
        db: Sesión de base de datos
        sku: Datos del SKU a crear
    
    Returns:
        SKU creado
    """
    db_sku = SKU.from_orm(sku)
    db.add(db_sku)
    db.commit()
    db.refresh(db_sku)
    return db_sku

def update_sku(db: Session, sku_id: int, sku: SKUUpdate) -> Optional[SKU]:
    """
    Actualiza un SKU existente.
    
    Args:
        db: Sesión de base de datos
        sku_id: ID del SKU a actualizar
        sku: Datos actualizados del SKU
    
    Returns:
        SKU actualizado o None si no existe
    """
    db_sku = get_sku(db, sku_id)
    if not db_sku:
        return None
    
    # Actualizar campos
    sku_data = sku.dict(exclude_unset=True)
    for key, value in sku_data.items():
        setattr(db_sku, key, value)
    
    # Actualizar timestamp
    from datetime import datetime
    db_sku.updated_at = datetime.now()
    
    db.add(db_sku)
    db.commit()
    db.refresh(db_sku)
    return db_sku

def delete_sku(db: Session, sku_id: int) -> bool:
    """
    Elimina un SKU (baja lógica).
    
    Args:
        db: Sesión de base de datos
        sku_id: ID del SKU a eliminar
    
    Returns:
        True si se eliminó correctamente, False en caso contrario
    """
    db_sku = get_sku(db, sku_id)
    if not db_sku:
        return False
    
    # Baja lógica
    db_sku.activo = False
    
    # Actualizar timestamp
    from datetime import datetime
    db_sku.updated_at = datetime.now()
    
    db.add(db_sku)
    db.commit()
    return True
