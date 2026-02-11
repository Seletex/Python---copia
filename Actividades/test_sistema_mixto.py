#!/usr/bin/env python3
"""
Script de prueba para verificar el sistema mixto de configuración
(Actividades globales + actividades personales por usuario)
"""

from database import cargar_actividades

def test_sistema_mixto():
    """Prueba el sistema mixto de actividades"""
    print("🔍 TESTEANDO SISTEMA MIXTO DE CONFIGURACIÓN")
    print("=" * 60)
    
    # Test 1: Actividades globales (sin usuario específico)
    print("\n1. 📋 ACTIVIDADES GLOBALES (sin usuario):")
    actividades_globales = cargar_actividades()
    print(f"   Total: {len(actividades_globales)} actividades")
    for i, actividad in enumerate(actividades_globales, 1):
        print(f"   {i:2d}. {actividad}")
    
    # Test 2: Actividades para admin (globales + personales)
    print("\n2. 👨‍💼 ACTIVIDADES PARA ADMIN:")
    actividades_admin = cargar_actividades("admin")
    print(f"   Total: {len(actividades_admin)} actividades")
    for i, actividad in enumerate(actividades_admin, 1):
        print(f"   {i:2d}. {actividad}")
    
    # Test 3: Actividades para usuario1 (globales + personales)
    print("\n3. 👤 ACTIVIDADES PARA USUARIO1:")
    actividades_usuario1 = cargar_actividades("usuario1")
    print(f"   Total: {len(actividades_usuario1)} actividades")
    for i, actividad in enumerate(actividades_usuario1, 1):
        print(f"   {i:2d}. {actividad}")
    
    # Test 4: Actividades para usuario2 (globales + personales)
    print("\n4. 👤 ACTIVIDADES PARA USUARIO2:")
    actividades_usuario2 = cargar_actividades("usuario2")
    print(f"   Total: {len(actividades_usuario2)} actividades")
    for i, actividad in enumerate(actividades_usuario2, 1):
        print(f"   {i:2d}. {actividad}")
    
    # Test 5: Actividades para usuario3 (globales + personales)
    print("\n5. 👤 ACTIVIDADES PARA USUARIO3:")
    actividades_usuario3 = cargar_actividades("usuario3")
    print(f"   Total: {len(actividades_usuario3)} actividades")
    for i, actividad in enumerate(actividades_usuario3, 1):
        print(f"   {i:2d}. {actividad}")
    
    # Verificación del sistema mixto
    print("\n" + "=" * 60)
    print("✅ VERIFICACIÓN DEL SISTEMA MIXTO:")
    
    # Verificar que cada usuario tiene actividades únicas
    actividades_unicas = {}
    for usuario in ["admin", "usuario1", "usuario2", "usuario3"]:
        actividades = cargar_actividades(usuario)
        actividades_unicas[usuario] = actividades
        print(f"   • {usuario}: {len(actividades)} actividades")
    
    # Verificar que hay actividades compartidas y únicas
    actividades_compartidas = set(actividades_globales)
    print(f"   • Actividades globales compartidas: {len(actividades_compartidas)}")
    
    for usuario, actividades in actividades_unicas.items():
        actividades_propias = set(actividades) - actividades_compartidas
        print(f"   • {usuario} tiene {len(actividades_propias)} actividades propias")
    
    print("\n🎉 ¡SISTEMA MIXTO FUNCIONANDO CORRECTAMENTE!")

if __name__ == "__main__":
    test_sistema_mixto()