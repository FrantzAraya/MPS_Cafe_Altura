import pandas as pd
import numpy as np
from prophet import Prophet
from sqlmodel import Session, select
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from app.models.venta import Venta
from app.models.sku import SKU
from app.utils.iso_weeks import semana_iso_a_fecha

def obtener_datos_ventas(db: Session, sku_id: Optional[int] = None) -> pd.DataFrame:
    """
    Obtiene los datos de ventas para el pronóstico.
    
    Args:
        db: Sesión de base de datos
        sku_id: ID del SKU (opcional)
    
    Returns:
        DataFrame con los datos de ventas
    """
    # Consultar ventas
    query = select(Venta)
    if sku_id is not None:
        query = query.where(Venta.sku_id == sku_id)
    
    ventas = db.exec(query).all()
    
    if not ventas:
        return pd.DataFrame()
    
    # Convertir a DataFrame
    ventas_df = pd.DataFrame([{
        "sku_id": v.sku_id,
        "fecha": v.fecha,
        "unidades": v.unidades,
        "semana_iso": v.semana_iso,
        "año_iso": v.año_iso
    } for v in ventas])
    
    # Agrupar por semana y SKU
    ventas_semanales = ventas_df.groupby(["sku_id", "año_iso", "semana_iso"]).agg({
        "unidades": "sum"
    }).reset_index()
    
    # Crear columna de fecha para Prophet (primer día de la semana)
    ventas_semanales["ds"] = ventas_semanales.apply(
        lambda row: semana_iso_a_fecha(row["año_iso"], row["semana_iso"]),
        axis=1
    )
    
    # Renombrar columna de unidades para Prophet
    ventas_semanales = ventas_semanales.rename(columns={"unidades": "y"})
    
    return ventas_semanales

def entrenar_modelo(datos: pd.DataFrame) -> Prophet:
    """
    Entrena un modelo de Prophet con los datos proporcionados.
    
    Args:
        datos: DataFrame con columnas 'ds' (fecha) y 'y' (valor)
    
    Returns:
        Modelo entrenado
    """
    # Crear y entrenar modelo
    modelo = Prophet(
        seasonality_mode='multiplicative',
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False,
        changepoint_prior_scale=0.05
    )
    
    modelo.fit(datos)
    
    return modelo

def generar_pronostico(
    modelo: Prophet,
    periodos: int = 26,
    frecuencia: str = 'W'
) -> pd.DataFrame:
    """
    Genera un pronóstico con el modelo entrenado.
    
    Args:
        modelo: Modelo entrenado
        periodos: Número de periodos a pronosticar
        frecuencia: Frecuencia del pronóstico ('W' para semanal)
    
    Returns:
        DataFrame con el pronóstico
    """
    # Generar fechas futuras
    future = modelo.make_future_dataframe(periods=periodos, freq=frecuencia)
    
    # Generar pronóstico
    forecast = modelo.predict(future)
    
    # Extraer columnas relevantes
    resultado = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]
    
    # Redondear valores a enteros positivos
    resultado['yhat'] = np.maximum(0, np.round(resultado['yhat']))
    resultado['yhat_lower'] = np.maximum(0, np.round(resultado['yhat_lower']))
    resultado['yhat_upper'] = np.maximum(0, np.round(resultado['yhat_upper']))
    
    return resultado

