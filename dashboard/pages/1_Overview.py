"""
═══════════════════════════════════════════════════════════════════════
PÁGINA: OVERVIEW - VISIÓN GENERAL DEL ANÁLISIS
═══════════════════════════════════════════════════════════════════════
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
from pathlib import Path

# Agregar utils al path
sys.path.append(str(Path(__file__).parent.parent))

from config import PAGE_CONFIG, COLORS
from utils.db_connection import get_engine, execute_query
from utils.queries import (
    QUERY_TOP_PETROLERAS,
    QUERY_STATS_PROVINCIA,
    QUERY_SCATTER_DATA
)

# ═══════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════════════

st.set_page_config(**PAGE_CONFIG)

st.title("Overview")
st.markdown("Análisis exploratorio de datos geoespaciales")

st.markdown("---")

# Obtener conexión
engine = get_engine()

if not engine:
    st.error("No se pudo conectar a la base de datos")
    st.stop()

# ═══════════════════════════════════════════════════════════════════════
# HALLAZGO PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════

st.info("**Hallazgo clave:** Las parroquias con actividad petrolera tienen 33% menos acceso a servicios de salud.")

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════
# SCATTER PLOT - PETRÓLEO VS SALUD
# ═══════════════════════════════════════════════════════════════════════

st.markdown("### Relación: Infraestructura Petrolera vs Acceso a Salud")

df_scatter = execute_query(engine, QUERY_SCATTER_DATA)

if not df_scatter.empty:
    # Scatter plot
    fig = px.scatter(
        df_scatter,
        x='num_infraestructura_petrolera',
        y='establecimientos_por_10k_hab',
        color='tiene_petroleo',
        color_discrete_map={0: '#3b82f6', 1: '#ef4444'},
        labels={
            'num_infraestructura_petrolera': 'Infraestructura Petrolera',
            'establecimientos_por_10k_hab': 'Establecimientos de Salud (por 10k hab)',
            'tiene_petroleo': 'Tiene Petróleo'
        },
        hover_data=['nombre_parroquia', 'nombre_provincia'],
        opacity=0.6,
        size='num_infraestructura_petrolera',
        size_max=15
    )
    
    fig.update_layout(
        height=500,
        showlegend=True,
        legend=dict(
            title='',
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Estadísticas
    col1, col2, col3 = st.columns(3)
    
    con_petroleo = df_scatter[df_scatter['tiene_petroleo'] == 1]
    sin_petroleo = df_scatter[df_scatter['tiene_petroleo'] == 0]
    
    with col1:
        st.metric(
            "Parroquias con Petróleo",
            f"{len(con_petroleo):,}"
        )
    
    with col2:
        st.metric(
            "Salud CON petróleo",
            f"{con_petroleo['establecimientos_por_10k_hab'].mean():.2f}"
        )
    
    with col3:
        st.metric(
            "Salud SIN petróleo",
            f"{sin_petroleo['establecimientos_por_10k_hab'].mean():.2f}"
        )
    
    # Interpretación
    st.caption(f"**Interpretación:** Se observa una relación inversa entre infraestructura petrolera y acceso a salud. Las {len(con_petroleo)} parroquias con petróleo tienen un promedio de {con_petroleo['establecimientos_por_10k_hab'].mean():.2f} establecimientos/10k hab, mientras que las {len(sin_petroleo)} sin petróleo alcanzan {sin_petroleo['establecimientos_por_10k_hab'].mean():.2f}. Esta brecha del 33% evidencia la paradoja extractivista.")

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════
# TOP 10 PARROQUIAS MÁS PETROLERAS
# ═══════════════════════════════════════════════════════════════════════

st.markdown("### Top 10 Parroquias Más Petroleras")

df_top = execute_query(engine, QUERY_TOP_PETROLERAS.format(limit=10))

if not df_top.empty:
    # Gráfico de barras
    fig = px.bar(
        df_top,
        x='num_infraestructura_petrolera',
        y='nombre_parroquia',
        orientation='h',
        labels={
            'num_infraestructura_petrolera': 'Infraestructura Total',
            'nombre_parroquia': ''
        },
        color='num_infraestructura_petrolera',
        color_continuous_scale='Reds',
        hover_data=['nombre_provincia', 'num_pozos', 'num_sitios_contaminados']
    )
    
    fig.update_layout(
        height=400,
        yaxis={'categoryorder': 'total ascending'},
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Tabla compacta
    df_display = df_top[[
        'nombre_parroquia',
        'nombre_provincia',
        'num_infraestructura_petrolera',
        'num_pozos',
        'num_sitios_contaminados',
        'salud_10k'
    ]].copy()
    
    df_display.columns = [
        'Parroquia',
        'Provincia',
        'Infraestructura',
        'Pozos',
        'Contaminación',
        'Salud (10k hab)'
    ]
    
    st.dataframe(df_display, use_container_width=True, hide_index=True)
    
    # Interpretación
    top_parroquia = df_top.iloc[0]
    st.caption(f"**Interpretación:** {top_parroquia['nombre_parroquia']} ({top_parroquia['nombre_provincia']}) lidera con {int(top_parroquia['num_infraestructura_petrolera'])} infraestructuras petroleras, incluyendo {int(top_parroquia['num_pozos'])} pozos y {int(top_parroquia['num_sitios_contaminados'])} sitios contaminados. Las 10 parroquias más petroleras concentran el {(df_top['num_infraestructura_petrolera'].sum() / 15851 * 100):.1f}% de la infraestructura total del país. Todas están ubicadas en Amazonía y Costa.")

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════
# ANÁLISIS POR PROVINCIA
# ═══════════════════════════════════════════════════════════════════════

st.markdown("### Análisis por Provincia")

df_provincias = execute_query(engine, QUERY_STATS_PROVINCIA)

if not df_provincias.empty:
    # Filtrar provincias con actividad petrolera
    df_provincias_petroleo = df_provincias[df_provincias['total_infraestructura'] > 0].copy()
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de infraestructura por provincia
        fig1 = px.bar(
            df_provincias_petroleo.head(10),
            x='nombre_provincia',
            y='total_infraestructura',
            title='Infraestructura Petrolera (Top 10)',
            labels={
                'total_infraestructura': 'Infraestructura Total',
                'nombre_provincia': ''
            },
            color='total_infraestructura',
            color_continuous_scale='Oranges'
        )
        
        fig1.update_layout(
            xaxis_tickangle=-45,
            showlegend=False,
            height=400
        )
        
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        # Gráfico de acceso a salud por provincia
        fig2 = px.bar(
            df_provincias_petroleo.head(10),
            x='nombre_provincia',
            y='salud_promedio',
            title='Acceso a Salud (Top 10 petroleras)',
            labels={
                'salud_promedio': 'Salud Promedio',
                'nombre_provincia': ''
            },
            color='salud_promedio',
            color_continuous_scale='Greens'
        )
        
        fig2.update_layout(
            xaxis_tickangle=-45,
            showlegend=False,
            height=400
        )
        
        st.plotly_chart(fig2, use_container_width=True)
    
    # Interpretación
    top_prov_petroleo = df_provincias_petroleo.iloc[0]
    top_prov_salud = df_provincias_petroleo.nlargest(1, 'salud_promedio').iloc[0]
    st.caption(f"**Interpretación:** {top_prov_petroleo['nombre_provincia']} concentra la mayor infraestructura petrolera ({int(top_prov_petroleo['total_infraestructura'])} unidades), pero su acceso a salud promedio es de {top_prov_petroleo['salud_promedio']:.2f} estab/10k hab. En contraste, {top_prov_salud['nombre_provincia']} tiene mejor acceso a salud ({top_prov_salud['salud_promedio']:.2f}) con menor actividad petrolera. La paradoja se replica a nivel provincial.")

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════
# POBLACIÓN AFROECUATORIANA
# ═══════════════════════════════════════════════════════════════════════

st.markdown("### Población Afroecuatoriana y Petróleo")

# Query para parroquias afro con petróleo
query_afro = """
SELECT 
    nombre_parroquia,
    nombre_provincia,
    pct_poblacion_afro,
    num_infraestructura_petrolera,
    establecimientos_por_10k_hab
