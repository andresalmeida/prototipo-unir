# Paradoja Extractivista en Ecuador

Análisis geoespacial de la relación entre infraestructura petrolera, acceso a salud y población afroecuatoriana en Ecuador.

**TFM — Máster en Análisis de Datos Masivos · 2025**

---

## Estructura del repositorio

```
TFM-UNIR/
├── dashboard/              ← Aplicación Streamlit
│   ├── app.py              ← Punto de entrada
│   ├── config.py
│   ├── pages/              ← Páginas del dashboard
│   └── utils/              ← Loader de CSV y queries
├── data/
│   └── processed/          ← CSVs usados por el dashboard
├── notebooks/              ← Pipeline ETL (no requerido para el deploy)
├── requirements.txt        ← Deps mínimas para Streamlit Cloud
├── runtime.txt             ← Versión de Python
└── .streamlit/config.toml  ← Tema y settings
```

El dashboard lee directamente desde `data/processed/parroquias_con_clusters.csv`. **No requiere base de datos** para funcionar.

---

## Ejecutar localmente

```bash
pip install -r requirements.txt
streamlit run dashboard/app.py
```

Abre [http://localhost:8501](http://localhost:8501).

---

## Deploy en Streamlit Community Cloud

### 1. Sube el repo a GitHub

```bash
git init
git add .
git commit -m "Dashboard listo para deploy"
git branch -M main
git remote add origin https://github.com/<TU_USUARIO>/<TU_REPO>.git
git push -u origin main
```

### 2. Conecta con Streamlit Cloud

1. Entra a [share.streamlit.io](https://share.streamlit.io) e inicia sesión con GitHub.
2. Click en **"New app"**.
3. Configura:
   - **Repository:** `<TU_USUARIO>/<TU_REPO>`
   - **Branch:** `main`
   - **Main file path:** `dashboard/app.py`
4. (Opcional) **Advanced settings** → Python version: `3.11`
5. Click **"Deploy"**.

En 2-3 minutos tendrás una URL pública del estilo `https://tu-app.streamlit.app`.

### 3. Actualizar el deploy

Cualquier `git push` a `main` redeploya automáticamente.

---

## Hallazgos principales

- **Paradoja extractivista**: parroquias con actividad petrolera tienen ~33% menos acceso a servicios de salud (3.06 vs 5.39 establecimientos por 10k habitantes).
- 106 parroquias con infraestructura petrolera de un total de 1,236.
- 4,716 pozos petroleros y 7,026 sitios contaminados registrados.
- Las comunidades afroecuatorianas (concentradas en Esmeraldas) **no** están expuestas a actividad petrolera significativa — hallazgo inesperado del análisis.

---

## Páginas del dashboard

1. **Inicio** — Métricas generales y hallazgos clave
2. **Overview** — Análisis exploratorio (scatter, top 10 petroleras, comparativas por provincia)
3. **Análisis Espacial** — 4 mapas interactivos + clustering K-Means
4. **Explorador de Datos** — Filtros por provincia, descarga CSV

---

## Fuentes de datos

- **CONALI** — Límites parroquiales (1,236 parroquias)
- **INEC** — Censo de población y etnia (2022)
- **MSP** — Registro de establecimientos de salud (RAS 2020)
- **MAATE** — Infraestructura petrolera y contaminación
