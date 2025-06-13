import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from services.api_client import APIClient
from components.tables import create_editable_table
from components.forms import create_form

# Inicializar cliente API
api_client = APIClient()

# Configuración de la página
st.set_page_config(page_title="Ventas - Café de Altura", page_icon="☕")

# Título de la página
st.title("📊 Registro de Ventas")

# Función para cargar SKUs
@st.cache_data(ttl=300)
def load_skus():
    response = api_client.get("/skus")
    if isinstance(response, list):
        return pd.DataFrame(response)
    return pd.DataFrame()

# Función para cargar ventas
@st.cache_data(ttl=60)
def load_ventas(filtros=None):
    params = {}
    if filtros:
        if filtros.get("sku_id"):
            params["sku_id"] = filtros["sku_id"]
        if filtros.get("fecha_inicio") and filtros.get("fecha_fin"):
            params["fecha_inicio"] = filtros["fecha_inicio"].strftime("%Y-%m-%d")
            params["fecha_fin"] = filtros["fecha_fin"].strftime("%Y-%m-%d")
    
    response = api_client.get("/ventas", params=params)
    if isinstance(response, list):
        df = pd.DataFrame(response)
        if not df.empty:
            df["fecha"] = pd.to_datetime(df["fecha"]).dt.date
            df["semana_iso"] = pd.to_datetime(df["fecha"]).dt.isocalendar().week
            df["año_iso"] = pd.to_datetime(df["fecha"]).dt.isocalendar().year
        return df
    return pd.DataFrame()

# Función para cargar ventas consolidadas por semana
@st.cache_data(ttl=60)
def load_ventas_semanales():
    response = api_client.get("/ventas/semanal")
    if isinstance(response, list):
        return pd.DataFrame(response)
    return pd.DataFrame()

# Cargar datos
skus_df = load_skus()

# Crear pestañas
tab1, tab2, tab3 = st.tabs(["Registro de Ventas", "Ventas por Semana", "Filtros y Búsqueda"])

