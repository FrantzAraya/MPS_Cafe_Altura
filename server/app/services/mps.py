import pandas as pd
import numpy as np
from sqlmodel import Session, select
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from app.models.sku import SKU
from app.models.produccion import Produccion
from app.services.pronostico import obtener_pronostico_futuro
from app.crud.produccion import get_scrap_promedio
from app.crud.parametros import get_parametro

def calcular_inventario_inicial(
    db: Session,
    sku_id: int,
    semana_actual: str
) -> int:
    """
    Calcula el inventario inicial para un SKU en la semana actual.
    
    Args:
        db: Sesión de base de datos
        sku_id: ID del SKU
        semana_actual: Semana actual en formato "YYYY-SWW"
    
    Returns:
        Inventario inicial en unidades
    """
    # En una implementación real, esto se obtendría de un sistema de inventario
    # Por ahora, asumimos un valor inicial basado en la producción reciente
    
    # Obtener producciones recientes
    query = select(Produccion).where(Produccion.sku_id == sku_id)
    producciones = db.exec(query).all()
    
    if not producciones:
        return 100  # Valor por defecto
    
    # Convertir a DataFrame
    prod_df = pd.DataFrame([{
        "semana_iso": p.semana_iso,
        "año_iso": p.año_iso,
        "unidades_producidas": p.unidades_producidas
    } for p in producciones])
    
    # Crear clave de semana
    prod_df["semana_clave"] = prod_df["año_iso"].astype(str) + "-S" + prod_df["semana_iso"].astype(str).str.zfill(2)
    
    # Calcular promedio de producción
    promedio_produccion = prod_df["unidades_producidas"].mean()
    
    # Inventario inicial aproximado (2 semanas de producción)
    inventario_inicial = int(promedio_produccion * 2)
    
    return max(100, inventario_inicial)  # Mínimo 100 unidades

def calcular_stock_seguridad(
    db: Session,
    sku_id: int,
    demanda: int
) -> int:
    """
    Calcula el stock de seguridad para un SKU.
    
    Args:
        db: Sesión de base de datos
        sku_id: ID del SKU
        demanda: Demanda proyectada
    
    Returns:
        Stock de seguridad en unidades
    """
    # Obtener nivel de servicio
    param_nivel_servicio = get_parametro(db, "nivel_servicio")
    nivel_servicio = float(param_nivel_servicio.valor) if param_nivel_servicio else 0.95
    
    # Factor de seguridad basado en nivel de servicio
    # Aproximación simple: para 95% usamos 1.65 (distribución normal)
    if nivel_servicio >= 0.99:
        factor = 2.33
    elif nivel_servicio >= 0.98:
        factor = 2.05
    elif nivel_servicio >= 0.95:
        factor = 1.65
    elif nivel_servicio >= 0.90:
        factor = 1.28
    else:
        factor = 1.0
    
    # Calcular stock de seguridad como porcentaje de la demanda
    # En una implementación real, se usaría la desviación estándar de la demanda
    stock_seguridad = int(demanda * 0.2 * factor)
    
    return max(10, stock_seguridad)  # Mínimo 10 unidades

def calcular_produccion_con_regla_60kg(
    db: Session,
    sku_id: int,
    necesidad_neta: int,
    scrap: float
) -> Tuple[int, List[str]]:
    """
    Calcula la cantidad a producir aplicando la regla de 60 kg.
    
    Args:
        db: Sesión de base de datos
        sku_id: ID del SKU
        necesidad_neta: Necesidad neta en unidades
        scrap: Porcentaje de scrap (0-1)
    
    Returns:
        Tupla (cantidad a producir, alertas)
    """
    # Obtener información del SKU
    sku = db.get(SKU, sku_id)
    if not sku:
        return (necesidad_neta, ["SKU no encontrado"])
    
    # Calcular necesidad bruta (considerando scrap)
    if scrap < 1:
        necesidad_bruta = int(necesidad_neta / (1 - scrap))
    else:
        necesidad_bruta = necesidad_neta
    
    # Calcular cuántas unidades salen de 60 kg de café verde
    # Fórmula: (60 kg * 1000 g/kg) / presentación_g * (1 - scrap)
    unidades_por_tanda = int((60 * 1000) / sku.presentacion_g * (1 - scrap))
    
    if unidades_por_tanda <= 0:
        return (necesidad_bruta, ["Error en cálculo de unidades por tanda"])
    
    # Calcular número de tandas completas
    tandas_completas = necesidad_bruta // unidades_por_tanda
    
    # Calcular unidades restantes
    unidades_restantes = necesidad_bruta % unidades_por_tanda
    
    # Calcular kg necesarios para unidades restantes
    kg_restantes = (unidades_restantes * sku.presentacion_g) / (1000 * (1 - scrap))
    
    alertas = []
    
    # Verificar si los kg restantes superan 60 kg
    if kg_restantes > 60:
        # Esto no debería ocurrir, pero por si acaso
        tandas_completas += 1
        unidades_restantes = 0
        alertas.append("Error en cálculo de tandas")
    
    # Calcular producción total
    produccion_total = (tandas_completas * unidades_por_tanda) + unidades_restantes
    
    return (produccion_total, alertas)

