"""
═══════════════════════════════════════════════════════════════════════
FUENTE DE DATOS DEL DASHBOARD
═══════════════════════════════════════════════════════════════════════
Lee siempre desde los CSVs procesados en data/processed/.
No requiere PostgreSQL/PostGIS.
"""

import streamlit as st
import pandas as pd
from pathlib import Path


class CSVEngine:
    """Sentinel truthy que indica al resto del código que use CSVs."""
    def __bool__(self):
        return True

    def __repr__(self):
        return "CSVEngine(data/processed)"


@st.cache_resource
def get_engine():
    """Devuelve siempre un CSVEngine: el dashboard usa CSVs procesados."""
    return CSVEngine()


@st.cache_data(ttl=600)
def execute_query(_engine, query, params=None):
    """Ejecuta un 'query' contra los CSVs procesados y retorna un DataFrame."""
    from utils.data_loader import execute_from_csv
    return execute_from_csv(query, params)


@st.cache_data(ttl=600)
def execute_geo_query(_engine, query, geom_col='geometry'):
    """No se usa en modo CSV (los mapas usan scatter_mapbox con lat/lon)."""
    return pd.DataFrame()


def test_connection():
    """Muestra información sobre la fuente de datos del dashboard."""
    from utils.data_loader import load_parroquias

    try:
        df = load_parroquias()
        st.success(f"""
        ✅ **Datos cargados correctamente**
        - Fuente: `data/processed/parroquias_con_clusters.csv`
        - Parroquias: {len(df):,}
        - Provincias: {df['nombre_provincia'].nunique()}
        - Con petróleo: {int(df['tiene_petroleo'].sum()):,}
        """)
        return True
    except Exception as e:
        st.error(f"❌ Error cargando los CSVs procesados: {e}")
        return False

