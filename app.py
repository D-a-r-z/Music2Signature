"""
Music2Signature - Aplicación principal
Muestra lo que estás reproduciendo en Plex en tu perfil de GitHub
"""
import os
import logging
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
from flask import Flask, Response, request, jsonify
from api.plex_client import create_plex_client
from api.svg_generator import SVGGenerator

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO if os.getenv('DEBUG', 'false').lower() != 'true' else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Crear aplicación Flask
app = Flask(__name__)

# Configuración de cache
CACHE_DURATION = int(os.getenv('CACHE_DURATION', 60))

# Cache en memoria
image_cache = {
    'last_update': None,
    'image_url': None,
    'session_data': None,
    'cache_duration': CACHE_DURATION
}

# Nota: PNGs eliminados - servimos sólo SVG


@app.route('/')
def index():
    """Página principal con información del proyecto"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
    <title>Music2Signature</title>
        <meta charset="utf-8">
        <style>
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                max-width: 800px; margin: 30px auto; padding: 15px;
                background: #0d1117; color: #f0f6fc;
            }
            .card { 
                background: #161b22; border-radius: 12px; padding: 15px; margin: 15px 0;
                border: 1px solid #9C27B0;
                box-shadow: 0 2px 8px rgba(0,0,0,0.3);
            }
            .status { padding: 8px; border-radius: 4px; margin: 8px 0; }
            .success { background: #161b22; color: white; }
            .error { background: #da3633; color: white; }
            .warning { background: #bf8700; color: white; }
            code { background: #21262d; padding: 2px 4px; border-radius: 3px; color: #f0f6fc; font-size: 0.9em; }
            a { color: #9C27B0; text-decoration: none; }
            a:hover { text-decoration: underline; }
            h1 { margin-top: 0; margin-bottom: 16px; }
            h2 { margin-top: 0; margin-bottom: 18px; }
            h3 { margin-top: 16px; margin-bottom: 8px; }
            p { margin-top: 4px; margin-bottom: 4px; }
            img { 
                max-width: 100%; 
                border-radius: 6px; 
                border: 1px solid #ddd; 
                margin: 1px 0;
                padding: 1px;
            }
        </style>
    </head>
    <body>
    <h1>🎵 Music2Signature</h1>
        <p>Utilidad para generar imágenes dinámicas y estáticas de tu reproducción actual de Plex. Perfecta para perfiles de GitHub, foros, webs y redes sociales.</p>
        <p><small>Basado en <a href="https://github.com/kittinan/spotify-github-profile" target="_blank">spotify-github-profile</a> de kittinan y los estilos de barras de <a href="https://github.com/novatorem/novatorem" target="_blank">Novatorem</a>. Originalmente creado para GitHub, pero expandido para múltiples usos.</small></p>
        
        <div class="card">
            <h2>📊 Estado del Sistema</h2>
            <div id="status">Verificando...</div>
        </div>
        
        <div class="card">
            <h2>🔧 Uso en GitHub</h2>
            <p>Añade esto a tu <code>README.md</code> del perfil:</p>
            <pre><code>![Music2Signature](''' + request.url_root + '''api/now-playing)</code></pre>
        </div>
        
        <div class="card">
            <h3>Diseños disponibles</h3>
            
                    <div style="margin: 2px 0;">
                        <p style="margin: 2px 0;"><strong>Transparent Dark</strong> - Fondo blanco sólido con letras oscuras para fondos oscuros</p>
                        <img src="/api/now-playing-svg?theme=transparent-dark&height=90" alt="Transparent Dark" style="max-width: 400px;" />
                        <br><small><a href="/api/now-playing-svg?theme=transparent-dark&height=90">Ver enlace directo</a></small>
                    </div>

                    <div style="margin: 2px 0;">
                        <p style="margin: 2px 0;"><strong>Transparent Light</strong> - Fondo oscuro sólido con letras blancas para fondos claros</p>
                        <img src="/api/now-playing-svg?theme=transparent-light&height=90" alt="Transparent Light" style="max-width: 400px;" />
                        <br><small><a href="/api/now-playing-svg?theme=transparent-light&height=90">Ver enlace directo</a></small>
                    </div>

                    <div style="margin: 2px 0;">
                        <p style="margin: 2px 0;"><strong>Light</strong> - Tema claro con ecualizador animado</p>
                        <img src="/api/now-playing-svg?theme=normal&height=90" alt="Light" style="max-width: 400px;" />
                        <br><small><a href="/api/now-playing-svg?theme=normal&height=90">Ver enlace directo</a></small>
                    </div>
            
                <div style="margin: 2px 0;">
                    <p style="margin: 2px 0;"><strong>Dark</strong> - Tema oscuro con ecualizador animado</p>
                    <img src="/api/now-playing-svg?theme=dark&height=90" alt="Dark" style="max-width: 400px;" />
                    <br><small><a href="/api/now-playing-svg?theme=dark&height=90">Ver enlace directo</a></small>
                </div>
        </div>
        
        <script>
            fetch('/api/status')
                .then(r => r.json())
                .then(data => {
                    const statusDiv = document.getElementById('status');
                    let html = '';
                    
                    if (data.plex.connected) {
                        html += '<div class="success">✅ Plex: Conectado (' + data.plex.server_name + ')</div>';
                    } else {
                        html += '<div class="error">❌ Plex: ' + (data.plex.error || 'No conectado') + '</div>';
                    }
                    
                    // Imgur eliminado
                    
                    if (data.current_session) {
                        html += '<div class="success">🎵 Reproduciendo: ' + data.current_session.title + '</div>';
                    } else {
                        html += '<div class="warning">⏸️ No hay reproducción activa</div>';
                    }
                    
                    statusDiv.innerHTML = html;
                })
                .catch(e => {
                    document.getElementById('status').innerHTML = '<div class="error">❌ Error obteniendo estado</div>';
                });
        </script>
    </body>
    </html>
    '''


@app.route('/api/status')
def api_status():
    """Endpoint para verificar el estado del sistema"""
    # Obtener token de parámetro de consulta o variable de entorno
    token = request.args.get('token')
    plex_client = create_plex_client(token)
    status = {
        'plex': {
            'connected': False,
            'server_name': None,
            'error': None
        },
        'current_session': None,
        'cache': {
            'last_update': image_cache['last_update'].isoformat() if image_cache['last_update'] else None,
            'has_cached_image': image_cache['image_url'] is not None
        }
    }
    
    if plex_client and plex_client.is_connected():
        server_info = plex_client.get_server_info()
        status['plex']['connected'] = True
        status['plex']['server_name'] = server_info.get('name', 'Unknown')
        status['plex']['sessions_count'] = server_info.get('sessions_count', 0)
        
        # Obtener sesión actual
        session_data = plex_client.get_current_session()
        if session_data:
            status['current_session'] = {
                'title': session_data.get('title'),
                'type': session_data.get('type'),
                'state': session_data.get('state'),
                'user': session_data.get('user')
            }
    else:
        status['plex']['error'] = 'No se pudo conectar'
    
    return jsonify(status)


@app.route('/api/now-playing')
def api_now_playing():
    """Endpoint principal que genera y devuelve la imagen de reproducción actual"""
    try:
        # Parámetros de la petición
        theme = request.args.get('theme', os.getenv('DEFAULT_THEME', 'normal'))
        width = int(request.args.get('width', os.getenv('IMAGE_WIDTH', 400)))
        height = int(request.args.get('height', 90))  # Forzado a 90, ignorando IMAGE_HEIGHT
        force_refresh = request.args.get('refresh', 'false').lower() == 'true'
        
        # Obtener datos de Plex
        token = request.args.get('token')
        plex_client = create_plex_client(token)
        if not plex_client:
            logger.error("No se pudo crear cliente de Plex")
            return generate_error_image("Error: Plex no configurado")

        # Obtener usuario específico si está configurado
        allowed_user = request.args.get('user')
        session_data = plex_client.get_current_session(allowed_user)
        logger.info(f"Datos de sesión obtenidos: {session_data}")

        # Si no hay sesión activa, intentar usar historial
        if not session_data:
            offset = int(time.time() // 30) % 5
            history_data = plex_client.get_recent_playback_history(allowed_user, limit=25, offset=offset)
            logger.info(f"Historial obtenido: {history_data}")
            if history_data:
                logger.info("No hay sesión activa, usando historial de reproducciones")
                session_data = history_data
            else:
                logger.info("No hay sesión activa, historial ni cache, generando imagen de 'sin actividad'")
                session_data = None

        # Clave de caché (solo para logging)
        cache_key = f"now_playing:{token}:{allowed_user}:{theme}:{width}:{height}"
        cached_image = None

        # Verificar cache en memoria
        if image_cache.get('image_url') and image_cache.get('last_update'):
            elapsed = (datetime.now() - image_cache['last_update']).total_seconds()
            if elapsed < CACHE_DURATION:
                cached_image = image_cache['image_url']

        if cached_image:
            logger.info("Devolviendo imagen desde caché en memoria")
            resp = Response(cached_image, mimetype='image/svg+xml')
            # Evitar que los proxies/navegadores cacheen indefinidamente
            resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            return resp

        # Ahora devolvemos SVG en lugar de PNG
        svg_generator = SVGGenerator(width, height, theme)
        try:
            svg_content = svg_generator.generate_now_playing_svg(session_data)
        except Exception as e:
            logger.error(f"Error generando contenido SVG: {e}")
            return generate_error_image(f"Error: {str(e)}")

        # inject version/timestamp comment (no debe romper la ejecución si git falla)
        try:
            import subprocess
            git_hash = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode().strip()
        except Exception:
            git_hash = 'unknown'

        svg_content = svg_content.replace('<svg', f'<!-- version:{git_hash} ts:{int(time.time())} --><svg', 1)
        resp = Response(svg_content, mimetype='image/svg+xml')
        resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        resp.headers['X-SVG-Version'] = git_hash
        return resp
    except Exception as e:
        logger.error(f"Error en api_now_playing: {e}")
        return generate_error_image(f"Error: {str(e)}")


def generate_error_image(message: str) -> Response:
    """Genera imagen de error"""
    try:
        # Generar un SVG de error en lugar de PNG
        return generate_error_svg(message)
    except Exception as e:
        logger.error(f"Error generando imagen de error: {e}")
        return Response("Error", mimetype='text/plain', status=500)


def generate_error_svg(message: str) -> Response:
    """Genera SVG de error"""
    try:
        svg_content = f'''
        <svg width="400" height="90" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <style>
                    .error-text {{
                        font-family: Arial, sans-serif;
                        fill: #ff4444;
                        font-size: 14px;
                        text-anchor: middle;
                    }}
                </style>
            </defs>
            <text x="200" y="80" class="error-text">{message}</text>
        </svg>
        '''
        return Response(svg_content, mimetype='image/svg+xml')
    except Exception as e:
        logger.error(f"Error generando SVG de error: {e}")
        return Response("Error SVG", mimetype='text/plain', status=500)


@app.route('/api/now-playing-svg')
def api_now_playing_svg():
    """Endpoint que genera y devuelve SVG animado de reproducción actual"""
    try:
        # Parámetros de la petición
        theme = request.args.get('theme', os.getenv('DEFAULT_THEME', 'normal'))
        width = int(request.args.get('width', os.getenv('IMAGE_WIDTH', 400)))
        height = int(request.args.get('height', 90))  # Forzado a 90, ignorando IMAGE_HEIGHT
        
        # Obtener datos de Plex
        token = request.args.get('token')
        plex_client = create_plex_client(token)
        if not plex_client:
            logger.error("No se pudo crear cliente de Plex")
            return generate_error_svg("Error: Plex no configurado")
        
        # Obtener usuario específico si está configurado
        allowed_user = request.args.get('user')
        session_data = plex_client.get_current_session(allowed_user)
        logger.info(f"Datos de sesión obtenidos para SVG: {session_data}")
        
        # Si no hay sesión activa, intentar usar historial
        if not session_data:
            offset = int(time.time() // 30) % 5  # Alternar entre 0-4 cada 30 segundos
            history_data = plex_client.get_recent_playback_history(allowed_user, limit=25, offset=offset)
            logger.info(f"Historial obtenido: {history_data}")
            if history_data:
                logger.info("No hay sesión activa, usando historial de reproducciones para SVG")
                session_data = history_data
            else:
                logger.info("No hay sesión activa, historial ni cache, generando SVG de 'sin actividad'")
                session_data = None
        
        # Allow forcing fresh generation by passing refresh=true
        force_refresh = request.args.get('refresh', 'false').lower() == 'true'

        # Generar SVG
        svg_generator = SVGGenerator(width, height, theme)
        svg_content = svg_generator.generate_now_playing_svg(session_data)

        logger.info("SVG generado exitosamente")
        try:
            import subprocess
            git_hash = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode().strip()
        except Exception:
            git_hash = 'unknown'
        svg_content = svg_content.replace('<svg', f'<!-- version:{git_hash} ts:{int(time.time())} --><svg', 1)
        resp = Response(svg_content, mimetype='image/svg+xml')
        # Ensure clients and CDNs get fresh content when requested
        if force_refresh:
            resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        else:
            # still recommend short caching for typical requests
            resp.headers['Cache-Control'] = 'public, max-age=5, must-revalidate'
        resp.headers['X-SVG-Version'] = git_hash
        return resp

    except Exception as e:
        logger.error(f"Error generando SVG: {e}")
        return generate_error_svg(f"Error: {str(e)}")


@app.route('/api/now-playing-png')
def api_now_playing_png():
    """Endpoint que genera y devuelve PNG estático de reproducción actual"""
    try:
        # Parámetros de la petición
        theme = request.args.get('theme', os.getenv('DEFAULT_THEME', 'normal'))
        width = int(request.args.get('width', os.getenv('IMAGE_WIDTH', 400)))
        height = int(request.args.get('height', 90))  # Forzado a 90, ignorando IMAGE_HEIGHT
        
        # Obtener cliente Plex
        token = request.args.get('token')
        plex_client = create_plex_client(token)
        if not plex_client:
            logger.error("No se pudo crear cliente Plex")
            return "Error: No se pudo conectar a Plex", 500
        
        # Obtener sesión actual
        allowed_user = request.args.get('user')
        session_data = plex_client.get_current_session(allowed_user)
        logger.info(f"Datos de sesión obtenidos para PNG: {session_data}")
        
        # Si no hay sesión activa, intentar usar historial
        if not session_data:
            offset = int(time.time() // 30) % 5  # Alternar entre 0-4 cada 30 segundos
            history_data = plex_client.get_recent_playback_history(allowed_user, limit=25, offset=offset)
            logger.info(f"PNG: Historial obtenido: {history_data}")
            if history_data:
                logger.info("No hay sesión activa, usando historial de reproducciones para PNG")
                session_data = history_data
            else:
                logger.info("No hay sesión activa, historial ni cache, generando PNG de 'sin actividad'")
                session_data = None
        # Este endpoint ya no devuelve PNG; devolvemos SVG
        svg_generator = SVGGenerator(width, height, theme)
        svg_content = svg_generator.generate_now_playing_svg(session_data)
        return Response(svg_content, mimetype='image/svg+xml')
    except Exception as e:
        logger.error(f"Error generando PNG (ahora retorna SVG): {e}")
        return generate_error_svg(f"Error: {str(e)}")


@app.route('/api/cache/clear')
def api_clear_cache():
    """Endpoint para limpiar el cache manualmente"""
    global image_cache
    try:
        image_cache = {
            'last_update': None,
            'image_url': None,
            'session_data': None,
            'cache_duration': CACHE_DURATION
        }
        logger.info("Cache en memoria limpiado")
        return jsonify({'success': True, 'message': 'Cache en memoria limpiado'})
    except Exception as e:
        logger.exception("Error limpiando cache en memoria: %s", e)
        return jsonify({'success': False, 'message': str(e)}), 500


# Nota: El endpoint para convertir SVG a PNG se eliminó. La aplicación sirve sólo SVG.


if __name__ == '__main__':
    # Verificar configuración
    if not os.getenv('PLEX_URL') or not os.getenv('PLEX_TOKEN'):
        logger.error("⚠️  Faltan variables de entorno PLEX_URL y/o PLEX_TOKEN")
        logger.info("💡 Copia .env.example a .env y configura tus credenciales")
    
    # Imgur eliminado: no se requiere advertencia
    
    # Ejecutar aplicación
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'false').lower() == 'true'
    
    logger.info(f"🚀 Iniciando Music2Signature en puerto {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)
