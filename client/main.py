import streamlit as st
from services.api_client import APIClient

# Configuración de la página
st.set_page_config(
    page_title="Café de Altura - Sistema de Planificación",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inicializar cliente API
api_client = APIClient()

# Título principal
st.title("☕ Café de Altura")
st.subheader("Sistema de Planificación de Producción")

# Información de bienvenida
st.markdown("""
Este sistema permite gestionar la planificación de producción para Café de Altura.
Utilice el menú lateral para navegar entre las diferentes secciones.
""")

# Mostrar estado de conexión con el backend
try:
    health = api_client.get("/health")
    if health.get("status") == "ok":
        st.success("✅ Conexión con el servidor establecida")
    else:
        st.warning("⚠️ El servidor está respondiendo pero puede haber problemas")
except Exception:
    st.error("❌ No se pudo conectar con el servidor. Verifique que esté en ejecución.")

# Información sobre las secciones
st.markdown("""
### Secciones disponibles:

1. **Ventas**: Registro y gestión de ventas por SKU y semana.
2. **Producción**: Registro de lotes de producción y cálculo de scrap.
3. **MPS**: Plan Maestro de Producción con proyección a 6 semanas.
4. **Dashboard**: Indicadores clave de desempeño (KPIs).
5. **Parámetros**: Configuración de parámetros del sistema.
""")

# Nota: La navegación se maneja automáticamente por Streamlit a través de la carpeta pages/
