"""
═══════════════════════════════════════════════════════════════════════
PÁGINA: EXPLORADOR DE DATOS
═══════════════════════════════════════════════════════════════════════
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path

# Agregar utils al path
sys.path.append(str(Path(__file__).parent.parent))

from config import PAGE_CONFIG
from utils.db_connection import get_engine, execute_query
from utils.queries import QUERY_PROVINCIAS, QUERY_FILTRO_PROVINCIA

# ═══════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════════════

st.set_page_config(**PAGE_CONFIG)

st.title("Explorador de Datos")
st.markdown("Filtra y descarga datos por provincia")

st.markdown("---")

# Obtener conexión
engine = get_engine()

if not engine:
    st.error("No se pudo conectar a la base de datos")
    st.stop()

# ═══════════════════════════════════════════════════════════════════════
# FILTROS
# ═══════════════════════════════════════════════════════════════════════

st.sidebar.markdown("### Filtros")

# Obtener lista de provincias
df_provincias = execute_query(engine, QUERY_PROVINCIAS)

if not df_provincias.empty:
    provincias_list = ['Todas'] + sorted(df_provincias['nombre_provincia'].tolist())
    
    provincia_seleccionada = st.sidebar.selectbox(
        "Provincia",
        provincias_list
    )
else:
    provincia_seleccionada = 'Todas'

# Filtros adicionales
st.sidebar.markdown("---")

filtro_petroleo = st.sidebar.checkbox("Solo con petróleo", value=False)
filtro_afro = st.sidebar.slider("% Mínimo Población Afro", 0.0, 100.0, 0.0, 1.0)
filtro_salud = st.sidebar.slider("Salud Mínima (estab/10k)", 0.0, 50.0, 0.0, 1.0)

# ═══════════════════════════════════════════════════════════════════════
# DATOS FILTRADOS
# ═══════════════════════════════════════════════════════════════════════

st.markdown("### Datos Filtrados")

# Cargar datos
if provincia_seleccionada != 'Todas':
    df_datos = execute_query(engine, QUERY_FILTRO_PROVINCIA, params={'provincia': provincia_seleccionada})
else:
    query_completa = """
    SELECT 
        nombre_parroquia,
        nombre_canton,
        nombre_provincia,
        COALESCE(num_infraestructura_petrolera, 0) as infraestructura,
        COALESCE(num_pozos, 0) as pozos,
        COALESCE(num_sitios_contaminados, 0) as contaminacion,
        COALESCE(establecimientos_por_10k_hab, 0) as salud_10k,
        COALESCE(pct_poblacion_afro, 0) as pct_afro,
        COALESCE(poblacion_total, 0) as poblacion
    FROM parroquias;
    """
    df_datos = execute_query(engine, query_completa)

# Aplicar filtros
if not df_datos.empty:
    df_filtrado = df_datos.copy()
    
    if filtro_petroleo:
        df_filtrado = df_filtrado[df_filtrado['infraestructura'] > 0]
    
    if filtro_afro > 0:
        df_filtrado = df_filtrado[df_filtrado['pct_afro'] >= filtro_afro]
    
    if filtro_salud > 0:
        df_filtrado = df_filtrado[df_filtrado['salud_10k'] >= filtro_salud]
    
    # Mostrar métricas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Parroquias", f"{len(df_filtrado):,}")
    
    with col2:
        total_infra = df_filtrado['infraestructura'].sum()
        st.metric("Infraestructura Total", f"{total_infra:,.0f}")
    
    with col3:
        salud_promedio = df_filtrado['salud_10k'].mean()
        st.metric("Salud Promedio", f"{salud_promedio:.2f}")
    
    with col4:
        poblacion_total = df_filtrado['poblacion'].sum()
        st.metric("Población Total", f"{poblacion_total:,.0f}")
    
    st.markdown("---")
    
    # Tabla de datos
    st.markdown("### Tabla de Datos")
    
    # Preparar columnas
    df_display = df_filtrado[[
        'nombre_parroquia',
        'nombre_canton',
        'nombre_provincia',
        'infraestructura',
        'pozos',
        'contaminacion',
        'salud_10k',
        'pct_afro',
        'poblacion'
    ]].copy()
    
    df_display.columns = [
        'Parroquia',
        'Cantón',
        'Provincia',
        'Infraestructura',
        'Pozos',
        'Contaminación',
        'Salud (10k hab)',
        '% Afro',
        'Población'
    ]
    
    # Ordenar por infraestructura
    df_display = df_display.sort_values('Infraestructura', ascending=False)
    
    # Mostrar tabla
    st.dataframe(df_display, use_container_width=True, hide_index=True, height=400)
    
    # Botón de descarga
    csv = df_display.to_csv(index=False).encode('utf-8')
    
    st.download_button(
        label="Descargar CSV",
        data=csv,
        file_name=f"datos_{provincia_seleccionada}.csv",
        mime="text/csv"
    )

else:
    st.warning("No hay datos disponibles con los filtros seleccionados")

st.markdown("---")

# Estadísticas descriptivas
if not df_filtrado.empty:
    st.markdown("### Estadísticas Descriptivas")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Estadísticas básicas
        stats = df_filtrado[['infraestructura', 'salud_10k', 'pct_afro', 'poblacion']].describe().T
        stats = stats[['mean', 'std', 'min', 'max']]
        stats.columns = ['Promedio', 'Desv. Estándar', 'Mínimo', 'Máximo']
        stats = stats.round(2)
        
        st.dataframe(stats, use_container_width=True)
    
    with col2:
        # Conteos
        st.markdown("**Conteos**")
        
        con_petroleo = len(df_filtrado[df_filtrado['infraestructura'] > 0])
        st.metric("Con Petróleo", f"{con_petroleo:,}")
        
        con_afro = len(df_filtrado[df_filtrado['pct_afro'] > 5])
        st.metric("Con >5% Población Afro", f"{con_afro:,}")
        
        sin_salud = len(df_filtrado[df_filtrado['salud_10k'] == 0])
        st.metric("Sin Acceso a Salud", f"{sin_salud:,}")

st.markdown("---")
st.caption("TFM - Máster en Análisis de Datos Masivos | 2025")

