from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from typing import Dict, Any, List

from app.db.session import get_session
from app.services.kpis import obtener_kpis, obtener_kpis_historicos

router = APIRouter()

@router.get("/dashboard/kpis")
def get_kpis(db: Session = Depends(get_session)):
    """
    Obtiene los KPIs actuales.
    """
    try:
        kpis = obtener_kpis(db)
        return kpis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener KPIs: {str(e)}")

@router.get("/dashboard/kpis/historico")
def get_kpis_historicos(dias: int = 90, db: Session = Depends(get_session)):
    """
    Obtiene el historial de KPIs.
    """
    try:
        historico = obtener_kpis_historicos(db, dias)
        return historico
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener historial de KPIs: {str(e)}")
