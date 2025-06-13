import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from services.api_client import APIClient

# Inicializar cliente API
api_client = APIClient()

# Configuración de la página
st.set_page_config(page_title="Dashboard - Café de Altura", page_icon="☕", layout="wide")

# Título de la página
st.title("📊 Dashboard de KPIs")

# Función para cargar KPIs
@st.cache_data(ttl=60)
def load_kpis():
    response = api_client.get("/dashboard/kpis")
    return response

# Función para cargar datos históricos de KPIs
@st.cache_data(ttl=300)
def load_kpis_historicos():
    response = api_client.get("/dashboard/kpis/historico")
    if isinstance(response, list):
        return pd.DataFrame(response)
    return pd.DataFrame()

# Cargar datos
kpis = load_kpis()
kpis_historicos = load_kpis_historicos()

# Mostrar KPIs actuales
if kpis:
    st.subheader("Indicadores Clave de Desempeño (KPIs)")
    
    # Crear columnas para los KPIs
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        dias_inventario = kpis.get("dias_inventario", 0)
        st.metric(
            "Días de Inventario",
            f"{dias_inventario:.1f} días",
            delta=None,
            help="Promedio de días que el inventario actual puede cubrir la demanda"
        )
    
    with col2:
        cumplimiento_plan = kpis.get("cumplimiento_plan", 0) * 100
        st.metric(
            "Cumplimiento del Plan",
            f"{cumplimiento_plan:.1f}%",
            delta=None,
            help="Porcentaje de cumplimiento del plan de producción"
        )
    
    with col3:
        otd = kpis.get("otd", 0) * 100
        st.metric(
            "On-Time Delivery (OTD)",
            f"{otd:.1f}%",
            delta=None,
            help="Porcentaje de entregas a tiempo"
        )
    
    with col4:
        rechazos = kpis.get("rechazos", 0) * 100
        st.metric(
            "Tasa de Rechazos",
            f"{rechazos:.1f}%",
            delta=None,
            delta_color="inverse",
            help="Porcentaje de productos rechazados por control de calidad"
        )

