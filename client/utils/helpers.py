import pandas as pd
from datetime import datetime, timedelta

def get_iso_week_dates(year, week):
    """
    Obtiene las fechas de inicio y fin de una semana ISO.
    
    Args:
        year: Año
        week: Número de semana ISO
    
    Returns:
        Tupla con fecha de inicio y fin (datetime)
    """
    # Crear una fecha en la semana especificada
    # El 4 de enero siempre está en la primera semana del año
    jan4 = datetime(year, 1, 4)
    # Calcular el lunes de la primera semana
    first_monday = jan4 - timedelta(days=jan4.weekday())
    
    # Calcular el lunes de la semana deseada
    target_monday = first_monday + timedelta(weeks=week-1)
    
    # El domingo es 6 días después
    target_sunday = target_monday + timedelta(days=6)
    
    return target_monday, target_sunday

def format_iso_week(year, week):
    """
    Formatea una semana ISO como string.
    
    Args:
        year: Año
        week: Número de semana ISO
    
    Returns:
        String con formato "YYYY-SWW"
    """
    return f"{year}-S{week:02d}"

def parse_iso_week(iso_week_str):
    """
    Parsea un string de semana ISO.
    
    Args:
        iso_week_str: String con formato "YYYY-SWW"
    
    Returns:
        Tupla (año, semana)
    """
    parts = iso_week_str.split("-S")
    if len(parts) != 2:
        raise ValueError(f"Formato de semana ISO inválido: {iso_week_str}")
    
    year = int(parts[0])
    week = int(parts[1])
    
    return year, week

def calculate_scrap(kg_verde, unidades_producidas, presentacion_g):
    """
    Calcula el porcentaje de scrap.
    
    Args:
        kg_verde: Kilogramos de café verde
        unidades_producidas: Unidades producidas
        presentacion_g: Gramos por unidad
    
    Returns:
        Porcentaje de scrap (0-1)
    """
    # Convertir kg a g
    g_verde = kg_verde * 1000
    
    # Calcular gramos teóricos en producto terminado
    g_producto = unidades_producidas * presentacion_g
    
    # Calcular scrap
    if g_verde > 0:
        scrap = 1 - (g_producto / g_verde)
        return max(0, min(1, scrap))  # Limitar entre 0 y 1
    else:
        return 0
