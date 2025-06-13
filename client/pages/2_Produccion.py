import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from services.api_client import APIClient
from components.tables import create_editable_table
from components.forms import create_form

# Inicializar cliente API
api_client = APIClient()

# Configuración de la página
st.set_page_config(page_title="Producción - Café de Altura", page_icon="☕")

# Título de la página
st.title("🏭 Registro de Producción")

# Función para cargar SKUs
@st.cache_data(ttl=300)
def load_skus():
    response = api_client.get("/skus")
    if isinstance(response, list):
        return pd.DataFrame(response)
    return pd.DataFrame()

# Función para cargar lotes de producción
@st.cache_data(ttl=60)
def load_produccion(filtros=None):
    params = {}
    if filtros:
        if filtros.get("sku_id"):
            params["sku_id"] = filtros["sku_id"]
        if filtros.get("semana_iso"):
            params["semana_iso"] = filtros["semana_iso"]
        if filtros.get("año_iso"):
            params["año_iso"] = filtros["año_iso"]
    
    response = api_client.get("/produccion", params=params)
    if isinstance(response, list):
        return pd.DataFrame(response)
    return pd.DataFrame()

# Cargar datos
skus_df = load_skus()
produccion_df = load_produccion()

# Crear pestañas
tab1, tab2, tab3 = st.tabs(["Registro de Producción", "Historial de Producción", "Análisis de Scrap"])

with tab1:
    st.subheader("Registrar Nuevo Lote de Producción")
    
    # Formulario para nuevo lote
    with st.form("nuevo_lote_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            sku_id = st.selectbox(
                "Producto (SKU)",
                options=skus_df["id"].tolist() if not skus_df.empty else [],
                format_func=lambda x: f"{skus_df[skus_df['id'] == x]['nombre'].iloc[0]} ({skus_df[skus_df['id'] == x]['presentacion_g'].iloc[0]}g)" if not skus_df.empty else "",
            )
            
            semana_iso = st.number_input("Semana ISO", min_value=1, max_value=53, value=datetime.now().isocalendar()[1])
            año_iso = st.number_input("Año", min_value=2020, max_value=2030, value=datetime.now().isocalendar()[0])
        
        with col2:
            kg_verde = st.number_input("Kg de Café Verde", min_value=1.0, value=60.0, step=1.0)
            unidades_producidas = st.number_input("Unidades Producidas", min_value=1, value=100)
            
            # Mostrar información del SKU seleccionado
            if sku_id and not skus_df.empty:
                sku_info = skus_df[skus_df["id"] == sku_id].iloc[0]
                st.info(f"Producto: {sku_info['nombre']} - {sku_info['presentacion_g']}g")
        
        submit_button = st.form_submit_button("Registrar Lote")
        
        if submit_button:
            nuevo_lote = {
                "sku_id": sku_id,
                "semana_iso": int(semana_iso),
                "año_iso": int(año_iso),
                "kg_verde": float(kg_verde),
                "unidades_producidas": int(unidades_producidas)
            }
            
            response = api_client.post("/produccion", json=nuevo_lote)
            
            if "id" in response:
                st.success(f"Lote registrado correctamente con ID: {response['id']}")
                # Mostrar información de scrap calculado
                if "scrap" in response:
                    st.info(f"Scrap calculado: {response['scrap']:.2%}")
                # Invalidar caché para recargar datos
                load_produccion.clear()
            else:
                st.error(f"Error al registrar el lote: {response.get('detail', 'Error desconocido')}")

