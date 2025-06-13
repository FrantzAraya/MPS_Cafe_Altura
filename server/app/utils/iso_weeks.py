from datetime import datetime, date, timedelta
from typing import Tuple

def fecha_a_semana_iso(fecha: date) -> Tuple[int, int]:
    """
    Convierte una fecha a año y semana ISO.
    
    Args:
        fecha: Fecha a convertir
    
    Returns:
        Tupla (año_iso, semana_iso)
    """
    iso_calendar = fecha.isocalendar()
    return iso_calendar[0], iso_calendar[1]

def semana_iso_a_fecha(año: int, semana: int, dia: int = 1) -> date:
    """
    Convierte un año y semana ISO a fecha.
    
    Args:
        año: Año ISO
        semana: Semana ISO
        dia: Día de la semana (1=lunes, 7=domingo)
    
    Returns:
        Fecha correspondiente
    """
    # El 4 de enero siempre está en la primera semana del año
    jan4 = date(año, 1, 4)
    # Calcular el lunes de la primera semana
    first_monday = jan4 - timedelta(days=jan4.weekday())
    # Calcular la fecha deseada
    target_date = first_monday + timedelta(weeks=semana-1, days=dia-1)
    return target_date

def formato_semana_iso(año: int, semana: int) -> str:
    """
    Formatea un año y semana ISO como string.
    
    Args:
        año: Año ISO
        semana: Semana ISO
    
    Returns:
        String con formato "YYYY-SWW"
    """
    return f"{año}-S{semana:02d}"

def parsear_semana_iso(semana_str: str) -> Tuple[int, int]:
    """
    Parsea un string de semana ISO.
    
    Args:
        semana_str: String con formato "YYYY-SWW"
    
    Returns:
        Tupla (año, semana)
    """
    partes = semana_str.split("-S")
    if len(partes) != 2:
        raise ValueError(f"Formato de semana ISO inválido: {semana_str}")
    
    año = int(partes[0])
    semana = int(partes[1])
    
    return año, semana