def generar_mps(db: Session, semanas: int = 6) -> Dict[str, Any]:
    """
    Genera el Plan Maestro de Producción (MPS).
    
    Args:
        db: Sesión de base de datos
        semanas: Número de semanas a planificar
    
    Returns:
        Diccionario con el MPS
    """
    # Obtener pronóstico
    pronostico = obtener_pronostico_futuro(db, semanas)
    
    # Obtener capacidad semanal
    param_capacidad = get_parametro(db, "capacidad_semanal")
    capacidad_semanal = float(param_capacidad.valor) if param_capacidad else 300
    
    # Extraer semanas únicas
    todas_semanas = set()
    for sku_data in pronostico.values():
        todas_semanas.update(sku_data["semanas"])
    
    semanas_ordenadas = sorted(todas_semanas)
    
    # Generar MPS para cada SKU
    mps_data = []
    
    for sku_id, sku_data in pronostico.items():
        # Obtener scrap promedio
        scrap_promedio = get_scrap_promedio(db, sku_id)
        
        # Inicializar datos del SKU en el MPS
        mps_sku = {
            "sku_id": sku_id,
            "nombre": sku_data["nombre"],
            "presentacion_g": sku_data["presentacion_g"],
            "demanda": {},
            "inventario_inicial": {},
            "stock_seguridad": {},
            "scrap": {},
            "produccion": {},
            "inventario_final": {},
            "alertas": {}
        }
        
        # Inventario inicial para la primera semana
        inv_inicial = calcular_inventario_inicial(db, sku_id, semanas_ordenadas[0])
        
        # Procesar cada semana
        for i, semana in enumerate(semanas_ordenadas):
            # Obtener demanda de la semana
            demanda = sku_data["demanda"].get(semana, 0)
            
            # Calcular stock de seguridad
            ss = calcular_stock_seguridad(db, sku_id, demanda)
            
            # Usar scrap promedio si no hay un valor específico
            scrap = scrap_promedio
            
            # Calcular necesidad neta
            if i == 0:
                # Primera semana
                necesidad_neta = max(0, demanda + ss - inv_inicial)
            else:
                # Semanas siguientes
                necesidad_neta = max(0, demanda + ss - mps_sku["inventario_final"][semanas_ordenadas[i-1]])
            
            # Aplicar regla de 60 kg
            produccion, alertas_produccion = calcular_produccion_con_regla_60kg(
                db, sku_id, necesidad_neta, scrap
            )
            
            # Calcular inventario final
            if i == 0:
                inv_final = inv_inicial + int(produccion * (1 - scrap)) - demanda
            else:
                inv_final = mps_sku["inventario_final"][semanas_ordenadas[i-1]] + int(produccion * (1 - scrap)) - demanda
            
            # Almacenar valores
            mps_sku["demanda"][semana] = demanda
            mps_sku["inventario_inicial"][semana] = inv_inicial if i == 0 else mps_sku["inventario_final"][semanas_ordenadas[i-1]]
            mps_sku["stock_seguridad"][semana] = ss
            mps_sku["scrap"][semana] = scrap
            mps_sku["produccion"][semana] = produccion
            mps_sku["inventario_final"][semana] = inv_final
            
            # Verificar alertas
            alertas = []
            
            # Alerta si SS > 1.2 * demanda
            if ss > 1.2 * demanda and demanda > 0:
                alertas.append("Stock de seguridad elevado")
            
            # Alerta si inventario final < stock de seguridad
            if inv_final < ss:
                alertas.append("Inventario final por debajo del stock de seguridad")
            
            # Calcular kg de café verde necesarios
            kg_verde_necesarios = (produccion * sku_data["presentacion_g"]) / (1000 * (1 - scrap))
            
            # Alerta si se excede la capacidad semanal
            if kg_verde_necesarios > capacidad_semanal:
                alertas.append("Excede capacidad semanal")
            
            # Agregar alertas de producción
            alertas.extend(alertas_produccion)
            
            mps_sku["alertas"][semana] = alertas
        
        mps_data.append(mps_sku)
    
    return {
        "semanas": semanas_ordenadas,
        "capacidad_semanal": capacidad_semanal,
        "data": mps_data
    }

def guardar_ajustes_mps(
    db: Session,
    sku_id: int,
    stock_seguridad: Dict[str, int],
    scrap: Dict[str, float]
) -> bool:
    """
    Guarda los ajustes del MPS para un SKU.

    Actualmente es un stub y simplemente devuelve ``True`` sin
    persistir los datos en la base de datos.

    Args:
        db: Sesión de base de datos
        sku_id: ID del SKU
        stock_seguridad: Diccionario de stock de seguridad por semana
        scrap: Diccionario de scrap por semana

    Returns:
        ``True`` si se guardó correctamente, ``False`` en caso contrario
    """
    # TODO: Persistir ajustes de MPS en la base de datos
    # En una implementación real, estos ajustes se guardarían en una tabla
    # Por ahora, simplemente devolvemos True
    return True
