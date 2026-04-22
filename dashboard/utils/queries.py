"""
═══════════════════════════════════════════════════════════════════════
QUERIES SQL PARA EL DASHBOARD
═══════════════════════════════════════════════════════════════════════
"""

# ───────────────────────────────────────────────────────────────────────
# QUERIES DE MÉTRICAS GENERALES
# ───────────────────────────────────────────────────────────────────────

QUERY_METRICAS_GENERALES = """
SELECT 
    COUNT(*) as total_parroquias,
    COUNT(CASE WHEN tiene_petroleo = 1 THEN 1 END) as parroquias_con_petroleo,
    SUM(num_pozos) as total_pozos,
    SUM(num_sitios_contaminados) as total_sitios_contaminados,
    ROUND(CAST(AVG(CASE WHEN tiene_petroleo = 1 THEN establecimientos_por_10k_hab END) AS NUMERIC), 2) as salud_con_petroleo,
    ROUND(CAST(AVG(CASE WHEN tiene_petroleo = 0 THEN establecimientos_por_10k_hab END) AS NUMERIC), 2) as salud_sin_petroleo
FROM parroquias
WHERE establecimientos_por_10k_hab IS NOT NULL;
"""

# ───────────────────────────────────────────────────────────────────────
# QUERY TOP PARROQUIAS PETROLERAS
# ───────────────────────────────────────────────────────────────────────

QUERY_TOP_PETROLERAS = """
SELECT 
    nombre_parroquia,
    nombre_canton,
    nombre_provincia,
    num_infraestructura_petrolera,
    num_pozos,
    num_sitios_contaminados,
    ROUND(CAST(densidad_petroleo_km2 AS NUMERIC), 2) as densidad_km2,
    COALESCE(establecimientos_por_10k_hab, 0) as salud_10k,
    COALESCE(poblacion_total, 0) as poblacion,
    COALESCE(pct_poblacion_afro, 0) as pct_afro
FROM parroquias
WHERE num_infraestructura_petrolera > 0
ORDER BY num_infraestructura_petrolera DESC
LIMIT {limit};
"""

# ───────────────────────────────────────────────────────────────────────
# QUERY PARADOJA EXTRACTIVISTA
# ───────────────────────────────────────────────────────────────────────

QUERY_PARADOJA_CRITICA = """
SELECT 
    nombre_parroquia,
    nombre_canton,
    nombre_provincia,
    num_infraestructura_petrolera,
    num_pozos,
    num_sitios_contaminados,
    COALESCE(establecimientos_por_10k_hab, 0) as salud_10k,
    COALESCE(poblacion_total, 0) as poblacion
FROM parroquias
WHERE num_infraestructura_petrolera > 100
  AND (establecimientos_por_10k_hab = 0 OR establecimientos_por_10k_hab IS NULL)
ORDER BY num_infraestructura_petrolera DESC
LIMIT {limit};
"""

# ───────────────────────────────────────────────────────────────────────
# QUERY CORRELACIÓN PETRÓLEO VS SALUD
# ───────────────────────────────────────────────────────────────────────

QUERY_CORRELACION = """
SELECT 
    CASE 
        WHEN tiene_petroleo = 1 THEN 'Con petróleo'
        ELSE 'Sin petróleo'
    END as categoria,
    COUNT(*) as num_parroquias,
    ROUND(CAST(AVG(establecimientos_por_10k_hab) AS NUMERIC), 2) as salud_promedio,
    ROUND(CAST(AVG(num_infraestructura_petrolera) AS NUMERIC), 2) as infra_promedio,
    ROUND(CAST(AVG(pct_poblacion_afro) AS NUMERIC), 2) as afro_promedio
FROM parroquias
WHERE establecimientos_por_10k_hab IS NOT NULL
GROUP BY tiene_petroleo
ORDER BY tiene_petroleo DESC;
"""

# ───────────────────────────────────────────────────────────────────────
# QUERY ANÁLISIS ÉTNICO
# ───────────────────────────────────────────────────────────────────────

