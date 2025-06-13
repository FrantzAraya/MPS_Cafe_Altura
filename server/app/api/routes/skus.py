from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from typing import List, Optional

from app.db.session import get_session
from app.models.sku import SKU, SKUCreate, SKUUpdate, SKURead
from app.crud.skus import get_skus, get_sku, create_sku, update_sku, delete_sku

router = APIRouter()

@router.get("/skus", response_model=List[SKURead])
def read_skus(
    skip: int = 0,
    limit: int = 100,
    activo: Optional[bool] = None,
    db: Session = Depends(get_session)
):
    """
    Obtiene la lista de SKUs.
    """
    return get_skus(db, skip=skip, limit=limit, activo=activo)

@router.post("/skus", response_model=SKURead)
def create_sku_endpoint(sku: SKUCreate, db: Session = Depends(get_session)):
    """
    Crea un nuevo SKU.
    """
    return create_sku(db, sku)

@router.get("/skus/{sku_id}", response_model=SKURead)
def read_sku(sku_id: int, db: Session = Depends(get_session)):
    """
    Obtiene un SKU por su ID.
    """
    db_sku = get_sku(db, sku_id)
    if db_sku is None:
        raise HTTPException(status_code=404, detail="SKU no encontrado")
    return db_sku

@router.put("/skus/{sku_id}", response_model=SKURead)
def update_sku_endpoint(sku_id: int, sku: SKUUpdate, db: Session = Depends(get_session)):
    """
    Actualiza un SKU existente.
    """
    db_sku = update_sku(db, sku_id, sku)
    if db_sku is None:
        raise HTTPException(status_code=404, detail="SKU no encontrado")
    return db_sku

@router.delete("/skus/{sku_id}")
def delete_sku_endpoint(sku_id: int, db: Session = Depends(get_session)):
    """
    Elimina un SKU (baja lógica).
    """
    success = delete_sku(db, sku_id)
    if not success:
        raise HTTPException(status_code=404, detail="SKU no encontrado")
    return {"success": True, "message": "SKU eliminado correctamente"}
