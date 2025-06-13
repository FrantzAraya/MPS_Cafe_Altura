from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from typing import List

from app.db.session import get_session
from app.models.parametro import Parametro, ParametroUpdate, ParametroRead
from app.crud.parametros import get_parametros, get_parametro, update_parametro

router = APIRouter()

@router.get("/parametros", response_model=List[ParametroRead])
def read_parametros(db: Session = Depends(get_session)):
    """
    Obtiene todos los parámetros.
    """
    return get_parametros(db)

@router.get("/parametros/{nombre}", response_model=ParametroRead)
def read_parametro(nombre: str, db: Session = Depends(get_session)):
    """
    Obtiene un parámetro por su nombre.
    """
    db_parametro = get_parametro(db, nombre)
    if db_parametro is None:
        raise HTTPException(status_code=404, detail="Parámetro no encontrado")
    return db_parametro

@router.put("/parametros/{nombre}", response_model=ParametroRead)
def update_parametro_endpoint(nombre: str, parametro: ParametroUpdate, db: Session = Depends(get_session)):
    """
    Actualiza un parámetro existente.
    """
    db_parametro = update_parametro(db, nombre, parametro)
    if db_parametro is None:
        raise HTTPException(status_code=404, detail="Parámetro no encontrado")
    return db_parametro
