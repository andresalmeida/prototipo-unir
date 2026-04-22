"""
═══════════════════════════════════════════════════════════════════════
CARGA DE DATOS DESDE CSV (MODO FALLBACK SIN BASE DE DATOS)
═══════════════════════════════════════════════════════════════════════
Simula las queries SQL usando pandas sobre los CSVs procesados.
"""

import pandas as pd
import streamlit as st
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "processed"
CSV_PARROQUIAS = DATA_DIR / "parroquias_con_clusters.csv"


@st.cache_data
def load_parroquias() -> pd.DataFrame:
    df = pd.read_csv(CSV_PARROQUIAS)
    numeric_cols = [
        'num_infraestructura_petrolera', 'num_pozos', 'num_sitios_contaminados',
        'establecimientos_por_10k_hab', 'pct_poblacion_afro',
        'poblacion_total', 'densidad_petroleo_km2', 'densidad_establecimientos_km2',
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].fillna(0)
    df['tiene_petroleo'] = df['tiene_petroleo'].fillna(0).astype(int)
    return df


def execute_from_csv(query: str, params: dict = None) -> pd.DataFrame:
    """
    Recibe un string SQL y lo routea a la función pandas equivalente.
    Se identifica cada query por tokens únicos en el texto.
    """
    df = load_parroquias()
    q = str(query)

    # ── QUERY_METRICAS_GENERALES ──────────────────────────────────────────
    if 'total_parroquias' in q:
        return _metricas_generales(df)

    # ── QUERY_PARADOJA_CRITICA ────────────────────────────────────────────
    if 'num_infraestructura_petrolera > 100' in q:
        limit = _extract_limit(q, default=10)
        return _paradoja_critica(df, limit)

    # ── QUERY_SCATTER_DATA ────────────────────────────────────────────────
    if 'tiene_petroleo' in q and 'GROUP BY' not in q.upper() and 'total_infraestructura' not in q:
        if 'nombre_parroquia' in q and 'DISTINCT' not in q.upper() and '%(provincia)s' not in q and 'nombre_canton' not in q:
            return _scatter_data(df)

    # ── QUERY_STATS_PROVINCIA ─────────────────────────────────────────────
    if 'GROUP BY nombre_provincia' in q or ('total_infraestructura' in q and 'GROUP BY' in q.upper()):
        return _stats_provincia(df)

    # ── QUERY_TOP_PETROLERAS ──────────────────────────────────────────────
    if 'densidad_km2' in q or ('num_infraestructura_petrolera > 0' in q and 'ORDER BY num_infraestructura_petrolera DESC' in q and 'pct_poblacion_afro' not in q):
        limit = _extract_limit(q, default=10)
        return _top_petroleras(df, limit)

    # ── QUERY_PROVINCIAS ──────────────────────────────────────────────────
    if 'DISTINCT nombre_provincia' in q:
        return _provincias(df)

    # ── QUERY_FILTRO_PROVINCIA ────────────────────────────────────────────
    if '%(provincia)s' in q:
        provincia = params.get('provincia') if params else None
        return _filtro_provincia(df, provincia)

    # ── QUERY_TOP_AFRO ────────────────────────────────────────────────────
    if 'ORDER BY pct_poblacion_afro DESC' in q and 'num_infraestructura_petrolera > 0' not in q:
        limit = _extract_limit(q, default=10)
        return _top_afro(df, limit)

    # ── QUERY_AFRO_PETROLEO ───────────────────────────────────────────────
    if 'pct_poblacion_afro > 5' in q and 'num_infraestructura_petrolera > 0' in q:
        limit = _extract_limit(q, default=None)
        return _afro_petroleo(df, limit)

    # ── QUERY_CORRELACION ─────────────────────────────────────────────────
    if 'Con petróleo' in q or ("tiene_petroleo" in q and 'GROUP BY' in q.upper()):
        return _correlacion(df)

    # ── FALLBACK GENÉRICO (SELECT * style) ───────────────────────────────
    return _full_data(df)


