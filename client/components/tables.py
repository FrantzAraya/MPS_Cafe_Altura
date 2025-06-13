import streamlit as st
import pandas as pd

def create_editable_table(df, key, column_config=None, hide_index=True):
    """
    Crea una tabla editable con detección de cambios.
    
    Args:
        df: DataFrame a mostrar
        key: Clave única para la tabla
        column_config: Configuración de columnas
        hide_index: Si se debe ocultar el índice
    
    Returns:
        DataFrame editado
    """
    # Crear tabla editable
    edited_df = st.data_editor(
        df,
        column_config=column_config,
        hide_index=hide_index,
        key=key
    )
    
    # Detectar cambios
    if not df.equals(edited_df):
        st.session_state[f"{key}_edited"] = True
    
    return edited_df