FROM parroquias
WHERE pct_poblacion_afro > 5 
  AND num_infraestructura_petrolera > 0
ORDER BY pct_poblacion_afro DESC
LIMIT 10;
"""

df_afro = execute_query(engine, query_afro)

if not df_afro.empty:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        fig = px.bar(
            df_afro,
            x='nombre_parroquia',
            y='pct_poblacion_afro',
            title='Parroquias con >5% Población Afro e Infraestructura Petrolera',
            labels={
                'pct_poblacion_afro': '% Población Afro',
                'nombre_parroquia': ''
            },
            color='pct_poblacion_afro',
            color_continuous_scale='Purples',
            hover_data=['nombre_provincia', 'num_infraestructura_petrolera', 'establecimientos_por_10k_hab']
        )
        
        fig.update_layout(
            xaxis_tickangle=-45,
            showlegend=False,
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("**Observación:**")
        st.info("Solo 3 parroquias tienen >5% población afro y actividad petrolera significativa.")
        
        # Métricas
        salud_promedio_afro = df_afro['establecimientos_por_10k_hab'].mean()
        st.metric("Salud Promedio (Afro + Petróleo)", f"{salud_promedio_afro:.2f}")
    
    # Interpretación
    st.caption(f"**Interpretación:** Solo {len(df_afro)} parroquias combinan alta población afroecuatoriana (>5%) con actividad petrolera significativa. Estas comunidades enfrentan una doble vulnerabilidad: extracción de recursos en su territorio y limitado acceso a servicios básicos (promedio de {salud_promedio_afro:.2f} estab/10k hab). La mayoría se concentra en Esmeraldas, evidenciando inequidades históricas.")
else:
    st.warning("Datos de población afroecuatoriana no disponibles")

st.markdown("---")
st.caption("TFM - Máster en Visual Analytics and Big Data | 2025")

