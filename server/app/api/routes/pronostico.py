from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from typing import Dict, Any

from app.db.session import get_session
from app.services.pronostico import entrenar_y_pronosticar, obtener_pronostico_futuro

router = APIRouter()

@router.get("/pronostico")
def get_pronostico(semanas: int = 6, db: Session = Depends(get_session)):
    """
    Obtiene el pronóstico para las próximas semanas.
    """
    try:
        pronostico = obtener_pronostico_futuro(db, semanas)
        return pronostico
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener pronóstico: {str(e)}")

@router.post("/pronostico/reentrenar")
def reentrenar_pronostico(db: Session = Depends(get_session)):
    """
    Reentrenar el modelo de pronóstico.
    """
    try:
        entrenar_y_pronosticar(db)
        return {"success": True, "message": "Pronóstico reentrenado correctamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al reentrenar pronóstico: {str(e)}")
