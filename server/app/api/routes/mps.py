from fastapi import APIRouter, Depends, HTTPException, Body
from sqlmodel import Session
from typing import Dict, Any, List

from app.db.session import get_session
from app.services.mps import generar_mps, guardar_ajustes_mps
from app.crud.parametros import update_parametro, get_parametro
from app.models.parametro import ParametroUpdate

router = APIRouter()

@router.get("/mps")
def get_mps(semanas: int = 6, db: Session = Depends(get_session)):
    """
    Obtiene el Plan Maestro de Producción (MPS).
    """
    try:
        mps = generar_mps(db, semanas)
        return mps
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar MPS: {str(e)}")

@router.post("/mps/guardar")
def save_mps_adjustments(
    ajustes: Dict[str, Any] = Body(...),
    db: Session = Depends(get_session)
):
    """
    Guarda los ajustes del MPS para un SKU.
    """
    try:
        sku_id = ajustes.get("sku_id")
        stock_seguridad = ajustes.get("stock_seguridad", {})
        scrap = ajustes.get("scrap", {})
        
        if not sku_id:
            raise HTTPException(status_code=400, detail="Se requiere sku_id")
        
        success = guardar_ajustes_mps(db, sku_id, stock_seguridad, scrap)
        
        if success:
            return {"success": True, "message": "Ajustes guardados correctamente"}
        else:
            raise HTTPException(status_code=500, detail="Error al guardar ajustes")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