QUERY_AFRO_PETROLEO = """
SELECT 
    nombre_parroquia,
    nombre_provincia,
    pct_poblacion_afro,
    num_infraestructura_petrolera,
    establecimientos_por_10k_hab
FROM parroquias
WHERE pct_poblacion_afro > 5 
  AND num_infraestructura_petrolera > 0
ORDER BY pct_poblacion_afro DESC;
"""

QUERY_TOP_AFRO = """
SELECT 
    nombre_parroquia,
    nombre_provincia,
    pct_poblacion_afro,
    poblacion_total,
    COALESCE(num_infraestructura_petrolera, 0) as infraestructura,
    COALESCE(establecimientos_por_10k_hab, 0) as salud_10k
FROM parroquias
WHERE pct_poblacion_afro > 0
ORDER BY pct_poblacion_afro DESC
LIMIT {limit};
"""

# ───────────────────────────────────────────────────────────────────────
# QUERY DATOS COMPLETOS (PARA SCATTER PLOTS)
# ───────────────────────────────────────────────────────────────────────

QUERY_SCATTER_DATA = """
SELECT 
    nombre_parroquia,
    nombre_provincia,
    num_infraestructura_petrolera,
    establecimientos_por_10k_hab,
    pct_poblacion_afro,
    tiene_petroleo
FROM parroquias
WHERE establecimientos_por_10k_hab IS NOT NULL
  AND num_infraestructura_petrolera IS NOT NULL;
"""

# ───────────────────────────────────────────────────────────────────────
# QUERIES GEOESPACIALES (CON GEOMETRÍA)
# ───────────────────────────────────────────────────────────────────────

QUERY_MAPA_PARROQUIAS = """
SELECT 
    codigo_dpa,
    nombre_parroquia,
    nombre_provincia,
    COALESCE(num_infraestructura_petrolera, 0) as infraestructura,
    COALESCE(establecimientos_por_10k_hab, 0) as salud_10k,
    COALESCE(pct_poblacion_afro, 0) as pct_afro,
    tiene_petroleo,
    geometry
FROM parroquias
WHERE geometry IS NOT NULL;
"""

QUERY_POZOS = """
SELECT 
    nombre as nombre_pozo,
    estado,
    geometry
FROM pozos_petroleros
WHERE geometry IS NOT NULL
LIMIT {limit};
"""

QUERY_CONTAMINACION = """
SELECT 
    geometry
FROM sitios_contaminacion
WHERE geometry IS NOT NULL
LIMIT {limit};
"""

# ───────────────────────────────────────────────────────────────────────
# QUERY FILTRADO POR PROVINCIA
# ───────────────────────────────────────────────────────────────────────

QUERY_FILTRO_PROVINCIA = """
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
FROM parroquias
WHERE nombre_provincia = %(provincia)s
ORDER BY num_infraestructura_petrolera DESC;
"""

# ───────────────────────────────────────────────────────────────────────
# QUERY LISTA DE PROVINCIAS
# ───────────────────────────────────────────────────────────────────────

QUERY_PROVINCIAS = """
SELECT DISTINCT nombre_provincia
FROM parroquias
ORDER BY nombre_provincia;
"""

# ───────────────────────────────────────────────────────────────────────
# QUERY ESTADÍSTICAS POR PROVINCIA
# ───────────────────────────────────────────────────────────────────────

QUERY_STATS_PROVINCIA = """
SELECT 
    nombre_provincia,
    COUNT(*) as num_parroquias,
    SUM(CASE WHEN tiene_petroleo = 1 THEN 1 ELSE 0 END) as parroquias_petroleras,
    SUM(COALESCE(num_infraestructura_petrolera, 0)) as total_infraestructura,
    ROUND(CAST(AVG(COALESCE(establecimientos_por_10k_hab, 0)) AS NUMERIC), 2) as salud_promedio,
    ROUND(CAST(AVG(COALESCE(pct_poblacion_afro, 0)) AS NUMERIC), 2) as afro_promedio
FROM parroquias
GROUP BY nombre_provincia
ORDER BY total_infraestructura DESC;
"""