# ═══════════════════════════════════════════════════════════════════════
# IMPLEMENTACIONES PANDAS
# ═══════════════════════════════════════════════════════════════════════

def _metricas_generales(df: pd.DataFrame) -> pd.DataFrame:
    valid = df[df['establecimientos_por_10k_hab'].notna()].copy()
    con = valid[valid['tiene_petroleo'] == 1]
    sin = valid[valid['tiene_petroleo'] == 0]
    return pd.DataFrame([{
        'total_parroquias': len(valid),
        'parroquias_con_petroleo': int(valid['tiene_petroleo'].sum()),
        'total_pozos': int(valid['num_pozos'].sum()),
        'total_sitios_contaminados': int(valid['num_sitios_contaminados'].sum()),
        'salud_con_petroleo': round(con['establecimientos_por_10k_hab'].mean(), 2),
        'salud_sin_petroleo': round(sin['establecimientos_por_10k_hab'].mean(), 2),
    }])


def _top_petroleras(df: pd.DataFrame, limit: int = 10) -> pd.DataFrame:
    result = df[df['num_infraestructura_petrolera'] > 0].copy()
    result = result.sort_values('num_infraestructura_petrolera', ascending=False).head(limit)
    result['densidad_km2'] = result['densidad_petroleo_km2'].round(2)
    result['salud_10k'] = result['establecimientos_por_10k_hab'].fillna(0)
    result['poblacion'] = result['poblacion_total'].fillna(0)
    result['pct_afro'] = result['pct_poblacion_afro'].fillna(0)
    return result[[
        'nombre_parroquia', 'nombre_canton', 'nombre_provincia',
        'num_infraestructura_petrolera', 'num_pozos', 'num_sitios_contaminados',
        'densidad_km2', 'salud_10k', 'poblacion', 'pct_afro'
    ]].reset_index(drop=True)


def _paradoja_critica(df: pd.DataFrame, limit: int = 10) -> pd.DataFrame:
    result = df[
        (df['num_infraestructura_petrolera'] > 100) &
        (df['establecimientos_por_10k_hab'] == 0)
    ].copy()
    result = result.sort_values('num_infraestructura_petrolera', ascending=False).head(limit)
    result['salud_10k'] = result['establecimientos_por_10k_hab']
    result['poblacion'] = result['poblacion_total']
    return result[[
        'nombre_parroquia', 'nombre_canton', 'nombre_provincia',
        'num_infraestructura_petrolera', 'num_pozos', 'num_sitios_contaminados',
        'salud_10k', 'poblacion'
    ]].reset_index(drop=True)


def _correlacion(df: pd.DataFrame) -> pd.DataFrame:
    valid = df[df['establecimientos_por_10k_hab'].notna()].copy()
    grupos = []
    for tiene, label in [(1, 'Con petróleo'), (0, 'Sin petróleo')]:
        g = valid[valid['tiene_petroleo'] == tiene]
        grupos.append({
            'categoria': label,
            'num_parroquias': len(g),
            'salud_promedio': round(g['establecimientos_por_10k_hab'].mean(), 2),
            'infra_promedio': round(g['num_infraestructura_petrolera'].mean(), 2),
            'afro_promedio': round(g['pct_poblacion_afro'].mean(), 2),
        })
    return pd.DataFrame(grupos)


def _afro_petroleo(df: pd.DataFrame, limit: int = None) -> pd.DataFrame:
    result = df[
        (df['pct_poblacion_afro'] > 5) &
        (df['num_infraestructura_petrolera'] > 0)
    ].sort_values('pct_poblacion_afro', ascending=False)
    if limit:
        result = result.head(limit)
    return result[[
        'nombre_parroquia', 'nombre_provincia',
        'pct_poblacion_afro', 'num_infraestructura_petrolera',
        'establecimientos_por_10k_hab'
    ]].reset_index(drop=True)