with tab2:
    st.subheader("Historial de Lotes de Producción")
    
    # Filtros para el historial
    col1, col2, col3 = st.columns(3)
    
    with col1:
        sku_filter = st.selectbox(
            "Filtrar por Producto",
            options=[None] + skus_df["id"].tolist() if not skus_df.empty else [None],
            format_func=lambda x: "Todos los productos" if x is None else f"{skus_df[skus_df['id'] == x]['nombre'].iloc[0]} ({skus_df[skus_df['id'] == x]['presentacion_g'].iloc[0]}g)" if not skus_df.empty else "",
            key="hist_sku_filter"
        )
    
    with col2:
        semana_filter = st.number_input("Filtrar por Semana ISO", min_value=0, max_value=53, value=0, key="hist_semana_filter")
        if semana_filter == 0:
            semana_filter = None
    
    with col3:
        año_filter = st.number_input("Filtrar por Año", min_value=0, max_value=2030, value=0, key="hist_año_filter")
        if año_filter == 0:
            año_filter = None
    
    # Botón para aplicar filtros
    if st.button("Aplicar Filtros", key="hist_apply_filters"):
        filtros = {
            "sku_id": sku_filter,
            "semana_iso": semana_filter,
            "año_iso": año_filter
        }
        produccion_df = load_produccion(filtros=filtros)
    
    # Mostrar tabla de producción
    if not produccion_df.empty:
        # Preparar datos para mostrar
        display_df = produccion_df.copy()
        
        # Unir con SKUs para mostrar nombres
        if not skus_df.empty:
            display_df = display_df.merge(
                skus_df[["id", "nombre", "presentacion_g"]],
                left_on="sku_id",
                right_on="id",
                suffixes=("", "_sku")
            )
            display_df["producto"] = display_df["nombre"] + " (" + display_df["presentacion_g"].astype(str) + "g)"
        
        # Formatear scrap como porcentaje
        if "scrap" in display_df.columns:
            display_df["scrap_pct"] = display_df["scrap"] * 100
        
        # Seleccionar y ordenar columnas para mostrar
        cols_to_display = ["id", "producto", "semana_iso", "año_iso", "kg_verde", "unidades_producidas", "scrap_pct"]
        display_df = display_df[cols_to_display].sort_values(by=["año_iso", "semana_iso"], ascending=False)
        
        # Crear tabla editable
        edited_df = create_editable_table(
            display_df,
            key="produccion_table",
            column_config={
                "id": st.column_config.NumberColumn("ID", disabled=True),
                "producto": st.column_config.TextColumn("Producto", disabled=True),
                "semana_iso": st.column_config.NumberColumn("Semana ISO"),
                "año_iso": st.column_config.NumberColumn("Año"),
                "kg_verde": st.column_config.NumberColumn("Kg Verde", format="%.2f"),
                "unidades_producidas": st.column_config.NumberColumn("Unidades Producidas"),
                "scrap_pct": st.column_config.NumberColumn("% Scrap", format="%.2f", disabled=True),
            },
            hide_index=True,
        )
        
        # Detectar cambios y actualizar
        if st.session_state.get("produccion_table_edited", False):
            for idx, row in edited_df.iterrows():
                original_row = display_df.loc[idx]
                if (row["kg_verde"] != original_row["kg_verde"] or 
                    row["unidades_producidas"] != original_row["unidades_producidas"] or
                    row["semana_iso"] != original_row["semana_iso"] or
                    row["año_iso"] != original_row["año_iso"]):
                    
                    # Preparar datos para actualización
                    updated_data = {
                        "kg_verde": float(row["kg_verde"]),
                        "unidades_producidas": int(row["unidades_producidas"]),
                        "semana_iso": int(row["semana_iso"]),
                        "año_iso": int(row["año_iso"])
                    }
                    
                    # Enviar actualización a la API
                    response = api_client.put(f"/produccion/{row['id']}", json=updated_data)
                    
                    if "id" in response:
                        st.success(f"Lote ID {row['id']} actualizado correctamente")
                        # Mostrar información de scrap recalculado
                        if "scrap" in response:
                            st.info(f"Scrap recalculado: {response['scrap']:.2%}")
                        # Invalidar caché
                        load_produccion.clear()
                    else:
                        st.error(f"Error al actualizar el lote: {response.get('detail', 'Error desconocido')}")
            
            # Resetear flag de edición
            st.session_state["produccion_table_edited"] = False
        
        # Botón para eliminar lotes seleccionados
        if not display_df.empty:
            selected_rows = st.multiselect(
                "Seleccionar lotes para eliminar",
                options=display_df["id"].tolist(),
                format_func=lambda x: f"ID: {x} - {display_df[display_df['id'] == x]['producto'].iloc[0]} (Semana {display_df[display_df['id'] == x]['semana_iso'].iloc[0]}/{display_df[display_df['id'] == x]['año_iso'].iloc[0]})"
            )
            
            if selected_rows:
                if st.button("Eliminar Lotes Seleccionados"):
                    for lote_id in selected_rows:
                        response = api_client.delete(f"/produccion/{lote_id}")
                        if response.get("success", False):
                            st.success(f"Lote ID {lote_id} eliminado correctamente")
                        else:
                            st.error(f"Error al eliminar el lote ID {lote_id}: {response.get('detail', 'Error desconocido')}")
                    
                    # Invalidar caché
                    load_produccion.clear()
                    st.experimental_rerun()
    else:
        st.info("No hay lotes de producción registrados o que coincidan con los filtros aplicados.")

