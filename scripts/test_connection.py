#!/usr/bin/env python3
"""
Script para probar la conexión con Plex y generar imagen de prueba
"""
import os
import sys
from dotenv import load_dotenv

# Añadir el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.plex_client import create_plex_client
from api.svg_generator import SVGGenerator

def test_plex_connection():
    """Prueba la conexión con Plex"""
    print("🔍 Probando conexión con Plex...")
    
    client = create_plex_client()
    if not client:
        print("❌ No se pudo crear cliente de Plex")
        return False
    
    if not client.is_connected():
        print("❌ No se pudo conectar al servidor Plex")
        return False
    
    server_info = client.get_server_info()
    print(f"✅ Conectado a: {server_info.get('name', 'Unknown')}")
    print(f"   Versión: {server_info.get('version', 'Unknown')}")
    print(f"   Sesiones activas: {server_info.get('sessions_count', 0)}")
    
    # Probar obtener sesión actual
    session = client.get_current_session()
    if session:
        print(f"🎵 Reproduciendo: {session.get('title', 'Unknown')}")
        print(f"   Tipo: {session.get('type', 'Unknown')}")
        print(f"   Estado: {session.get('state', 'Unknown')}")
        print(f"   Usuario: {session.get('user', 'Unknown')}")
    else:
        print("⏸️  No hay reproducción activa")
    
    return True

def test_image_generation():
    """Prueba la generación de imágenes"""
    print("\n🖼️  Probando generación de imágenes...")
    # Datos de prueba
    test_data = {
        'title': 'Canción de Prueba',
        'type': 'track',
        'state': 'playing',
        'user': 'TestUser',
        'progress': 120,
        'duration': 240,
        'track_title': 'Canción de Prueba',
        'artist': 'Artista de Prueba',
        'album': 'Álbum de Prueba'
    }
    svggen = SVGGenerator(400, 90, 'normal')
    try:
        svg = svggen.generate_now_playing_svg(test_data)
        with open('test_image.svg', 'w', encoding='utf-8') as f:
            f.write(svg)
        print("✅ SVG generado exitosamente: test_image.svg")
        return True
    except Exception as e:
        print(f"❌ Error generando SVG: {e}")
        return False

def main():
    """Función principal"""
    print("🧪 Plex2Sign - Test de Conexiones\n")
    # Cargar variables de entorno
    load_dotenv()
    # Verificar solo el token
    if not os.getenv('PLEX_TOKEN'):
        print("❌ Falta la variable de entorno: PLEX_TOKEN")
        print("💡 Asegúrate de tener un archivo .env configurado")
        return False
        # Agregar script de prueba para depurar la conexión y mostrar el token, URL y usuario detectados
        print(f"Token usado: {os.getenv('PLEX_TOKEN')}")
        print(f"URL detectada: {os.getenv('PLEX_URL')}")
        print(f"Usuario propietario detectado: {os.getenv('PLEX_USER', 'Desconocido')}")
    success = True
    # Probar Plex
    success &= test_plex_connection()
    # Probar generación de imágenes
    success &= test_image_generation()
    print(f"\n{'✅ Todas las pruebas pasaron' if success else '❌ Algunas pruebas fallaron'}")
    return success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
