import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import io
from services.api_client import APIClient

# Inicializar cliente API
api_client = APIClient()

# Configuración de la página
st.set_page_config(page_title="MPS - Café de Altura", page_icon="☕", layout="wide")

# Título de la página
st.title("📅 Plan Maestro de Producción (MPS)")

# Función para cargar SKUs
@st.cache_data(ttl=300)
def load_skus():
    response = api_client.get("/skus")
    if isinstance(response, list):
        return pd.DataFrame(response)
    return pd.DataFrame()

# Función para cargar datos del MPS
@st.cache_data(ttl=60)
def load_mps():
    response = api_client.get("/mps")
    if isinstance(response, dict) and "data" in response:
        return response
    return {"data": [], "semanas": [], "capacidad_semanal": 0}

# Función para actualizar el pronóstico
def actualizar_pronostico():
    with st.spinner("Actualizando pronóstico... Esto puede tomar unos segundos."):
        response = api_client.post("/pronostico/reentrenar")
        if response.get("success", False):
            st.success("Pronóstico actualizado correctamente")
            # Invalidar caché
            load_mps.clear()
            return True
        else:
            st.error(f"Error al actualizar el pronóstico: {response.get('detail', 'Error desconocido')}")
            return False

# Cargar datos
skus_df = load_skus()
mps_data = load_mps()

# Extraer datos del MPS
mps_items = mps_data.get("data", [])
semanas = mps_data.get("semanas", [])
capacidad_semanal = mps_data.get("capacidad_semanal", 0)

# Crear DataFrame del MPS
if mps_items and semanas:
    # Crear lista para almacenar filas del DataFrame
    rows = []
    
    for item in mps_items:
        sku_id = item.get("sku_id")
        sku_nombre = item.get("nombre", "")
        presentacion = item.get("presentacion_g", 0)
        
        # Datos base del SKU
        base_row = {
            "sku_id": sku_id,
            "producto": f"{sku_nombre} ({presentacion}g)"
        }
        
        # Agregar datos de demanda
        for i, semana in enumerate(semanas):
            demanda = item.get("demanda", {}).get(semana, 0)
            inv_inicial = item.get("inventario_inicial", {}).get(semana, 0)
            ss = item.get("stock_seguridad", {}).get(semana, 0)
            scrap = item.get("scrap", {}).get(semana, 0)
            produccion = item.get("produccion", {}).get(semana, 0)
            inv_final = item.get("inventario_final", {}).get(semana, 0)
            alerta = item.get("alertas", {}).get(semana, [])
            
            base_row[f"demanda_{i}"] = demanda
            base_row[f"inv_inicial_{i}"] = inv_inicial
            base_row[f"ss_{i}"] = ss
            base_row[f"scrap_{i}"] = scrap
            base_row[f"produccion_{i}"] = produccion
            base_row[f"inv_final_{i}"] = inv_final
            base_row[f"alerta_{i}"] = alerta
        
        rows.append(base_row)
    
    # Crear DataFrame
    mps_df = pd.DataFrame(rows)
else:
    mps_df = pd.DataFrame()

# Mostrar información de semanas
if semanas:
    st.subheader("Horizonte de Planificación")
    
    # Mostrar las semanas del horizonte
    semanas_info = []
    for i, semana in enumerate(semanas):
        año, num_semana = semana.split("-S")
        # Calcular fecha aproximada del lunes de esa semana
        fecha_lunes = datetime.strptime(f"{año}-{int(num_semana)}-1", "%Y-%W-%w")
        semanas_info.append({
            "semana": semana,
            "fecha_inicio": fecha_lunes.strftime("%d/%m/%Y"),
            "fecha_fin": (fecha_lunes + timedelta(days=6)).strftime("%d/%m/%Y")
        })
    
    # Mostrar tabla de semanas
    semanas_df = pd.DataFrame(semanas_info)
    st.dataframe(
        semanas_df,
        column_config={
            "semana": st.column_config.TextColumn("Semana ISO"),
            "fecha_inicio": st.column_config.TextColumn("Fecha Inicio"),
            "fecha_fin": st.column_config.TextColumn("Fecha Fin"),
        },
        hide_index=True,
    )