def entrenar_y_pronosticar(db: Session) -> Dict[int, Dict[str, List[int]]]:
    """
    Entrena modelos y genera pronósticos para todos los SKUs.
    
    Args:
        db: Sesión de base de datos
    
    Returns:
        Diccionario con pronósticos por SKU
    """
    # Obtener todos los SKUs activos
    skus = db.exec(select(SKU).where(SKU.activo == True)).all()
    
    if not skus:
        return {}
    
    # Diccionario para almacenar pronósticos
    pronosticos = {}
    
    # Procesar cada SKU
    for sku in skus:
        # Obtener datos de ventas
        datos = obtener_datos_ventas(db, sku.id)
        
        # Si no hay datos suficientes, usar un modelo simple
        if len(datos) < 10:
            # Crear pronóstico simple basado en el promedio o un valor por defecto
            if not datos.empty:
                promedio = datos["y"].mean()
            else:
                promedio = 100  # Valor por defecto
            
            # Generar fechas futuras
            hoy = datetime.now()
            fechas_futuras = [hoy + timedelta(weeks=i) for i in range(26)]
            
            # Crear DataFrame de pronóstico
            pronostico = pd.DataFrame({
                "ds": fechas_futuras,
                "yhat": [promedio] * 26,
                "yhat_lower": [promedio * 0.8] * 26,
                "yhat_upper": [promedio * 1.2] * 26
            })
        else:
            # Entrenar modelo
            modelo = entrenar_modelo(datos)
            
            # Generar pronóstico
            pronostico = generar_pronostico(modelo)
        
        # Extraer semanas ISO del pronóstico
        pronostico["año_iso"] = pronostico["ds"].dt.isocalendar().year
        pronostico["semana_iso"] = pronostico["ds"].dt.isocalendar().week
        
        # Crear clave de semana ISO
        pronostico["semana_clave"] = pronostico["año_iso"].astype(str) + "-S" + pronostico["semana_iso"].astype(str).str.zfill(2)
        
        # Almacenar pronóstico
        pronosticos[sku.id] = {
            "semanas": pronostico["semana_clave"].tolist(),
            "demanda": dict(zip(pronostico["semana_clave"], pronostico["yhat"].astype(int).tolist())),
            "demanda_min": dict(zip(pronostico["semana_clave"], pronostico["yhat_lower"].astype(int).tolist())),
            "demanda_max": dict(zip(pronostico["semana_clave"], pronostico["yhat_upper"].astype(int).tolist()))
        }
    
    return pronosticos

def obtener_pronostico_futuro(db: Session, semanas: int = 6) -> Dict[str, Dict]:
    """
    Obtiene el pronóstico para las próximas semanas.
    
    Args:
        db: Sesión de base de datos
        semanas: Número de semanas a pronosticar
    
    Returns:
        Diccionario con pronósticos por SKU y semana
    """
    # Obtener todos los SKUs activos
    skus = db.exec(select(SKU).where(SKU.activo == True)).all()
    
    if not skus:
        return {}
    
    # Generar semanas futuras
    semanas_futuras = []
    hoy = datetime.now()
    año_actual, semana_actual, _ = hoy.isocalendar()
    
    for i in range(semanas):
        fecha = hoy + timedelta(weeks=i)
        año, semana, _ = fecha.isocalendar()
        semanas_futuras.append(f"{año}-S{semana:02d}")
    
    # Obtener pronósticos
    try:
        # Intentar cargar pronósticos desde la base de datos o archivo
        # En una implementación real, esto podría almacenarse en una tabla
        # Por ahora, generamos nuevos pronósticos
        pronosticos = entrenar_y_pronosticar(db)
    except Exception as e:
        print(f"Error al obtener pronósticos: {e}")
        pronosticos = {}
    
    # Filtrar solo las semanas futuras
    resultado = {}
    for sku_id, datos in pronosticos.items():
        semanas_sku = datos["semanas"]
        demanda_sku = datos["demanda"]
        
        # Filtrar semanas futuras
        semanas_filtradas = [s for s in semanas_sku if s in semanas_futuras]
        
        if semanas_filtradas:
            # Obtener información del SKU
            sku = db.get(SKU, sku_id)
            
            resultado[sku_id] = {
                "nombre": sku.nombre if sku else f"SKU {sku_id}",
                "presentacion_g": sku.presentacion_g if sku else 0,
                "semanas": semanas_filtradas,
                "demanda": {s: demanda_sku[s] for s in semanas_filtradas if s in demanda_sku}
            }
    
    return resultado
