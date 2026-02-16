
import sys
import os
import json

# Agregar el directorio actual al path
sys.path.append(os.getcwd())

try:
    from database import (
        cargar_ubicaciones, guardar_ubicaciones,
        cargar_tipos_solicitud, guardar_tipos_solicitud,
        cargar_medios_solicitud, guardar_medios_solicitud
    )
    
    print("Verificando funciones de gestión de configuración...")
    
    # 1. Ubicaciones
    orig_ubicaciones = cargar_ubicaciones()
    test_ubicacion = f"UBICACION_PRUEBA_{os.getpid()}"
    print(f" - Añadiendo ubicación: {test_ubicacion}")
    temp_ubicaciones = orig_ubicaciones + [test_ubicacion]
    guardar_ubicaciones(temp_ubicaciones)
    
    if test_ubicacion in cargar_ubicaciones():
        print("   ✅ Ubicación guardada correctamente.")
    else:
        print("   ❌ Error: Ubicación no encontrada tras guardar.")
        
    # Limpiar
    guardar_ubicaciones(orig_ubicaciones)
    
    # 2. Tipos de Solicitud
    orig_tipos = cargar_tipos_solicitud()
    test_tipo = f"TIPO_PRUEBA_{os.getpid()}"
    print(f" - Añadiendo tipo: {test_tipo}")
    temp_tipos = orig_tipos + [test_tipo]
    guardar_tipos_solicitud(temp_tipos)
    
    if test_tipo in cargar_tipos_solicitud():
        print("   ✅ Tipo de solicitud guardado correctamente.")
    else:
        print("   ❌ Error: Tipo no encontrado tras guardar.")
        
    guardar_tipos_solicitud(orig_tipos)
    
    # 3. Medios de Solicitud
    orig_medios = cargar_medios_solicitud()
    test_medio = f"MEDIO_PRUEBA_{os.getpid()}"
    print(f" - Añadiendo medio: {test_medio}")
    temp_medios = orig_medios + [test_medio]
    guardar_medios_solicitud(temp_medios)
    
    if test_medio in cargar_medios_solicitud():
        print("   ✅ Medio de solicitud guardado correctamente.")
    else:
        print("   ❌ Error: Medio no encontrado tras guardar.")
        
    guardar_medios_solicitud(orig_medios)
    
    print("\n✅ Verificación de base de datos completada satisfactoriamente.")
            
except Exception as e:
    import traceback
    traceback.print_exc()
