import streamlit as st

def create_form(title, fields, submit_label="Guardar", key=None):
    """
    Crea un formulario genérico.
    
    Args:
        title: Título del formulario
        fields: Lista de diccionarios con configuración de campos
        submit_label: Etiqueta del botón de envío
        key: Clave única para el formulario
    
    Returns:
        Diccionario con los valores del formulario si se envió, None en caso contrario
    """
    form_key = key or f"form_{title.lower().replace(' ', '_')}"
    
    with st.form(form_key):
        st.write(f"### {title}")
        
        # Valores del formulario
        values = {}
        
        # Crear campos
        for field in fields:
            field_type = field.get("type", "text")
            field_key = field.get("key")
            field_label = field.get("label", field_key)
            field_options = field.get("options", {})
            
            if field_type == "text":
                values[field_key] = st.text_input(field_label, **field_options)
            elif field_type == "number":
                values[field_key] = st.number_input(field_label, **field_options)
            elif field_type == "date":
                values[field_key] = st.date_input(field_label, **field_options)
            elif field_type == "select":
                values[field_key] = st.selectbox(field_label, **field_options)
            elif field_type == "multiselect":
                values[field_key] = st.multiselect(field_label, **field_options)
            elif field_type == "checkbox":
                values[field_key] = st.checkbox(field_label, **field_options)
            elif field_type == "radio":
                values[field_key] = st.radio(field_label, **field_options)
            elif field_type == "slider":
                values[field_key] = st.slider(field_label, **field_options)
            elif field_type == "textarea":
                values[field_key] = st.text_area(field_label, **field_options)
        
        # Botón de envío
        submitted = st.form_submit_button(submit_label)
        
        if submitted:
            return values
        
        return None