def _top_afro(df: pd.DataFrame, limit: int = 10) -> pd.DataFrame:
    result = df[df['pct_poblacion_afro'] > 0].sort_values('pct_poblacion_afro', ascending=False).head(limit)
    result = result.copy()
    result['infraestructura'] = result['num_infraestructura_petrolera']
    result['salud_10k'] = result['establecimientos_por_10k_hab']
    return result[[
        'nombre_parroquia', 'nombre_provincia',
        'pct_poblacion_afro', 'poblacion_total',
        'infraestructura', 'salud_10k'
    ]].reset_index(drop=True)


def _scatter_data(df: pd.DataFrame) -> pd.DataFrame:
    valid = df[
        df['establecimientos_por_10k_hab'].notna() &
        df['num_infraestructura_petrolera'].notna()
    ].copy()
    return valid[[
        'nombre_parroquia', 'nombre_provincia',
        'num_infraestructura_petrolera', 'establecimientos_por_10k_hab',
        'pct_poblacion_afro', 'tiene_petroleo'
    ]].reset_index(drop=True)


def _provincias(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        sorted(df['nombre_provincia'].dropna().unique()),
        columns=['nombre_provincia']
    )


def _filtro_provincia(df: pd.DataFrame, provincia: str = None) -> pd.DataFrame:
    result = df.copy()
    if provincia:
        result = result[result['nombre_provincia'] == provincia]
    result = result.sort_values('num_infraestructura_petrolera', ascending=False)
    result['infraestructura'] = result['num_infraestructura_petrolera'].fillna(0)
    result['pozos'] = result['num_pozos'].fillna(0)
    result['contaminacion'] = result['num_sitios_contaminados'].fillna(0)
    result['salud_10k'] = result['establecimientos_por_10k_hab'].fillna(0)
    result['pct_afro'] = result['pct_poblacion_afro'].fillna(0)
    result['poblacion'] = result['poblacion_total'].fillna(0)
    return result[[
        'nombre_parroquia', 'nombre_canton', 'nombre_provincia',
        'infraestructura', 'pozos', 'contaminacion',
        'salud_10k', 'pct_afro', 'poblacion'
    ]].reset_index(drop=True)


def _stats_provincia(df: pd.DataFrame) -> pd.DataFrame:
    grouped = df.groupby('nombre_provincia').agg(
        num_parroquias=('nombre_parroquia', 'count'),
        parroquias_petroleras=('tiene_petroleo', 'sum'),
        total_infraestructura=('num_infraestructura_petrolera', 'sum'),
        salud_promedio=('establecimientos_por_10k_hab', 'mean'),
        afro_promedio=('pct_poblacion_afro', 'mean'),
    ).reset_index()
    grouped['salud_promedio'] = grouped['salud_promedio'].round(2)
    grouped['afro_promedio'] = grouped['afro_promedio'].round(2)
    grouped['parroquias_petroleras'] = grouped['parroquias_petroleras'].astype(int)
    return grouped.sort_values('total_infraestructura', ascending=False)


def _full_data(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    result['infraestructura'] = result['num_infraestructura_petrolera'].fillna(0)
    result['pozos'] = result['num_pozos'].fillna(0)
    result['contaminacion'] = result['num_sitios_contaminados'].fillna(0)
    result['salud_10k'] = result['establecimientos_por_10k_hab'].fillna(0)
    result['pct_afro'] = result['pct_poblacion_afro'].fillna(0)
    result['poblacion'] = result['poblacion_total'].fillna(0)
    return result


# ═══════════════════════════════════════════════════════════════════════
# UTILIDADES
# ═══════════════════════════════════════════════════════════════════════

def _extract_limit(query: str, default: int = 10):
    import re
    match = re.search(r'LIMIT\s+(\d+)', query, re.IGNORECASE)
    if match:
        return int(match.group(1))
    # Buscar {limit} ya resuelto como número
    match2 = re.search(r'LIMIT\s+\{(\w+)\}', query)
    if match2:
        return default
    return default
