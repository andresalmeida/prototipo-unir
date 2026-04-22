"""
═══════════════════════════════════════════════════════════════════════
PÁGINA: ANÁLISIS ESPACIAL - MAPAS Y CLUSTERING
═══════════════════════════════════════════════════════════════════════
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
from pathlib import Path

# Agregar utils al path
sys.path.append(str(Path(__file__).parent.parent))

from config import PAGE_CONFIG, COLORS
from utils.db_connection import get_engine, execute_query

# ═══════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════════════

st.set_page_config(**PAGE_CONFIG)

st.title("Análisis Espacial")
st.markdown("Mapas interactivos y clustering geoespacial")

st.markdown("---")

# Obtener conexión
engine = get_engine()

if not engine:
    st.error("No se pudo conectar a la base de datos")
    st.stop()

# ═══════════════════════════════════════════════════════════════════════
# CARGAR DATOS GEOESPACIALES
# ═══════════════════════════════════════════════════════════════════════

@st.cache_data
def load_spatial_data():
    """Carga datos con coordenadas y clusters del notebook 6"""
    # Intentar cargar desde CSV con clusters
    import pandas as pd
    from pathlib import Path
    
    csv_path = Path(__file__).parent.parent.parent / 'data' / 'processed' / 'parroquias_con_clusters.csv'
    
    if csv_path.exists():
        df_csv = pd.read_csv(csv_path)
        # Renombrar solo las que necesitamos para los mapas
        if 'centroide_lon' in df_csv.columns:
            df_csv = df_csv.rename(columns={'centroide_lon': 'lon', 'centroide_lat': 'lat'})
        # Crear alias para facilitar el código
        df_csv['infraestructura'] = df_csv.get('num_infraestructura_petrolera', 0)
        df_csv['salud_10k'] = df_csv.get('establecimientos_por_10k_hab', 0)
        df_csv['pct_afro'] = df_csv.get('pct_poblacion_afro', 0)
        df_csv['densidad_petroleo'] = df_csv.get('densidad_petroleo_km2', 0)
        df_csv['pozos'] = df_csv.get('num_pozos', 0)
        df_csv['contaminacion'] = df_csv.get('num_sitios_contaminados', 0)
        # NO llenar NaN en cluster_kmeans - mantener como están
        return df_csv
    else:
        # Fallback: cargar desde PostGIS
        query = """
        SELECT 
            nombre_parroquia,
            nombre_canton,
            nombre_provincia,
            ST_Y(ST_Centroid(geometry)) as lat,
            ST_X(ST_Centroid(geometry)) as lon,
            COALESCE(num_infraestructura_petrolera, 0) as infraestructura,
            COALESCE(num_pozos, 0) as pozos,
            COALESCE(num_sitios_contaminados, 0) as contaminacion,
            COALESCE(establecimientos_por_10k_hab, 0) as salud_10k,
            COALESCE(pct_poblacion_afro, 0) as pct_afro,
            COALESCE(densidad_petroleo_km2, 0) as densidad_petroleo,
            CASE 
                WHEN num_infraestructura_petrolera > 0 THEN 1 
                ELSE 0 
            END as tiene_petroleo
        FROM parroquias
        WHERE ST_Centroid(geometry) IS NOT NULL;
        """
        return execute_query(engine, query)

df = load_spatial_data()

if df.empty:
    st.error("No se pudieron cargar los datos espaciales")
    st.stop()

# ═══════════════════════════════════════════════════════════════════════
# USAR CLUSTERS DEL NOTEBOOK 6
# ═══════════════════════════════════════════════════════════════════════

# Si no hay cluster_kmeans, crear uno temporal (no debería pasar)
if 'cluster_kmeans' not in df.columns:
    st.warning("No se encontraron clusters pre-calculados. Usando clustering temporal.")
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    
    features = ['infraestructura', 'salud_10k', 'pct_afro', 'densidad_petroleo']
    df_cluster = df[features].copy().fillna(0)
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df_cluster)
    
    kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
    df['cluster_kmeans'] = kmeans.fit_predict(X_scaled)

# Renombrar para simplicidad en el código
df['cluster'] = df['cluster_kmeans']

# NO filtrar - mantener todas las parroquias (incluso sin cluster)
# El notebook 6 muestra todas las parroquias, solo colorea las que tienen cluster

# Debug: Mostrar cuántas parroquias se cargaron
st.sidebar.markdown("---")
st.sidebar.markdown(f"**Datos cargados:**")
st.sidebar.markdown(f"- Total parroquias: {len(df)}")
st.sidebar.markdown(f"- Con cluster: {df['cluster'].notna().sum()}")
st.sidebar.markdown(f"- Sin cluster: {df['cluster'].isna().sum()}")

# ═══════════════════════════════════════════════════════════════════════
# SECCIÓN 1: 4 MAPAS PRINCIPALES
# ═══════════════════════════════════════════════════════════════════════

st.markdown("### Mapas de Análisis Espacial")

# Crear los 4 mapas en columnas 2x2
col1, col2 = st.columns(2)

# MAPA 1: Acceso a Salud
with col1:
    df_salud = df[df['salud_10k'] > 0].copy()
    
    fig1 = px.scatter_mapbox(
        df_salud,
        lat='lat',
        lon='lon',
        color='salud_10k',
        color_continuous_scale='Greens',
        hover_name='nombre_parroquia',
        hover_data={
            'nombre_provincia': True,
            'salud_10k': ':.2f',
            'lat': False,
            'lon': False
        },
        zoom=5.2,
        height=400,
        labels={'salud_10k': 'Salud (10k hab)'}
    )
    
    fig1.update_layout(
        mapbox_style="carto-positron",
        margin={"r": 0, "t": 30, "l": 0, "b": 0},
        title={
            'text': 'Acceso a Salud (Establecimientos por 10k hab)',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 12}
        }
    )
    
    st.plotly_chart(fig1, use_container_width=True)
    st.caption(f"**Interpretación:** {len(df_salud):,} parroquias con datos de salud. Las áreas urbanas (costa y sierra centro) concentran mayor acceso a servicios de salud.")

# MAPA 2: Infraestructura Petrolera
with col2:
    df_petroleo = df[df['infraestructura'] > 0].copy()
    
    fig2 = px.scatter_mapbox(
        df_petroleo,
        lat='lat',
        lon='lon',
        color='infraestructura',
        color_continuous_scale='Reds',
        size='infraestructura',
        size_max=15,
        hover_name='nombre_parroquia',
        hover_data={
            'nombre_provincia': True,
            'infraestructura': True,
            'pozos': True,
            'lat': False,
            'lon': False
        },
        zoom=5.2,
        height=400,
        labels={'infraestructura': 'Infraestructura'}
    )
    
    fig2.update_layout(
        mapbox_style="carto-positron",
        margin={"r": 0, "t": 30, "l": 0, "b": 0},
        title={
            'text': 'Infraestructura Petrolera (conteo)',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 12}
        }
    )
    
    st.plotly_chart(fig2, use_container_width=True)
    st.caption(f"**Interpretación:** {len(df_petroleo):,} parroquias con actividad petrolera. Concentración en la Amazonía (Sucumbíos, Orellana) y costa (Santa Elena).")

col3, col4 = st.columns(2)

# MAPA 3: Presencia de Petróleo (Binario)
with col3:
    # Crear etiquetas legibles
    df_map3 = df.copy()
    df_map3['tiene_petroleo_str'] = df_map3['tiene_petroleo'].apply(
        lambda x: 'Con petróleo' if x == 1 else 'Sin petróleo'
    )
    
    # Colores exactos del notebook 6: lightblue (sin) y darkred (con)
    fig3 = px.scatter_mapbox(
        df_map3,
        lat='lat',
        lon='lon',
        color='tiene_petroleo_str',
        color_discrete_map={
            'Sin petróleo': '#add8e6',  # lightblue
            'Con petróleo': '#8b0000'   # darkred
        },
        hover_name='nombre_parroquia',
        hover_data={
            'nombre_provincia': True,
            'infraestructura': True,
            'lat': False,
            'lon': False,
            'tiene_petroleo_str': False
        },
        zoom=5.2,
        height=400,
        labels={'tiene_petroleo_str': ''},
        category_orders={'tiene_petroleo_str': ['Sin petróleo', 'Con petróleo']}
    )
    
    fig3.update_layout(
        mapbox_style="carto-positron",
        margin={"r": 0, "t": 30, "l": 0, "b": 0},
        title={
            'text': 'Presencia de Infraestructura Petrolera (Binario)',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 12}
        },
        showlegend=False  # Quitar leyenda para no tapar el mapa
    )
    
    st.plotly_chart(fig3, use_container_width=True)
    
    con_petroleo = len(df[df['tiene_petroleo'] == 1])
    sin_petroleo = len(df[df['tiene_petroleo'] == 0])
    st.caption(f"**Interpretación:** Con petróleo: {con_petroleo:,} | Sin petróleo: {sin_petroleo:,}. Solo el 8.6% de las parroquias tienen actividad petrolera.")

# MAPA 4: Clusters + Densidad Petrolera
with col4:
    # Convertir cluster a string para colores discretos (manejar NaN)
    df_map4 = df.copy()
    df_map4['cluster_str'] = df_map4['cluster'].apply(
        lambda x: f'Cluster {int(x)}' if pd.notna(x) else 'Sin cluster'
    )
    
    # Crear tamaño de punto: base + densidad (para que todos sean visibles)
    df_map4['size_punto'] = 5 + df_map4['densidad_petroleo'] * 2
    
    # Colores exactos del notebook 6
    cluster_colors = {
        'Cluster 0': 'blue',
        'Cluster 1': 'red',
        'Cluster 2': 'green',
        'Cluster 3': 'orange',
        'Sin cluster': 'lightgray'
    }
    
    fig4 = px.scatter_mapbox(
        df_map4,
        lat='lat',
        lon='lon',
        color='cluster_str',
        color_discrete_map=cluster_colors,
        size='size_punto',
        size_max=20,
        hover_name='nombre_parroquia',
        hover_data={
            'nombre_provincia': True,
            'densidad_petroleo': ':.2f',
            'salud_10k': ':.2f',
            'lat': False,
            'lon': False,
            'cluster_str': True,
            'size_punto': False
        },
        zoom=5.2,
        height=400,
        labels={'cluster_str': 'Cluster', 'densidad_petroleo': 'Densidad'},
        category_orders={'cluster_str': ['Cluster 0', 'Cluster 1', 'Cluster 2', 'Cluster 3', 'Sin cluster']}
    )
    
    fig4.update_layout(
        mapbox_style="carto-positron",
        margin={"r": 0, "t": 30, "l": 0, "b": 0},
        title={
            'text': 'Clusters + Densidad Petrolera (tamaño del punto)',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 12}
        }
    )
    
    st.plotly_chart(fig4, use_container_width=True)
    
    # Contar parroquias por cluster
    c0 = (df['cluster'] == 0).sum()
    c1 = (df['cluster'] == 1).sum()
    c2 = (df['cluster'] == 2).sum()
    c3 = (df['cluster'] == 3).sum()
    sin_cluster = df['cluster'].isna().sum()
    
    st.caption(f"**Interpretación:** K-Means identifica 4 grupos distintos. Cluster 0 (azul, n={c0}): baja actividad petrolera. Cluster 1 (rojo, n={c1}): **alta actividad petrolera en Amazonía**. Cluster 2 (verde, n={c2}): sin petróleo, mejor salud. Cluster 3 (naranja, n={c3}): alta población afroecuatoriana en Esmeraldas. Gris (n={sin_cluster}): sin datos completos. El tamaño indica densidad petrolera (infra/km²).")

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════
# SECCIÓN 2: PARADOJA EXTRACTIVISTA
# ═══════════════════════════════════════════════════════════════════════

st.markdown("### Paradoja Extractivista: Petróleo vs Salud")

col1, col2, col3 = st.columns(3)

# GRÁFICO 1: Scatter Plot con Tendencia
with col1:
    df_completo = df[(df['infraestructura'] > 0) & (df['salud_10k'] > 0)].copy()
    
    fig_scatter = px.scatter(
        df_completo,
        x='infraestructura',
        y='salud_10k',
        opacity=0.6,
        labels={
            'infraestructura': 'Núm. Infraestructura Petrolera',
            'salud_10k': 'Establecimientos por 10k hab'
        },
        hover_data=['nombre_parroquia', 'nombre_provincia']
    )
    
    # Añadir línea de tendencia
    from scipy import stats
    slope, intercept, r_value, p_value, std_err = stats.linregress(
        df_completo['infraestructura'], 
        df_completo['salud_10k']
    )
    
    line_x = [df_completo['infraestructura'].min(), df_completo['infraestructura'].max()]
    line_y = [slope * x + intercept for x in line_x]
    
    fig_scatter.add_trace(
        go.Scatter(
            x=line_x,
            y=line_y,
            mode='lines',
            name='Tendencia',
            line=dict(color='red', dash='dash'),
            showlegend=False
        )
    )
    
    # Añadir anotación con correlación
    fig_scatter.add_annotation(
        x=0.05,
        y=0.95,
        xref='paper',
        yref='paper',
        text=f'r = {r_value:.3f}<br>p = {p_value:.5f}',
        showarrow=False,
        bgcolor='white',
        bordercolor='black',
        borderwidth=1,
        font=dict(size=10)
    )
    
    fig_scatter.update_layout(
        title={
            'text': 'Paradoja Extractivista: Petróleo vs Salud',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 12}
        },
        height=400,
        showlegend=False
    )
    
    st.plotly_chart(fig_scatter, use_container_width=True)
    st.caption(f"**Interpretación:** Correlación negativa débil (r={r_value:.3f}). A mayor infraestructura petrolera, menor acceso a salud. La tendencia (línea roja) muestra la relación inversa.")

# GRÁFICO 2: Boxplot por Cluster
with col2:
    # Filtrar solo parroquias con cluster válido para el boxplot
    df_box = df[df['cluster'].notna()].copy()
    df_box['cluster_str'] = 'C' + df_box['cluster'].astype(int).astype(str)
    
    fig_box = px.box(
        df_box,
        x='cluster_str',
        y='salud_10k',
        color='cluster_str',
        labels={
            'cluster_str': 'Cluster',
            'salud_10k': 'Establecimientos por 10k hab'
        },
        color_discrete_map={'C0': 'blue', 'C1': 'red', 'C2': 'green', 'C3': 'orange'},
        category_orders={'cluster_str': ['C0', 'C1', 'C2', 'C3']}
    )
    
    fig_box.update_layout(
        title={
            'text': 'Acceso a Salud por Cluster',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 12}
        },
        height=400,
        showlegend=False
    )
    
    st.plotly_chart(fig_box, use_container_width=True)
    
    # Identificar cluster petrolero
    cluster_stats = df.groupby('cluster')['infraestructura'].mean()
    cluster_petrolero = cluster_stats.idxmax()
    
    st.caption(f"**Interpretación:** Cluster {cluster_petrolero} (petrolero) tiene la mediana más baja de acceso a salud. Los outliers superiores representan capitales provinciales.")

# GRÁFICO 3: Barras Comparativas
with col3:
    cluster_comparison = df.groupby('cluster').agg({
        'densidad_petroleo': 'mean',
        'salud_10k': 'mean'
    }).reset_index()
    
    # Normalizar para comparación visual
    cluster_comparison['densidad_norm'] = cluster_comparison['densidad_petroleo'] / cluster_comparison['densidad_petroleo'].max() * 20
    cluster_comparison['salud_norm'] = cluster_comparison['salud_10k']
    
    fig_bar = go.Figure()
    
    fig_bar.add_trace(go.Bar(
        x=cluster_comparison['cluster'],
        y=cluster_comparison['densidad_norm'],
        name='Densidad Petrolera (norm)',
        marker_color='#991b1b'
    ))
    
    fig_bar.add_trace(go.Bar(
        x=cluster_comparison['cluster'],
        y=cluster_comparison['salud_norm'],
        name='Establecimientos/10k hab',
        marker_color='#10b981'
    ))
    
    fig_bar.update_layout(
        title={
            'text': 'Paradoja: Petróleo Alto = Salud Baja',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 12}
        },
        xaxis_title='Cluster',
        yaxis_title='Valor',
        height=400,
        barmode='group',
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='center',
            x=0.5,
            font=dict(size=9)
        )
    )
    
    st.plotly_chart(fig_bar, use_container_width=True)
    st.caption(f"**Interpretación:** Cluster {cluster_petrolero} tiene alta densidad petrolera (rojo) pero baja salud (verde). La paradoja extractivista es evidente: los recursos no se traducen en servicios.")

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════
# SECCIÓN 3: CARACTERIZACIÓN DE CLUSTERS
# ═══════════════════════════════════════════════════════════════════════

st.markdown("### Caracterización de Clusters")

# Calcular estadísticas por cluster (solo clusters válidos)
df_clusters_valid = df[df['cluster'].notna()].copy()
cluster_stats_full = df_clusters_valid.groupby('cluster').agg({
    'nombre_parroquia': 'count',
    'infraestructura': 'mean',
    'salud_10k': 'mean',
    'pct_afro': 'mean',
    'densidad_petroleo': 'mean'
}).round(2)

cluster_stats_full.columns = ['Num. Parroquias', 'Infraestructura Promedio', 'Salud Promedio', '% Afro Promedio', 'Densidad Petróleo']

st.dataframe(cluster_stats_full, use_container_width=True)

# Identificar características de cada cluster
cluster_petrolero = cluster_stats_full['Infraestructura Promedio'].idxmax()
cluster_salud = cluster_stats_full['Salud Promedio'].idxmax()
cluster_afro = cluster_stats_full['% Afro Promedio'].idxmax()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.info(f"""
    **Cluster 0**
    
    {int(cluster_stats_full.loc[0, 'Num. Parroquias'])} parroquias
    
    Infraestructura: {cluster_stats_full.loc[0, 'Infraestructura Promedio']:.2f}
    
    Salud: {cluster_stats_full.loc[0, 'Salud Promedio']:.2f}
    """)

with col2:
    st.info(f"""
    **Cluster 1**
    
    {int(cluster_stats_full.loc[1, 'Num. Parroquias'])} parroquias
    
    Infraestructura: {cluster_stats_full.loc[1, 'Infraestructura Promedio']:.2f}
    
    Salud: {cluster_stats_full.loc[1, 'Salud Promedio']:.2f}
    """)

with col3:
    st.info(f"""
    **Cluster 2**
    
    {int(cluster_stats_full.loc[2, 'Num. Parroquias'])} parroquias
    
    Infraestructura: {cluster_stats_full.loc[2, 'Infraestructura Promedio']:.2f}
    
    Salud: {cluster_stats_full.loc[2, 'Salud Promedio']:.2f}
    """)

with col4:
    st.info(f"""
    **Cluster 3**
    
    {int(cluster_stats_full.loc[3, 'Num. Parroquias'])} parroquias
    
    Infraestructura: {cluster_stats_full.loc[3, 'Infraestructura Promedio']:.2f}
    
    Salud: {cluster_stats_full.loc[3, 'Salud Promedio']:.2f}
    """)

st.caption(f"**Interpretación:** Cluster {int(cluster_petrolero)} concentra la mayor actividad petrolera en Amazonía. Cluster {int(cluster_salud)} tiene el mejor acceso a salud sin petróleo. Cluster {int(cluster_afro)} presenta la mayor población afroecuatoriana en Esmeraldas. Cluster 0 representa parroquias con características intermedias.")

st.markdown("---")
st.caption("TFM - Máster en Visual Analytics and Big Data | 2025")