# Botón para actualizar pronóstico
col1, col2 = st.columns([1, 3])
with col1:
    if st.button("🔄 Actualizar Pronóstico", use_container_width=True):
        if actualizar_pronostico():
            st.experimental_rerun()

# Mostrar capacidad semanal
with col2:
    st.info(f"Capacidad de producción semanal: {capacidad_semanal} kg de café verde")

# Crear pestañas para diferentes vistas del MPS
tab1, tab2, tab3 = st.tabs(["Vista General", "Edición de Parámetros", "Alertas"])

with tab1:
    if not mps_df.empty:
        st.subheader("Plan Maestro de Producción - Vista General")
        
        # Preparar datos para la vista general
        vista_general = []
        
        for _, row in mps_df.iterrows():
            producto = row["producto"]
            
            for i in range(len(semanas)):
                vista_general.append({
                    "producto": producto,
                    "semana": semanas[i],
                    "demanda": row[f"demanda_{i}"],
                    "inv_inicial": row[f"inv_inicial_{i}"],
                    "produccion": row[f"produccion_{i}"],
                    "inv_final": row[f"inv_final_{i}"],
                    "tiene_alerta": len(row[f"alerta_{i}"]) > 0
                })
        
        # Convertir a DataFrame
        vista_df = pd.DataFrame(vista_general)
        
        # Crear tabla pivotada para mejor visualización
        pivot_demanda = vista_df.pivot(index="producto", columns="semana", values="demanda")
        pivot_produccion = vista_df.pivot(index="producto", columns="semana", values="produccion")
        pivot_inv_final = vista_df.pivot(index="producto", columns="semana", values="inv_final")
        
        # Mostrar tablas
        st.write("### Demanda Proyectada (unidades)")
        st.dataframe(pivot_demanda)
        
        st.write("### Plan de Producción (unidades)")
        st.dataframe(pivot_produccion)
        
        st.write("### Inventario Final Proyectado (unidades)")
        st.dataframe(pivot_inv_final)
        
        # Opción para exportar a Excel
        buffer = io.BytesIO()
        
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            pivot_demanda.to_excel(writer, sheet_name="Demanda")
            pivot_produccion.to_excel(writer, sheet_name="Producción")
            pivot_inv_final.to_excel(writer, sheet_name="Inventario Final")
        
        buffer.seek(0)
        
        st.download_button(
            label="📥 Exportar MPS a Excel",
            data=buffer,
            file_name=f"MPS_Cafe_de_Altura_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    else:
        st.warning("No hay datos disponibles para el MPS. Intente actualizar el pronóstico.")

with tab2:
    if not mps_df.empty:
        st.subheader("Edición de Parámetros del MPS")
        
        # Seleccionar producto para editar
        producto_seleccionado = st.selectbox(
            "Seleccionar Producto",
            options=mps_df["sku_id"].tolist(),
            format_func=lambda x: mps_df[mps_df["sku_id"] == x]["producto"].iloc[0]
        )
        
        if producto_seleccionado:
            # Filtrar datos del producto seleccionado
            producto_row = mps_df[mps_df["sku_id"] == producto_seleccionado].iloc[0]
            
            # Crear datos para edición
            edicion_data = []
            
            for i, semana in enumerate(semanas):
                edicion_data.append({
                    "semana": semana,
                    "demanda": producto_row[f"demanda_{i}"],
                    "inv_inicial": producto_row[f"inv_inicial_{i}"],
                    "ss": producto_row[f"ss_{i}"],
                    "scrap": producto_row[f"scrap_{i}"] * 100,  # Convertir a porcentaje
                    "produccion": producto_row[f"produccion_{i}"],
                    "inv_final": producto_row[f"inv_final_{i}"],
                    "alerta": ", ".join(producto_row[f"alerta_{i}"]) if producto_row[f"alerta_{i}"] else ""
                })
            
            # Crear DataFrame para edición
            edicion_df = pd.DataFrame(edicion_data)
            
            # Crear tabla editable
            edited_df = st.data_editor(
                edicion_df,
                column_config={
                    "semana": st.column_config.TextColumn("Semana ISO", disabled=True),
                    "demanda": st.column_config.NumberColumn("Demanda", disabled=True),
                    "inv_inicial": st.column_config.NumberColumn("Inv. Inicial", disabled=True),
                    "ss": st.column_config.NumberColumn("Stock Seguridad", min_value=0),
                    "scrap": st.column_config.NumberColumn("% Scrap", min_value=0, max_value=100, format="%.2f"),
                    "produccion": st.column_config.NumberColumn("Producción", disabled=True),
                    "inv_final": st.column_config.NumberColumn("Inv. Final", disabled=True),
                    "alerta": st.column_config.TextColumn("Alertas", disabled=True),
                },
                hide_index=True,
                key="mps_editor"
            )
            
            # Botón para guardar cambios
            if st.button("Guardar Cambios"):
                # Preparar datos para enviar a la API
                updates = {
                    "sku_id": producto_seleccionado,
                    "stock_seguridad": {},
                    "scrap": {}
                }
                
                for i, row in edited_df.iterrows():
                    semana = row["semana"]
                    updates["stock_seguridad"][semana] = int(row["ss"])
                    updates["scrap"][semana] = float(row["scrap"]) / 100  # Convertir de porcentaje a decimal
                
                # Enviar actualización a la API
                response = api_client.post("/mps/guardar", json=updates)
                
                if response.get("success", False):
                    st.success("Parámetros actualizados correctamente")
                    # Invalidar caché
                    load_mps.clear()
                    st.experimental_rerun()
                else:
                    st.error(f"Error al actualizar los parámetros: {response.get('detail', 'Error desconocido')}")
    else:
        st.warning("No hay datos disponibles para editar. Intente actualizar el pronóstico.")

with tab3:
    if not mps_df.empty:
        st.subheader("Alertas del MPS")
        
        # Recopilar todas las alertas
        alertas = []
        
        for _, row in mps_df.iterrows():
            producto = row["producto"]
            sku_id = row["sku_id"]
            
            for i, semana in enumerate(semanas):
                alertas_semana = row[f"alerta_{i}"]
                
                if alertas_semana:
                    for alerta in alertas_semana:
                        alertas.append({
                            "producto": producto,
                            "sku_id": sku_id,
                            "semana": semana,
                            "mensaje": alerta
                        })
        
        # Convertir a DataFrame
        alertas_df = pd.DataFrame(alertas)
        
        if not alertas_df.empty:
            # Mostrar alertas
            st.dataframe(
                alertas_df,
                column_config={
                    "producto": st.column_config.TextColumn("Producto"),
                    "semana": st.column_config.TextColumn("Semana"),
                    "mensaje": st.column_config.TextColumn("Mensaje de Alerta"),
                },
                hide_index=True,
            )
            
            # Resumen de alertas
            st.metric("Total de Alertas", len(alertas_df))
            
            # Agrupar por tipo de alerta
            if "mensaje" in alertas_df.columns:
                tipos_alerta = alertas_df["mensaje"].value_counts().reset_index()
                tipos_alerta.columns = ["Tipo de Alerta", "Cantidad"]
                
                st.write("### Resumen por Tipo de Alerta")
                st.dataframe(tipos_alerta, hide_index=True)
        else:
            st.success("No hay alertas en el plan actual.")
    else:
        st.warning("No hay datos disponibles para mostrar alertas. Intente actualizar el pronóstico.")

# Sección para ajustar capacidad semanal
st.subheader("Ajustar Capacidad de Producción")

with st.form("capacidad_form"):
    nueva_capacidad = st.number_input(
        "Capacidad Semanal (kg de café verde)",
        min_value=1.0,
        value=float(capacidad_semanal),
        step=1.0
    )
    
    submit_capacidad = st.form_submit_button("Actualizar Capacidad")
    
    if submit_capacidad and nueva_capacidad != capacidad_semanal:
        # Preparar datos para enviar a la API
        params = {
            "nombre": "capacidad_semanal",
            "valor": str(nueva_capacidad)
        }
        
        # Enviar actualización a la API
        response = api_client.put("/parametros/capacidad_semanal", json=params)
        
        if response.get("success", False):
            st.success("Capacidad actualizada correctamente")
            # Invalidar caché
            load_mps.clear()
            st.experimental_rerun()
        else:
            st.error(f"Error al actualizar la capacidad: {response.get('detail', 'Error desconocido')}")