# Mostrar gráficos históricos
if not kpis_historicos.empty:
    st.subheader("Evolución Histórica de KPIs")
    
    # Convertir fechas
    if "fecha" in kpis_historicos.columns:
        kpis_historicos["fecha"] = pd.to_datetime(kpis_historicos["fecha"])
    
    # Crear pestañas para diferentes gráficos
    tab1, tab2, tab3, tab4 = st.tabs(["Días de Inventario", "Cumplimiento del Plan", "OTD", "Rechazos"])
    
    with tab1:
        # Gráfico de días de inventario
        if "dias_inventario" in kpis_historicos.columns:
            fig_inv = px.line(
                kpis_historicos,
                x="fecha",
                y="dias_inventario",
                title="Evolución de Días de Inventario",
                labels={"dias_inventario": "Días", "fecha": "Fecha"},
                markers=True
            )
            
            # Añadir línea objetivo
            objetivo_dias = kpis.get("objetivo_dias_inventario", 15)
            fig_inv.add_hline(
                y=objetivo_dias,
                line_dash="dash",
                line_color="green",
                annotation_text=f"Objetivo: {objetivo_dias} días"
            )
            
            st.plotly_chart(fig_inv, use_container_width=True)
            
            # Estadísticas
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Promedio", f"{kpis_historicos['dias_inventario'].mean():.1f} días")
            with col2:
                st.metric("Mínimo", f"{kpis_historicos['dias_inventario'].min():.1f} días")
            with col3:
                st.metric("Máximo", f"{kpis_historicos['dias_inventario'].max():.1f} días")
    
    with tab2:
        # Gráfico de cumplimiento del plan
        if "cumplimiento_plan" in kpis_historicos.columns:
            # Convertir a porcentaje
            kpis_historicos["cumplimiento_plan_pct"] = kpis_historicos["cumplimiento_plan"] * 100
            
            fig_plan = px.line(
                kpis_historicos,
                x="fecha",
                y="cumplimiento_plan_pct",
                title="Evolución del Cumplimiento del Plan",
                labels={"cumplimiento_plan_pct": "Cumplimiento (%)", "fecha": "Fecha"},
                markers=True
            )
            
            # Añadir línea objetivo
            objetivo_plan = kpis.get("objetivo_cumplimiento_plan", 0.95) * 100
            fig_plan.add_hline(
                y=objetivo_plan,
                line_dash="dash",
                line_color="green",
                annotation_text=f"Objetivo: {objetivo_plan:.0f}%"
            )
            
            st.plotly_chart(fig_plan, use_container_width=True)
            
            # Estadísticas
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Promedio", f"{kpis_historicos['cumplimiento_plan'].mean() * 100:.1f}%")
            with col2:
                st.metric("Mínimo", f"{kpis_historicos['cumplimiento_plan'].min() * 100:.1f}%")
            with col3:
                st.metric("Máximo", f"{kpis_historicos['cumplimiento_plan'].max() * 100:.1f}%")
    
    with tab3:
        # Gráfico de OTD
        if "otd" in kpis_historicos.columns:
            # Convertir a porcentaje
            kpis_historicos["otd_pct"] = kpis_historicos["otd"] * 100
            
            fig_otd = px.line(
                kpis_historicos,
                x="fecha",
                y="otd_pct",
                title="Evolución del On-Time Delivery (OTD)",
                labels={"otd_pct": "OTD (%)", "fecha": "Fecha"},
                markers=True
            )
            
            # Añadir línea objetivo
            objetivo_otd = kpis.get("objetivo_otd", 0.98) * 100
            fig_otd.add_hline(
                y=objetivo_otd,
                line_dash="dash",
                line_color="green",
                annotation_text=f"Objetivo: {objetivo_otd:.0f}%"
            )
            
            st.plotly_chart(fig_otd, use_container_width=True)
            
            # Estadísticas
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Promedio", f"{kpis_historicos['otd'].mean() * 100:.1f}%")
            with col2:
                st.metric("Mínimo", f"{kpis_historicos['otd'].min() * 100:.1f}%")
            with col3:
                st.metric("Máximo", f"{kpis_historicos['otd'].max() * 100:.1f}%")
    
    with tab4:
        # Gráfico de rechazos
        if "rechazos" in kpis_historicos.columns:
            # Convertir a porcentaje
            kpis_historicos["rechazos_pct"] = kpis_historicos["rechazos"] * 100
            
            fig_rechazos = px.line(
                kpis_historicos,
                x="fecha",
                y="rechazos_pct",
                title="Evolución de la Tasa de Rechazos",
                labels={"rechazos_pct": "Rechazos (%)", "fecha": "Fecha"},
                markers=True
            )
            
            # Añadir línea objetivo
            objetivo_rechazos = kpis.get("objetivo_rechazos", 0.02) * 100
            fig_rechazos.add_hline(
                y=objetivo_rechazos,
                line_dash="dash",
                line_color="red",
                annotation_text=f"Objetivo: {objetivo_rechazos:.1f}%"
            )
            
            st.plotly_chart(fig_rechazos, use_container_width=True)
            
            # Estadísticas
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Promedio", f"{kpis_historicos['rechazos'].mean() * 100:.1f}%")
            with col2:
                st.metric("Mínimo", f"{kpis_historicos['rechazos'].min() * 100:.1f}%")
            with col3:
                st.metric("Máximo", f"{kpis_historicos['rechazos'].max() * 100:.1f}%")

    # Gráfico de radar para comparación de KPIs actuales vs objetivos
    st.subheader("Comparación de KPIs Actuales vs Objetivos")
    
    # Preparar datos para el gráfico de radar
    categorias = ["Días Inventario", "Cumplimiento Plan", "OTD", "Rechazos"]
    
    # Valores actuales (normalizados para el gráfico)
    valores_actuales = [
        min(kpis.get("dias_inventario", 0) / kpis.get("objetivo_dias_inventario", 15), 1.5),
        min(kpis.get("cumplimiento_plan", 0) / kpis.get("objetivo_cumplimiento_plan", 0.95), 1.5),
        min(kpis.get("otd", 0) / kpis.get("objetivo_otd", 0.98), 1.5),
        min(kpis.get("rechazos", 0) / kpis.get("objetivo_rechazos", 0.02), 1.5)
    ]
    
    # Valores objetivo (siempre 1.0 en la escala normalizada)
    valores_objetivo = [1.0, 1.0, 1.0, 1.0]
    
    # Crear gráfico de radar
    fig_radar = go.Figure()
    
    fig_radar.add_trace(go.Scatterpolar(
        r=valores_actuales,
        theta=categorias,
        fill='toself',
        name='Actual'
    ))
    
    fig_radar.add_trace(go.Scatterpolar(
        r=valores_objetivo,
        theta=categorias,
        fill='toself',
        name='Objetivo'
    ))
    
    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1.5]
            )
        ),
        showlegend=True
    )
    
    st.plotly_chart(fig_radar, use_container_width=True)

    # Opción para exportar datos
    st.subheader("Exportar Datos")
    
    if not kpis_historicos.empty:
        # Preparar datos para exportar
        export_df = kpis_historicos.copy()
        
        # Convertir decimales a porcentajes para mejor visualización
        if "cumplimiento_plan" in export_df.columns:
            export_df["cumplimiento_plan"] = export_df["cumplimiento_plan"] * 100
        if "otd" in export_df.columns:
            export_df["otd"] = export_df["otd"] * 100
        if "rechazos" in export_df.columns:
            export_df["rechazos"] = export_df["rechazos"] * 100
        
        # Renombrar columnas para mejor comprensión
        export_df = export_df.rename(columns={
            "dias_inventario": "Días de Inventario",
            "cumplimiento_plan": "Cumplimiento del Plan (%)",
            "otd": "OTD (%)",
            "rechazos": "Rechazos (%)",
            "fecha": "Fecha"
        })
        
        # Botón para descargar CSV
        csv = export_df.to_csv(index=False)
        st.download_button(
            label="📥 Descargar Datos en CSV",
            data=csv,
            file_name=f"KPIs_Cafe_de_Altura_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )
else:
    st.info("No hay datos históricos de KPIs disponibles.")
