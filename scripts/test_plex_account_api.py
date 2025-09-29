#!/usr/bin/env python3
"""
Script para probar la API de Plex Account y obtener URLs de servidores
"""
import os
import sys
import requests
import xml.etree.ElementTree as ET
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def test_plex_account_api():
    """Prueba la API de Plex Account para obtener recursos"""
    print("🧪 Plex2Sign - Test API de Plex Account")
    print()
    
    plex_token = os.getenv('PLEX_TOKEN')
    if not plex_token:
        print("❌ Faltan variables de entorno: PLEX_TOKEN")
        return False
    
    try:
        # API de Plex Account para obtener recursos
        api_url = f"https://plex.tv/api/resources?X-Plex-Token={plex_token}"
        print(f"🔍 Consultando: {api_url}")
        
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        
        print("✅ Respuesta recibida exitosamente")
        print()
        
        # Parsear XML
        root = ET.fromstring(response.content)
        
        print("📋 Dispositivos encontrados:")
        print("-" * 50)
        
        servers_found = 0
        for device in root.findall('Device'):
            name = device.get('name', 'Sin nombre')
            provides = device.get('provides', 'N/A')
            platform = device.get('platform', 'N/A')
            
            print(f"📱 {name}")
            print(f"   Plataforma: {platform}")
            print(f"   Proporciona: {provides}")
            
            # Buscar conexiones
            connections = device.findall('Connection')
            if connections:
                print("   🔗 Conexiones:")
                for conn in connections:
                    uri = conn.get('uri', 'N/A')
                    local = conn.get('local', 'false')
                    protocol = conn.get('protocol', 'N/A')
                    address = conn.get('address', 'N/A')
                    port = conn.get('port', 'N/A')
                    
                    connection_type = "🌐 Externa" if local == 'false' or local == '0' else "🏠 Local"
                    print(f"      {connection_type}: {uri}")
                    print(f"         Protocolo: {protocol}")
                    print(f"         Dirección: {address}:{port}")
                    print(f"         Local: {local}")
                    
                    # Si es un servidor, mostrar como recomendado
                    if 'server' in provides:
                        servers_found += 1
                        if 'plex.direct' in uri:
                            print(f"         ⭐ RECOMENDADO PARA VERCEL (plex.direct)")
                        elif local == 'false' or local == '0':
                            print(f"         ⭐ RECOMENDADO PARA VERCEL (externa)")
                        else:
                            print(f"         ⚠️  Solo funciona localmente")
            
            print()
        
        if servers_found == 0:
            print("❌ No se encontraron servidores Plex")
            return False
        else:
            print(f"✅ Se encontraron {servers_found} servidor(es) Plex")
            return True
            
    except requests.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return False
    except ET.ParseError as e:
        print(f"❌ Error parseando XML: {e}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

if __name__ == "__main__":
    success = test_plex_account_api()
    sys.exit(0 if success else 1)
