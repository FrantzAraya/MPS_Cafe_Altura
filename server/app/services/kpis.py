from sqlmodel import Session, select
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import random
from app.models.sku import SKU
from app.models.venta import Venta
from app.models.produccion import Produccion
from app.crud.parametros import get_parametro

def calcular_dias_inventario(db: Session) -> float:
    """
    Calcula el KPI de días de inventario.
    
    Args:
        db: Sesión de base de datos
    
    Returns:
        Días de inventario
    """
    # En una implementación real, esto se calcularía con datos reales de inventario
    # Por ahora, generamos un valor simulado
    
    # Obtener objetivo de días de inventario
    param = get_parametro(db, "dias_inventario_objetivo")
    objetivo = float(param.valor) if param else 15.0
    
    # Simular valor actual (entre 70% y 130% del objetivo)
    factor = random.uniform(0.7, 1.3)
    dias_inventario = objetivo * factor
    
    return dias_inventario

def calcular_cumplimiento_plan(db: Session) -> float:
    """
    Calcula el KPI de cumplimiento del plan.
    
    Args:
        db: Sesión de base de datos
    
    Returns:
        Porcentaje de cumplimiento (0-1)
    """
    # En una implementación real, esto se calcularía comparando la producción real vs planificada
    # Por ahora, generamos un valor simulado
    
    # Obtener objetivo de cumplimiento
    param = get_parametro(db, "objetivo_cumplimiento_plan")
    objetivo = float(param.valor) if param else 0.95
    
    # Simular valor actual (entre 80% y 105% del objetivo)
    factor = random.uniform(0.8, 1.05)
    cumplimiento = objetivo * factor
    
    return min(1.0, cumplimiento)  # Limitar a 1.0 (100%)

def calcular_otd(db: Session) -> float:
    """
    Calcula el KPI de On-Time Delivery.
    
    Args:
        db: Sesión de base de datos
    
    Returns:
        Porcentaje de OTD (0-1)
    """
    # En una implementación real, esto se calcularía con datos de entregas
    # Por ahora, generamos un valor simulado
    
    # Obtener objetivo de OTD
    param = get_parametro(db, "objetivo_otd")
    objetivo = float(param.valor) if param else 0.98
    
    # Simular valor actual (entre 90% y 102% del objetivo)
    factor = random.uniform(0.9, 1.02)
    otd = objetivo * factor
    
    return min(1.0, otd)  # Limitar a 1.0 (100%)

def calcular_rechazos(db: Session) -> float:
    """
    Calcula el KPI de tasa de rechazos.
    
    Args:
        db: Sesión de base de datos
    
    Returns:
        Porcentaje de rechazos (0-1)
    """
    # En una implementación real, esto se calcularía con datos de control de calidad
    # Por ahora, generamos un valor simulado
    
    # Obtener objetivo de rechazos
    param = get_parametro(db, "objetivo_rechazos")
    objetivo = float(param.valor) if param else 0.02
    
    # Simular valor actual (entre 80% y 150% del objetivo)
    factor = random.uniform(0.8, 1.5)
    rechazos = objetivo * factor
    
    return rechazos

def obtener_kpis(db: Session) -> Dict[str, Any]:
    """
    Obtiene todos los KPIs actuales.
    
    Args:
        db: Sesión de base de datos
    
    Returns:
        Diccionario con los KPIs
    """
    # Calcular KPIs
    dias_inventario = calcular_dias_inventario(db)
    cumplimiento_plan = calcular_cumplimiento_plan(db)
    otd = calcular_otd(db)
    rechazos = calcular_rechazos(db)
    
    # Obtener objetivos
    param_dias = get_parametro(db, "dias_inventario_objetivo")
    param_cumplimiento = get_parametro(db, "objetivo_cumplimiento_plan")
    param_otd = get_parametro(db, "objetivo_otd")
    param_rechazos = get_parametro(db, "objetivo_rechazos")
    
    objetivo_dias = float(param_dias.valor) if param_dias else 15.0
    objetivo_cumplimiento = float(param_cumplimiento.valor) if param_cumplimiento else 0.95
    objetivo_otd = float(param_otd.valor) if param_otd else 0.98
    objetivo_rechazos = float(param_rechazos.valor) if param_rechazos else 0.02
    
    return {
        "dias_inventario": dias_inventario,
        "cumplimiento_plan": cumplimiento_plan,
        "otd": otd,
        "rechazos": rechazos,
        "objetivo_dias_inventario": objetivo_dias,
        "objetivo_cumplimiento_plan": objetivo_cumplimiento,
        "objetivo_otd": objetivo_otd,
        "objetivo_rechazos": objetivo_rechazos
    }

def obtener_kpis_historicos(db: Session, dias: int = 90) -> List[Dict[str, Any]]:
    """
    Obtiene el historial de KPIs.
    
    Args:
        db: Sesión de base de datos
        dias: Número de días de historial
    
    Returns:
        Lista de diccionarios con los KPIs históricos
    """
    # En una implementación real, esto se obtendría de una tabla de historial
    # Por ahora, generamos datos simulados
    
    # Obtener objetivos
    kpis_actuales = obtener_kpis(db)
    
    objetivo_dias = kpis_actuales["objetivo_dias_inventario"]
    objetivo_cumplimiento = kpis_actuales["objetivo_cumplimiento_plan"]
    objetivo_otd = kpis_actuales["objetivo_otd"]
    objetivo_rechazos = kpis_actuales["objetivo_rechazos"]
    
    # Generar fechas
    hoy = datetime.now()
    fechas = [hoy - timedelta(days=i) for i in range(dias)]
    fechas.sort()  # Ordenar de más antiguo a más reciente
    
    # Generar datos históricos
    historico = []
    
    for fecha in fechas:
        # Simular valores con tendencia y algo de ruido
        progreso = fechas.index(fecha) / len(fechas)  # 0 a 1
        
        # Días de inventario: tendencia a mejorar
        dias_inv = objetivo_dias * (0.8 + 0.4 * progreso + random.uniform(-0.1, 0.1))
        
        # Cumplimiento: tendencia a mejorar
        cumpl = objetivo_cumplimiento * (0.85 + 0.2 * progreso + random.uniform(-0.05, 0.05))
        cumpl = min(1.0, cumpl)  # Limitar a 1.0
        
        # OTD: tendencia a mejorar
        otd = objetivo_otd * (0.9 + 0.15 * progreso + random.uniform(-0.03, 0.03))
        otd = min(1.0, otd)  # Limitar a 1.0
        
        # Rechazos: tendencia a disminuir
        rech = objetivo_rechazos * (1.5 - 0.5 * progreso + random.uniform(-0.2, 0.2))
        rech = max(0.001, rech)  # Evitar valores negativos
        
        historico.append({
            "fecha": fecha.strftime("%Y-%m-%d"),
            "dias_inventario": dias_inv,
            "cumplimiento_plan": cumpl,
            "otd": otd,
            "rechazos": rech
        })
    
    return historico
