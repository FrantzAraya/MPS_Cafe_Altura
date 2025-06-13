from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from typing import List, Optional
from datetime import date

from app.db.session import get_session
from app.models.venta import Venta, VentaCreate, VentaUpdate, VentaRead
from app.crud.ventas import get_ventas, get_venta, create_venta, update_venta, delete_venta, get_ventas_semanales

router = APIRouter()

@router.get("/ventas", response_model=List[VentaRead])
def read_ventas(
    skip: int = 0,
    limit: int = 100,
    sku_id: Optional[int] = None,
    fecha_inicio: Optional[date] = None,
    fecha_fin: Optional[date] = None,
    semana_iso: Optional[int] = None,
    año_iso: Optional[int] = None,
    db: Session = Depends(get_session)
):
    """
    Obtiene la lista de ventas con filtros opcionales.
    """
    return get_ventas(
        db,
        skip=skip,
        limit=limit,
        sku_id=sku_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        semana_iso=semana_iso,
        año_iso=año_iso
    )

@router.post("/ventas", response_model=VentaRead)
def create_venta_endpoint(venta: VentaCreate, db: Session = Depends(get_session)):
    """
    Crea una nueva venta.
    """
    return create_venta(db, venta)

@router.get("/ventas/{venta_id}", response_model=VentaRead)
def read_venta(venta_id: int, db: Session = Depends(get_session)):
    """
    Obtiene una venta por su ID.
    """
    db_venta = get_venta(db, venta_id)
    if db_venta is None:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    return db_venta

@router.put("/ventas/{venta_id}", response_model=VentaRead)
def update_venta_endpoint(venta_id: int, venta: VentaUpdate, db: Session = Depends(get_session)):
    """
    Actualiza una venta existente.
    """
    db_venta = update_venta(db, venta_id, venta)
    if db_venta is None:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    return db_venta

@router.delete("/ventas/{venta_id}")
def delete_venta_endpoint(venta_id: int, db: Session = Depends(get_session)):
    """
    Elimina una venta.
    """
    success = delete_venta(db, venta_id)
    if not success:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    return {"success": True, "message": "Venta eliminada correctamente"}

@router.get("/ventas/semanal")
def read_ventas_semanales(db: Session = Depends(get_session)):
    """
    Obtiene las ventas consolidadas por semana.
    """
    return get_ventas_semanales(db)
