"""
═══════════════════════════════════════════════════════════════════════
DASHBOARD PRINCIPAL - PARADOJA EXTRACTIVISTA EN ECUADOR
═══════════════════════════════════════════════════════════════════════

TFM - Máster en Análisis de Datos Masivos
Autor: [Tu Nombre]
Año: 2025

Análisis geoespacial de la relación entre infraestructura petrolera,
acceso a salud y población afroecuatoriana en Ecuador.
"""

import streamlit as st
import sys
from pathlib import Path

# Agregar utils al path
sys.path.append(str(Path(__file__).parent))

from config import PAGE_CONFIG, MENSAJES, COLORS, METRICAS_CLAVE
from utils.db_connection import get_engine, execute_query, test_connection
from utils.queries import QUERY_METRICAS_GENERALES

# ═══════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE LA PÁGINA
# ═══════════════════════════════════════════════════════════════════════

st.set_page_config(**PAGE_CONFIG)

# ═══════════════════════════════════════════════════════════════════════
# ESTILOS CSS PERSONALIZADOS
# ═══════════════════════════════════════════════════════════════════════

st.markdown("""
<style>
    /* Estilo minimalista profesional */
    [data-testid="stMetricValue"] {
        font-size: 1.8rem;
        font-weight: 600;
        color: #ffffff !important;
    }
    
    [data-testid="stMetricLabel"] {
        color: #e5e7eb !important;
    }
    
    [data-testid="stMetricDelta"] {
        color: #d1d5db !important;
    }
    
    h1 {
        color: #111827;
        font-weight: 700;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #e5e7eb;
    }
    
    h2 {
        color: #374151;
        font-weight: 600;
        margin-top: 2rem;
    }
    
    h3 {
        color: #4b5563;
        font-weight: 600;
    }
    
    .stAlert {
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════
# SIDEBAR - NAVEGACIÓN E INFORMACIÓN
# ═══════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("### Análisis Geoespacial")
    st.markdown("Ecuador 2020-2022")
    st.markdown("---")
    
    st.markdown("**Navegación**")
    st.caption("Usa el menú superior para explorar las secciones del análisis.")
    
    st.markdown("---")
    
    # Test de conexión
    with st.expander("Estado de Conexión"):
        if st.button("Probar Conexión"):
            test_connection()
    
    st.markdown("---")
    
    st.caption("TFM - Máster en Visual Analytics and Big Data")
    st.caption("2025")

# ═══════════════════════════════════════════════════════════════════════
# CONTENIDO PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════

# Título principal
st.title("Paradoja Extractivista en Ecuador")
st.markdown("Análisis Geoespacial: Infraestructura Petrolera, Acceso a Salud y Población Afroecuatoriana")

st.markdown("---")

# Hallazgo principal
st.markdown("### Hallazgo Principal")

col1, col2 = st.columns(2)

with col1:
    st.info("**Paradoja Extractivista**: Las parroquias con actividad petrolera tienen 33% menos acceso a servicios de salud (5.87 vs 8.88 establecimientos/10k hab).")

with col2:
    st.success("**Hallazgo Inesperado**: Las comunidades afroecuatorianas (Esmeraldas) NO están expuestas a actividad petrolera significativa.")

st.markdown("---")

st.markdown("### Métricas Clave")

# Obtener métricas de la base de datos
engine = get_engine()

if engine:
    df_metricas = execute_query(engine, QUERY_METRICAS_GENERALES)
    
    if not df_metricas.empty:
        metricas = df_metricas.iloc[0]
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="Total Parroquias",
                value=f"{int(metricas['total_parroquias']):,}"
            )
        
        with col2:
            st.metric(
                label="Parroquias con Petróleo",
                value=f"{int(metricas['parroquias_con_petroleo']):,}",
                delta=f"{int(metricas['parroquias_con_petroleo'])/int(metricas['total_parroquias'])*100:.1f}%"
            )
        
        with col3:
            st.metric(
                label="Pozos Petroleros",
                value=f"{int(metricas['total_pozos']):,}"
            )
        
        with col4:
            st.metric(
                label="Sitios Contaminados",
                value=f"{int(metricas['total_sitios_contaminados']):,}"
            )
        
        st.markdown("---")
        
        # Comparación de salud
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                label="Salud SIN Petróleo",
                value=f"{metricas['salud_sin_petroleo']:.2f}",
                help="Establecimientos/10k hab"
            )
        
        with col2:
            st.metric(
                label="Salud CON Petróleo",
                value=f"{metricas['salud_con_petroleo']:.2f}",
                delta=f"{(metricas['salud_con_petroleo'] - metricas['salud_sin_petroleo']) / metricas['salud_sin_petroleo'] * 100:.1f}%",
                delta_color="inverse",
                help="Establecimientos/10k hab"
            )
        
        with col3:
            diferencia = ((metricas['salud_con_petroleo'] - metricas['salud_sin_petroleo']) / metricas['salud_sin_petroleo'] * 100)
            st.metric(
                label="Diferencia",
                value=f"{abs(diferencia):.1f}%",
                delta="menos acceso",
                delta_color="inverse"
            )

else:
    st.error("❌ No se pudo conectar a la base de datos. Verifica la configuración.")

st.markdown("---")

st.markdown("---")

# Contexto
with st.expander("Metodología y Fuentes de Datos"):
    st.markdown("""
    **Fuentes de Datos:**
    - CONALI: Límites parroquiales (1,236 parroquias)
    - INEC: Censo de población y etnia (2022)
    - MSP: Registro de establecimientos de salud (RAS 2020)
    - MAATE: Infraestructura petrolera y contaminación
    
    **Métodos:**
    - Proceso ETL (7 notebooks)
    - Spatial joins con PostGIS
    - Clustering (K-Means)
    - Análisis estadístico (correlaciones, pruebas no paramétricas)
    """)

st.markdown("---")
st.caption("TFM - Máster en Visual Analytics and Big Data | 2025")

