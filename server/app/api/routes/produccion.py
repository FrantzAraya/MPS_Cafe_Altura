from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from typing import List, Optional

from app.db.session import get_session
from app.models.produccion import Produccion, ProduccionCreate, ProduccionUpdate, ProduccionRead
from app.crud.produccion import get_producciones, get_produccion, create_produccion, update_produccion, delete_produccion

router = APIRouter()

@router.get("/produccion", response_model=List[ProduccionRead])
def read_producciones(
    skip: int = 0,
    limit: int = 100,
    sku_id: Optional[int] = None,
    semana_iso: Optional[int] = None,
    año_iso: Optional[int] = None,
    db: Session = Depends(get_session)
):
    """
    Obtiene la lista de producciones con filtros opcionales.
    """
    return get_producciones(
        db,
        skip=skip,
        limit=limit,
        sku_id=sku_id,
        semana_iso=semana_iso,
        año_iso=año_iso
    )

@router.post("/produccion", response_model=ProduccionRead)
def create_produccion_endpoint(produccion: ProduccionCreate, db: Session = Depends(get_session)):
    """
    Crea un nuevo registro de producción.
    """
    return create_produccion(db, produccion)

@router.get("/produccion/{produccion_id}", response_model=ProduccionRead)
def read_produccion(produccion_id: int, db: Session = Depends(get_session)):
    """
    Obtiene una producción por su ID.
    """
    db_produccion = get_produccion(db, produccion_id)
    if db_produccion is None:
        raise HTTPException(status_code=404, detail="Registro de producción no encontrado")
    return db_produccion

@router.put("/produccion/{produccion_id}", response_model=ProduccionRead)
def update_produccion_endpoint(produccion_id: int, produccion: ProduccionUpdate, db: Session = Depends(get_session)):
    """
    Actualiza un registro de producción existente.
    """
    db_produccion = update_produccion(db, produccion_id, produccion)
    if db_produccion is None:
        raise HTTPException(status_code=404, detail="Registro de producción no encontrado")
    return db_produccion

@router.delete("/produccion/{produccion_id}")
def delete_produccion_endpoint(produccion_id: int, db: Session = Depends(get_session)):
    """
    Elimina un registro de producción.
    """
    success = delete_produccion(db, produccion_id)
    if not success:
        raise HTTPException(status_code=404, detail="Registro de producción no encontrado")
    return {"success": True, "message": "Registro de producción eliminado correctamente"}