with tab1:
    st.subheader("Registrar Nueva Venta")
    
    # Formulario para nueva venta
    with st.form("nueva_venta_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            sku_id = st.selectbox(
                "Producto (SKU)",
                options=skus_df["id"].tolist() if not skus_df.empty else [],
                format_func=lambda x: f"{skus_df[skus_df['id'] == x]['nombre'].iloc[0]} ({skus_df[skus_df['id'] == x]['presentacion_g'].iloc[0]}g)" if not skus_df.empty else "",
            )
            
            fecha = st.date_input(
                "Fecha de Venta",
                value=datetime.now().date(),
                max_value=datetime.now().date()
            )
        
        with col2:
            unidades = st.number_input("Unidades Vendidas", min_value=1, value=100)
            
            # Calcular semana ISO
            semana_iso = datetime.strptime(str(fecha), "%Y-%m-%d").isocalendar()[1]
            año_iso = datetime.strptime(str(fecha), "%Y-%m-%d").isocalendar()[0]
            st.info(f"Semana ISO: {semana_iso} del año {año_iso}")
        
        submit_button = st.form_submit_button("Registrar Venta")
        
        if submit_button:
            nueva_venta = {
                "sku_id": sku_id,
                "fecha": fecha.strftime("%Y-%m-%d"),
                "unidades": unidades
            }
            
            response = api_client.post("/ventas", json=nueva_venta)
            
            if "id" in response:
                st.success(f"Venta registrada correctamente con ID: {response['id']}")
                # Invalidar caché para recargar datos
                load_ventas.clear()
                load_ventas_semanales.clear()
            else:
                st.error(f"Error al registrar la venta: {response.get('detail', 'Error desconocido')}")

    # Mostrar últimas ventas
    st.subheader("Últimas Ventas Registradas")
    ventas_df = load_ventas()
    
    if not ventas_df.empty:
        # Preparar datos para mostrar
        display_df = ventas_df.copy()
        
        # Unir con SKUs para mostrar nombres
        if not skus_df.empty:
            display_df = display_df.merge(
                skus_df[["id", "nombre", "presentacion_g"]],
                left_on="sku_id",
                right_on="id",
                suffixes=("", "_sku")
            )
            display_df["producto"] = display_df["nombre"] + " (" + display_df["presentacion_g"].astype(str) + "g)"
            
        # Seleccionar y ordenar columnas para mostrar
        cols_to_display = ["id", "producto", "fecha", "semana_iso", "año_iso", "unidades"]
        display_df = display_df[cols_to_display].sort_values(by="fecha", ascending=False)
        
        # Crear tabla editable
        edited_df = create_editable_table(
            display_df,
            key="ventas_table",
            column_config={
                "id": st.column_config.NumberColumn("ID", disabled=True),
                "producto": st.column_config.TextColumn("Producto", disabled=True),
                "fecha": st.column_config.DateColumn("Fecha"),
                "semana_iso": st.column_config.NumberColumn("Semana ISO", disabled=True),
                "año_iso": st.column_config.NumberColumn("Año", disabled=True),
                "unidades": st.column_config.NumberColumn("Unidades", min_value=1),
            },
            hide_index=True,
        )
        
        # Detectar cambios y actualizar
        if st.session_state.get("ventas_table_edited", False):
            for idx, row in edited_df.iterrows():
                original_row = display_df.loc[idx]
                if (row["unidades"] != original_row["unidades"] or 
                    row["fecha"] != original_row["fecha"]):
                    
                    # Preparar datos para actualización
                    updated_data = {
                        "unidades": int(row["unidades"]),
                        "fecha": row["fecha"].strftime("%Y-%m-%d") if isinstance(row["fecha"], datetime) else row["fecha"]
                    }
                    
                    # Enviar actualización a la API
                    response = api_client.put(f"/ventas/{row['id']}", json=updated_data)
                    
                    if "id" in response:
                        st.success(f"Venta ID {row['id']} actualizada correctamente")
                        # Invalidar caché
                        load_ventas.clear()
                        load_ventas_semanales.clear()
                    else:
                        st.error(f"Error al actualizar la venta: {response.get('detail', 'Error desconocido')}")
            
            # Resetear flag de edición
            st.session_state["ventas_table_edited"] = False
        
        # Botón para eliminar ventas seleccionadas
        if not display_df.empty:
            selected_rows = st.multiselect(
                "Seleccionar ventas para eliminar",
                options=display_df["id"].tolist(),
                format_func=lambda x: f"ID: {x} - {display_df[display_df['id'] == x]['producto'].iloc[0]} ({display_df[display_df['id'] == x]['fecha'].iloc[0]})"
            )
            
            if selected_rows:
                if st.button("Eliminar Ventas Seleccionadas"):
                    for venta_id in selected_rows:
                        response = api_client.delete(f"/ventas/{venta_id}")
                        if response.get("success", False):
                            st.success(f"Venta ID {venta_id} eliminada correctamente")
                        else:
                            st.error(f"Error al eliminar la venta ID {venta_id}: {response.get('detail', 'Error desconocido')}")
                    
                    # Invalidar caché
                    load_ventas.clear()
                    load_ventas_semanales.clear()
                    st.experimental_rerun()
    else:
        st.info("No hay ventas registradas. Utilice el formulario para registrar nuevas ventas.")

