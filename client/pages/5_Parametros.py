import streamlit as st
import pandas as pd
from services.api_client import APIClient
from components.tables import create_editable_table
from components.forms import create_form

# Inicializar cliente API
api_client = APIClient()

# Configuración de la página
st.set_page_config(page_title="Parámetros - Café de Altura", page_icon="☕")

# Título de la página
st.title("⚙️ Configuración de Parámetros")

# Función para cargar parámetros
@st.cache_data(ttl=60)
def load_parametros():
    response = api_client.get("/parametros")
    if isinstance(response, list):
        return pd.DataFrame(response)
    return pd.DataFrame()

# Función para cargar SKUs
@st.cache_data(ttl=300)
def load_skus():
    response = api_client.get("/skus")
    if isinstance(response, list):
        return pd.DataFrame(response)
    return pd.DataFrame()

# Cargar datos
parametros_df = load_parametros()
skus_df = load_skus()

# Crear pestañas
tab1, tab2 = st.tabs(["Parámetros Generales", "Gestión de SKUs"])

with tab1:
    st.subheader("Parámetros del Sistema")
    
    if not parametros_df.empty:
        # Crear tabla editable
        edited_df = create_editable_table(
            parametros_df,
            key="parametros_table",
            column_config={
                "nombre": st.column_config.TextColumn("Nombre", disabled=True),
                "valor": st.column_config.TextColumn("Valor"),
                "descripcion": st.column_config.TextColumn("Descripción", disabled=True),
            },
            hide_index=True,
        )
        
        # Detectar cambios y actualizar
        if st.session_state.get("parametros_table_edited", False):
            for idx, row in edited_df.iterrows():
                original_row = parametros_df.loc[idx]
                if row["valor"] != original_row["valor"]:
                    # Preparar datos para actualización
                    updated_data = {
                        "nombre": row["nombre"],
                        "valor": row["valor"]
                    }
                    
                    # Enviar actualización a la API
                    response = api_client.put(f"/parametros/{row['nombre']}", json=updated_data)
                    
                    if response.get("success", False):
                        st.success(f"Parámetro '{row['nombre']}' actualizado correctamente")
                    else:
                        st.error(f"Error al actualizar el parámetro: {response.get('detail', 'Error desconocido')}")
            
            # Resetear flag de edición
            st.session_state["parametros_table_edited"] = False
            # Invalidar caché
            load_parametros.clear()
    else:
        st.info("No hay parámetros disponibles.")
    
    # Información adicional
    st.info("""
    **Nota sobre los parámetros:**
    - **nivel_servicio**: Afecta el cálculo del stock de seguridad (valor entre 0 y 1).
    - **capacidad_semanal**: Límite de kg de café verde que se pueden procesar por semana.
    - **dias_inventario_objetivo**: Objetivo de días de inventario para el KPI.
    - **objetivo_cumplimiento_plan**: Objetivo de cumplimiento del plan para el KPI (valor entre 0 y 1).
    - **objetivo_otd**: Objetivo de On-Time Delivery para el KPI (valor entre 0 y 1).
    - **objetivo_rechazos**: Objetivo de tasa de rechazos para el KPI (valor entre 0 y 1).
    """)

with tab2:
    st.subheader("Gestión de SKUs")
    
    # Formulario para nuevo SKU
    with st.form("nuevo_sku_form"):
        st.write("### Registrar Nuevo SKU")
        
        col1, col2 = st.columns(2)
        
        with col1:
            nombre = st.text_input("Nombre del Producto")
        
        with col2:
            presentacion_g = st.number_input("Presentación (gramos)", min_value=1, value=250)
        
        submit_button = st.form_submit_button("Registrar SKU")
        
        if submit_button:
            if nombre and presentacion_g:
                nuevo_sku = {
                    "nombre": nombre,
                    "presentacion_g": int(presentacion_g)
                }
                
                response = api_client.post("/skus", json=nuevo_sku)
                
                if "id" in response:
                    st.success(f"SKU registrado correctamente con ID: {response['id']}")
                    # Invalidar caché
                    load_skus.clear()
                else:
                    st.error(f"Error al registrar el SKU: {response.get('detail', 'Error desconocido')}")
            else:
                st.warning("Por favor complete todos los campos.")
    
    # Mostrar SKUs existentes
    st.write("### SKUs Existentes")
    
    if not skus_df.empty:
        # Crear tabla editable
        edited_skus_df = create_editable_table(
            skus_df,
            key="skus_table",
            column_config={
                "id": st.column_config.NumberColumn("ID", disabled=True),
                "nombre": st.column_config.TextColumn("Nombre"),
                "presentacion_g": st.column_config.NumberColumn("Presentación (g)", min_value=1),
                "activo": st.column_config.CheckboxColumn("Activo"),
            },
            hide_index=True,
        )
        
        # Detectar cambios y actualizar
        if st.session_state.get("skus_table_edited", False):
            for idx, row in edited_skus_df.iterrows():
                original_row = skus_df.loc[idx]
                if (row["nombre"] != original_row["nombre"] or 
                    row["presentacion_g"] != original_row["presentacion_g"] or
                    row["activo"] != original_row["activo"]):
                    
                    # Preparar datos para actualización
                    updated_data = {
                        "nombre": row["nombre"],
                        "presentacion_g": int(row["presentacion_g"]),
                        "activo": bool(row["activo"])
                    }
                    
                    # Enviar actualización a la API
                    response = api_client.put(f"/skus/{row['id']}", json=updated_data)
                    
                    if "id" in response:
                        st.success(f"SKU ID {row['id']} actualizado correctamente")
                    else:
                        st.error(f"Error al actualizar el SKU: {response.get('detail', 'Error desconocido')}")
            
            # Resetear flag de edición
            st.session_state["skus_table_edited"] = False
            # Invalidar caché
            load_skus.clear()
        
        # Botón para eliminar SKUs seleccionados
        selected_skus = st.multiselect(
            "Seleccionar SKUs para eliminar",
            options=skus_df["id"].tolist(),
            format_func=lambda x: f"ID: {x} - {skus_df[skus_df['id'] == x]['nombre'].iloc[0]} ({skus_df[skus_df['id'] == x]['presentacion_g'].iloc[0]}g)"
        )
        
        if selected_skus:
            if st.button("Eliminar SKUs Seleccionados"):
                for sku_id in selected_skus:
                    response = api_client.delete(f"/skus/{sku_id}")
                    if response.get("success", False):
                        st.success(f"SKU ID {sku_id} eliminado correctamente")
                    else:
                        st.error(f"Error al eliminar el SKU ID {sku_id}: {response.get('detail', 'Error desconocido')}")
                
                # Invalidar caché
                load_skus.clear()
                st.experimental_rerun()
    else:
        st.info("No hay SKUs registrados. Utilice el formulario para registrar nuevos SKUs.")
