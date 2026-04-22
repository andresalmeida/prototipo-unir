# Instrucciones Rápidas - Dashboard

## 🚀 Inicio Rápido

```bash
# 1. Activar entorno (si usas uno)
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate     # Windows

# 2. Ejecutar dashboard
streamlit run app.py
```

## 🔧 Configuración

### Base de Datos

Editar `config.py`:

```python
DB_CONFIG = {
    'host': 'localhost',
    'port': 5434,
    'database': 'prototipo_salud',
    'user': 'postgres',
    'password': 'postgres'
}
```

### Verificar Conexión

```bash
python test_connection.py
```

## 📊 Páginas Disponibles

1. **Inicio**: Métricas generales y hallazgo principal
2. **Overview**: Análisis exploratorio con gráficos
3. **Explorador de Datos**: Filtros y descarga de datos

## 🛠️ Solución de Problemas

### Error de conexión a la base de datos

```bash
# Verificar que PostgreSQL esté corriendo
docker ps

# Verificar credenciales en config.py
```

### Error de importación de módulos

```bash
# Instalar dependencias faltantes
pip install streamlit pandas plotly sqlalchemy psycopg2-binary geopandas
```

### Puerto 8501 ocupado

```bash
# Usar otro puerto
streamlit run app.py --server.port 8502
```

## 📝 Notas

- El dashboard se recarga automáticamente al guardar cambios
- Los datos se cachean para mejor rendimiento
- Las queries SQL están en `utils/queries.py`