with tab2:
    st.subheader("Ventas Consolidadas por Semana")
    
    ventas_semanales = load_ventas_semanales()
    
    if not ventas_semanales.empty:
        # Preparar datos para visualización
        if "sku_id" in ventas_semanales.columns and not skus_df.empty:
            ventas_semanales = ventas_semanales.merge(
                skus_df[["id", "nombre", "presentacion_g"]],
                left_on="sku_id",
                right_on="id",
                suffixes=("", "_sku")
            )
            ventas_semanales["producto"] = ventas_semanales["nombre"] + " (" + ventas_semanales["presentacion_g"].astype(str) + "g)"
        
        # Mostrar tabla
        st.dataframe(
            ventas_semanales[["año_iso", "semana_iso", "producto", "unidades_total"]],
            column_config={
                "año_iso": st.column_config.NumberColumn("Año"),
                "semana_iso": st.column_config.NumberColumn("Semana ISO"),
                "producto": st.column_config.TextColumn("Producto"),
                "unidades_total": st.column_config.NumberColumn("Unidades Totales"),
            },
            hide_index=True,
        )
        
        # Gráfico de ventas semanales
        st.subheader("Gráfico de Ventas Semanales")
        
        # Preparar datos para el gráfico
        pivot_df = ventas_semanales.pivot_table(
            index=["año_iso", "semana_iso"],
            columns="producto",
            values="unidades_total",
            aggfunc="sum"
        ).fillna(0).reset_index()
        
        # Crear etiquetas para el eje X
        pivot_df["periodo"] = pivot_df["año_iso"].astype(str) + "-S" + pivot_df["semana_iso"].astype(str).str.zfill(2)
        
        # Mostrar gráfico
        st.line_chart(pivot_df.set_index("periodo").drop(columns=["año_iso", "semana_iso"]))
        
        # Opción para exportar a CSV
        csv = pivot_df.to_csv(index=False)
        st.download_button(
            label="Descargar datos en CSV",
            data=csv,
            file_name="ventas_semanales.csv",
            mime="text/csv",
        )
    else:
        st.info("No hay datos de ventas semanales disponibles.")

with tab3:
    st.subheader("Filtrar Ventas")
    
    col1, col2 = st.columns(2)
    
    with col1:
        sku_filter = st.selectbox(
            "Filtrar por Producto",
            options=[None] + skus_df["id"].tolist() if not skus_df.empty else [None],
            format_func=lambda x: "Todos los productos" if x is None else f"{skus_df[skus_df['id'] == x]['nombre'].iloc[0]} ({skus_df[skus_df['id'] == x]['presentacion_g'].iloc[0]}g)" if not skus_df.empty else "",
        )
    
    with col2:
        date_range = st.date_input(
            "Rango de Fechas",
            value=(datetime.now().date() - timedelta(days=30), datetime.now().date()),
            max_value=datetime.now().date()
        )
        
        if len(date_range) == 2:
            fecha_inicio, fecha_fin = date_range
        else:
            fecha_inicio = fecha_fin = None
    
    if st.button("Aplicar Filtros"):
        filtros = {
            "sku_id": sku_filter,
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin
        }
        
        ventas_filtradas = load_ventas(filtros=filtros)
        
        if not ventas_filtradas.empty:
            # Preparar datos para mostrar
            if not skus_df.empty:
                ventas_filtradas = ventas_filtradas.merge(
                    skus_df[["id", "nombre", "presentacion_g"]],
                    left_on="sku_id",
                    right_on="id",
                    suffixes=("", "_sku")
                )
                ventas_filtradas["producto"] = ventas_filtradas["nombre"] + " (" + ventas_filtradas["presentacion_g"].astype(str) + "g)"
            
            # Mostrar resultados
            st.subheader("Resultados de la Búsqueda")
            st.dataframe(
                ventas_filtradas[["id", "producto", "fecha", "semana_iso", "año_iso", "unidades"]],
                hide_index=True
            )
            
            # Resumen de resultados
            st.metric("Total de Ventas Encontradas", len(ventas_filtradas))
            st.metric("Total de Unidades", ventas_filtradas["unidades"].sum())
            
            # Opción para exportar a CSV
            csv = ventas_filtradas.to_csv(index=False)
            st.download_button(
                label="Descargar resultados en CSV",
                data=csv,
                file_name="ventas_filtradas.csv",
                mime="text/csv",
            )
        else:
            st.info("No se encontraron ventas con los filtros aplicados.")
