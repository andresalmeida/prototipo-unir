"""
═══════════════════════════════════════════════════════════════════════
SCRIPT DE PRUEBA - CONEXIÓN A POSTGIS
═══════════════════════════════════════════════════════════════════════

Ejecuta este script para verificar que la conexión a PostGIS funciona
correctamente antes de lanzar el dashboard.

Uso:
    python dashboard/test_connection.py
"""

import sys
from pathlib import Path

# Agregar el directorio actual al path
sys.path.append(str(Path(__file__).parent))

from config import DB_CONFIG
from utils.db_connection import get_engine, execute_query
from utils.queries import QUERY_METRICAS_GENERALES

def test_connection():
    """Prueba la conexión a PostGIS y muestra métricas básicas."""
    
    print("="*70)
    print("🔧 PRUEBA DE CONEXIÓN A POSTGIS")
    print("="*70)
    
    # Mostrar configuración
    print("\n📋 Configuración:")
    print(f"   Host: {DB_CONFIG['host']}")
    print(f"   Puerto: {DB_CONFIG['port']}")
    print(f"   Database: {DB_CONFIG['database']}")
    print(f"   Usuario: {DB_CONFIG['user']}")
    
    # Intentar conexión
    print("\n🔌 Intentando conectar...")
    
    try:
        engine = get_engine()
        
        if engine is None:
            print("\n❌ ERROR: No se pudo crear el engine de conexión")
            return False
        
        # Test de conexión
        with engine.connect() as conn:
            # Versión de PostgreSQL
            result = conn.execute("SELECT version();")
            pg_version = result.fetchone()[0].split(',')[0]
            
            # Versión de PostGIS
            result = conn.execute("SELECT PostGIS_Version();")
            postgis_version = result.fetchone()[0]
            
            print("\n✅ CONEXIÓN EXITOSA")
            print(f"   PostgreSQL: {pg_version}")
            print(f"   PostGIS: {postgis_version}")
        
        # Obtener métricas
        print("\n📊 Obteniendo métricas generales...")
        
        df_metricas = execute_query(engine, QUERY_METRICAS_GENERALES)
        
        if df_metricas.empty:
            print("\n⚠️ WARNING: No se pudieron obtener métricas")
            return False
        
        metricas = df_metricas.iloc[0]
        
        print("\n✅ MÉTRICAS OBTENIDAS:")
        print(f"   Total Parroquias: {int(metricas['total_parroquias']):,}")
        print(f"   Parroquias con Petróleo: {int(metricas['parroquias_con_petroleo']):,}")
        print(f"   Total Pozos: {int(metricas['total_pozos']):,}")
        print(f"   Total Sitios Contaminados: {int(metricas['total_sitios_contaminados']):,}")
        print(f"   Salud SIN petróleo: {metricas['salud_sin_petroleo']:.2f} estab/10k hab")
        print(f"   Salud CON petróleo: {metricas['salud_con_petroleo']:.2f} estab/10k hab")
        
        diferencia = ((metricas['salud_con_petroleo'] - metricas['salud_sin_petroleo']) / metricas['salud_sin_petroleo'] * 100)
        print(f"   Diferencia: {diferencia:.1f}% (menos acceso en zonas petroleras)")
        
        print("\n" + "="*70)
        print("🎉 PRUEBA COMPLETADA EXITOSAMENTE")
        print("="*70)
        print("\n💡 El dashboard está listo para ejecutarse:")
        print("   streamlit run dashboard/app.py")
        print("\n" + "="*70)
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\n💡 SOLUCIONES:")
        print("   1. Verifica que el contenedor Docker esté corriendo:")
        print("      docker ps")
        print("   2. Verifica las credenciales en dashboard/config.py")
        print("   3. Verifica que el puerto 5434 esté disponible:")
        print("      lsof -i :5434")
        print("   4. Verifica que la base de datos 'prototipo_salud' exista")
        
        return False


if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)