with tab3:
    st.subheader("Análisis de Scrap por Producto")
    
    if not produccion_df.empty:
        # Preparar datos para análisis
        if not skus_df.empty:
            analisis_df = produccion_df.merge(
                skus_df[["id", "nombre", "presentacion_g"]],
                left_on="sku_id",
                right_on="id",
                suffixes=("", "_sku")
            )
            analisis_df["producto"] = analisis_df["nombre"] + " (" + analisis_df["presentacion_g"].astype(str) + "g)"
        else:
            analisis_df = produccion_df.copy()
            analisis_df["producto"] = analisis_df["sku_id"].astype(str)
        
        # Calcular estadísticas de scrap por producto
        scrap_stats = analisis_df.groupby("producto").agg(
            scrap_promedio=("scrap", "mean"),
            scrap_min=("scrap", "min"),
            scrap_max=("scrap", "max"),
            kg_verde_total=("kg_verde", "sum"),
            unidades_total=("unidades_producidas", "sum"),
            lotes=("id", "count")
        ).reset_index()
        
        # Formatear porcentajes
        scrap_stats["scrap_promedio_pct"] = scrap_stats["scrap_promedio"] * 100
        scrap_stats["scrap_min_pct"] = scrap_stats["scrap_min"] * 100
        scrap_stats["scrap_max_pct"] = scrap_stats["scrap_max"] * 100
        
        # Mostrar tabla de estadísticas
        st.dataframe(
            scrap_stats[["producto", "scrap_promedio_pct", "scrap_min_pct", "scrap_max_pct", "kg_verde_total", "unidades_total", "lotes"]],
            column_config={
                "producto": st.column_config.TextColumn("Producto"),
                "scrap_promedio_pct": st.column_config.NumberColumn("% Scrap Promedio", format="%.2f"),
                "scrap_min_pct": st.column_config.NumberColumn("% Scrap Mínimo", format="%.2f"),
                "scrap_max_pct": st.column_config.NumberColumn("% Scrap Máximo", format="%.2f"),
                "kg_verde_total": st.column_config.NumberColumn("Kg Verde Total", format="%.2f"),
                "unidades_total": st.column_config.NumberColumn("Unidades Totales"),
                "lotes": st.column_config.NumberColumn("Cantidad de Lotes"),
            },
            hide_index=True,
        )
        
        # Gráfico de scrap promedio por producto
        st.subheader("Scrap Promedio por Producto")
        chart_data = scrap_stats[["producto", "scrap_promedio_pct"]].set_index("producto")
        st.bar_chart(chart_data)
        
        # Gráfico de tendencia de scrap por semana
        st.subheader("Tendencia de Scrap por Semana")
        
        # Preparar datos para el gráfico de tendencia
        analisis_df["periodo"] = analisis_df["año_iso"].astype(str) + "-S" + analisis_df["semana_iso"].astype(str).str.zfill(2)
        trend_data = analisis_df.groupby(["periodo", "producto"]).agg(
            scrap_promedio=("scrap", "mean")
        ).reset_index()
        
        # Convertir a formato wide para el gráfico
        trend_pivot = trend_data.pivot(index="periodo", columns="producto", values="scrap_promedio")
        
        # Mostrar gráfico
        st.line_chart(trend_pivot * 100)  # Convertir a porcentaje
    else:
        st.info("No hay datos de producción disponibles para analizar.")
