"""
Music2Signature - Aplicación principal
Muestra lo que estás reproduciendo en Plex en tu perfil de GitHub y firmas web
"""
import os
import time
import json
import logging
import hashlib
from dotenv import load_dotenv
from flask import Flask, Response, request, jsonify
from api.plex_client import create_plex_client
from api.svg_generator import SVGGenerator, _escape_xml

# Cargar variables de entorno
load_dotenv()

# Configurar logging
DEBUG_MODE = os.getenv('DEBUG', 'false').lower() == 'true'
logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# Crear aplicación Flask
app = Flask(__name__)

# Configuración de cache
CACHE_DURATION = int(os.getenv('CACHE_DURATION', 60))


class CacheManager:
    """Gestor de caché en memoria de alto rendimiento con expiración por TTL."""
    def __init__(self, default_ttl=60, max_entries=150):
        self.default_ttl = default_ttl
        self._cache = {}  # key -> {'data': ..., 'expires_at': ..., 'created_at': ...}
        self._max_entries = max_entries

    def get(self, key: str):
        entry = self._cache.get(key)
        if entry:
            if time.time() < entry['expires_at']:
                return entry['data']
            self._cache.pop(key, None)
        return None

    def set(self, key: str, value: str, ttl: int = None):
        ttl = ttl if ttl is not None else self.default_ttl
        if len(self._cache) >= self._max_entries:
            oldest_k = min(self._cache.keys(), key=lambda k: self._cache[k]['created_at'])
            self._cache.pop(oldest_k, None)

        now = time.time()
        self._cache[key] = {
            'data': value,
            'expires_at': now + ttl,
            'created_at': now
        }

    def clear(self):
        cleared_count = len(self._cache)
        self._cache.clear()
        return {'cleared_items': cleared_count}

    def get_stats(self):
        now = time.time()
        valid_items = sum(1 for e in self._cache.values() if e['expires_at'] > now)
        return {
            'backend': 'memory',
            'active_items': valid_items
        }


# Instancia global del gestor de caché
cache_mgr = CacheManager(default_ttl=CACHE_DURATION)


def _resolve_git_hash() -> str:
    """Resuelve la versión o hash de git una sola vez al iniciar la aplicación."""
    env_hash = os.getenv('VERCEL_GIT_COMMIT_SHA') or os.getenv('GIT_COMMIT')
    if env_hash:
        return env_hash[:7]
    try:
        import subprocess
        return subprocess.check_output(
            ['git', 'rev-parse', '--short', 'HEAD'],
            stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception:
        return 'prod'


GIT_HASH = _resolve_git_hash()


def generate_error_svg(message: str) -> Response:
    """Genera una respuesta SVG de error válida y segura frente a inyección XML."""
    try:
        esc_msg = _escape_xml(message)
        svg_content = f'''<svg width="400" height="90" viewBox="0 0 400 90" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <style>
            .error-bg {{ fill: #161b22; }}
            .error-text {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
                fill: #ff5555;
                font-size: 13px;
                text-anchor: middle;
            }}
        </style>
    </defs>
    <rect class="error-bg" width="100%" height="100%" rx="8" />
    <text x="200" y="50" class="error-text">{esc_msg}</text>
</svg>'''
        resp = Response(svg_content, mimetype='image/svg+xml; charset=utf-8')
        resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        return resp
    except Exception as e:
        logger.error(f"Error generando SVG de error: {e}")
        return Response("Error SVG", mimetype='text/plain; charset=utf-8', status=500)


@app.route('/')
def index():
    """Página principal con información del proyecto y previsualización de temas."""
    return '''<!DOCTYPE html>
<html lang="es">
<head>
    <title>Music2Signature</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            max-width: 860px; margin: 36px auto; padding: 0 16px;
            background: #0d1117; color: #f0f6fc;
            line-height: 1.5;
        }
        h1, h2, h3 { color: #f0f6fc; font-weight: 600; margin-top: 0; }
        h1 { font-size: 1.85rem; margin-bottom: 6px; letter-spacing: -0.02em; }
        .subtitle { color: #8b949e; font-size: 0.98rem; margin-bottom: 24px; }
        
        .card {
            background: #161b22; border-radius: 10px; padding: 22px; margin: 18px 0;
            border: 1px solid #30363d;
            box-shadow: 0 2px 8px rgba(0,0,0,0.25);
        }
        .card-header {
            display: flex; align-items: center; justify-content: space-between;
            margin-bottom: 14px;
        }
        .card-header h2 { margin-bottom: 0; font-size: 1.2rem; }
        
        /* Dashboard Tiles */
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 14px;
        }
        .status-tile {
            background: #0d1117;
            border: 1px solid #21262d;
            border-radius: 8px;
            padding: 14px 16px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            min-height: 94px;
        }
        .tile-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 8px;
            margin-bottom: 8px;
        }
        .tile-label {
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: #8b949e;
            font-weight: 600;
            white-space: nowrap;
        }
        .tile-value {
            font-size: 1.05rem;
            font-weight: 600;
            color: #f0f6fc;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .tile-sub {
            font-size: 0.82rem;
            color: #8b949e;
            margin-top: 4px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        
        /* Badges */
        .badge {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            font-size: 0.72rem;
            font-weight: 500;
            text-transform: none;
            letter-spacing: normal;
            padding: 2px 9px;
            border-radius: 9999px;
            white-space: nowrap;
            flex-shrink: 0;
            line-height: 1.35;
        }
        .badge-dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            display: inline-block;
        }
        .badge-success {
            background: rgba(46, 160, 67, 0.15);
            color: #3fb950;
            border: 1px solid rgba(46, 160, 67, 0.35);
        }
        .badge-success .badge-dot {
            background: #3fb950;
            box-shadow: 0 0 4px rgba(63, 185, 80, 0.6);
        }
        .badge-error {
            background: rgba(248, 81, 73, 0.15);
            color: #f85149;
            border: 1px solid rgba(248, 81, 73, 0.35);
        }
        .badge-error .badge-dot {
            background: #f85149;
        }
        .badge-neutral {
            background: rgba(110, 118, 129, 0.15);
            color: #8b949e;
            border: 1px solid rgba(110, 118, 129, 0.28);
        }
        .badge-neutral .badge-dot {
            background: #8b949e;
        }
        .dot {
            width: 7px; height: 7px; border-radius: 50%;
            display: inline-block;
        }
        .dot-pulse {
            background: #3fb950;
            box-shadow: 0 0 0 0 rgba(63, 185, 80, 0.7);
            animation: pulse-ring 2s infinite;
        }
        @keyframes pulse-ring {
            0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(63, 185, 80, 0.7); }
            70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(63, 185, 80, 0); }
            100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(63, 185, 80, 0); }
        }
        
        .refresh-indicator {
            font-size: 0.78rem;
            color: #8b949e;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        /* Code blocks */
        code { background: #21262d; padding: 2px 6px; border-radius: 4px; color: #f0f6fc; font-size: 0.9em; }
        pre code { display: block; padding: 12px; overflow-x: auto; font-family: ui-monospace, SFMono-Regular, Consolas, monospace; }
        a { color: #58a6ff; text-decoration: none; }
        a:hover { text-decoration: underline; }
        
        /* Themes preview grid */
        .themes-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
            gap: 16px;
            margin-top: 12px;
        }
        .theme-item {
            background: #0d1117;
            border: 1px solid #21262d;
            border-radius: 8px;
            padding: 16px;
            display: flex;
            flex-direction: column;
        }
        .theme-item-header {
            display: flex; align-items: center; justify-content: space-between;
            margin-bottom: 6px;
        }
        .theme-name { font-weight: 600; font-size: 0.95rem; color: #f0f6fc; }
        .theme-desc {
            font-size: 0.82rem;
            color: #8b949e;
            margin-bottom: 12px;
            min-height: 24px;
            line-height: 1.4;
            display: flex;
            align-items: center;
        }
        .preview-img {
            max-width: 100%;
            border-radius: 6px;
            display: block;
            margin-top: auto;
        }
    </style>
</head>
<body>
    <h1>Music2Signature</h1>
    <div class="subtitle">Servicio de generación de tarjetas SVG dinámicas para Plex Media Server.</div>

    <div class="card">
        <div class="card-header">
            <h2>Estado del sistema</h2>
            <div class="refresh-indicator">
                <span class="dot dot-pulse"></span>
                <span id="last-update">Actualizando...</span>
            </div>
        </div>
        
        <div class="status-grid" id="status-grid">
            <div class="status-tile">
                <div class="tile-header">
                    <span class="tile-label">Servidor Plex</span>
                    <span class="badge badge-neutral"><span class="badge-dot"></span>Conectando</span>
                </div>
                <div class="tile-value">Comprobando conexión...</div>
                <div class="tile-sub">Consultando API de Plex</div>
            </div>
            <div class="status-tile">
                <div class="tile-header">
                    <span class="tile-label">Reproducción</span>
                    <span class="badge badge-neutral"><span class="badge-dot"></span>Inactivo</span>
                </div>
                <div class="tile-value">-</div>
                <div class="tile-sub">-</div>
            </div>
            <div class="status-tile">
                <div class="tile-header">
                    <span class="tile-label">Caché y Runtime</span>
                    <span class="badge badge-neutral">Memoria</span>
                </div>
                <div class="tile-value">-</div>
                <div class="tile-sub">-</div>
            </div>
        </div>
    </div>

    <div class="card">
        <h2>Uso en GitHub</h2>
        <p style="color: #8b949e; font-size: 0.9rem; margin-top: 0;">Añade la siguiente etiqueta a tu <code>README.md</code> para mostrar lo que estás escuchando:</p>
        <pre><code>![Music2Signature](''' + request.url_root + '''api/now-playing)</code></pre>
    </div>

    <div class="card">
        <h2>Diseños disponibles</h2>
        <div class="themes-grid">
            <div class="theme-item">
                <div class="theme-item-header">
                    <span class="theme-name">Transparent Light</span>
                    <a href="/api/now-playing-svg?theme=transparent-light&height=90" target="_blank" style="font-size: 0.8rem;">Enlace directo</a>
                </div>
                <div class="theme-desc">Fondo transparente con tipografía clara.</div>
                <img src="/api/now-playing-svg?theme=transparent-light&height=90" alt="Transparent Light" class="preview-img" data-theme="transparent-light" />
            </div>

            <div class="theme-item">
                <div class="theme-item-header">
                    <span class="theme-name">Transparent Dark</span>
                    <a href="/api/now-playing-svg?theme=transparent-dark&height=90" target="_blank" style="font-size: 0.8rem;">Enlace directo</a>
                </div>
                <div class="theme-desc">Fondo transparente con tipografía oscura.</div>
                <img src="/api/now-playing-svg?theme=transparent-dark&height=90" alt="Transparent Dark" class="preview-img" data-theme="transparent-dark" />
            </div>

            <div class="theme-item">
                <div class="theme-item-header">
                    <span class="theme-name">Dark</span>
                    <a href="/api/now-playing-svg?theme=dark&height=90" target="_blank" style="font-size: 0.8rem;">Enlace directo</a>
                </div>
                <div class="theme-desc">Fondo oscuro sólido con acentos de color.</div>
                <img src="/api/now-playing-svg?theme=dark&height=90" alt="Dark" class="preview-img" data-theme="dark" />
            </div>

            <div class="theme-item">
                <div class="theme-item-header">
                    <span class="theme-name">Normal (Light)</span>
                    <a href="/api/now-playing-svg?theme=normal&height=90" target="_blank" style="font-size: 0.8rem;">Enlace directo</a>
                </div>
                <div class="theme-desc">Fondo blanco sólido con tipografía oscura.</div>
                <img src="/api/now-playing-svg?theme=normal&height=90" alt="Light" class="preview-img" data-theme="normal" />
            </div>
        </div>
    </div>

    <script>
        function updateStatus() {
            fetch('/api/status')
                .then(r => r.json())
                .then(data => {
                    const grid = document.getElementById('status-grid');
                    const lastUpdate = document.getElementById('last-update');
                    const now = new Date().toLocaleTimeString();
                    lastUpdate.textContent = 'En vivo · ' + now;

                    let serverHtml = '';
                    if (data.plex && data.plex.connected) {
                        const sName = data.plex.server_name || 'Servidor activo';
                        const sessions = data.plex.sessions_count || 0;
                        serverHtml = `
                            <div class="tile-header">
                                <span class="tile-label">Servidor Plex</span>
                                <span class="badge badge-success"><span class="badge-dot"></span>Conectado</span>
                            </div>
                            <div class="tile-value">${escapeHtml(sName)}</div>
                            <div class="tile-sub">${sessions} ${sessions === 1 ? 'sesión activa' : 'sesiones activas'}</div>
                        `;
                    } else {
                        const err = (data.plex && data.plex.error) || 'Sin conexión';
                        serverHtml = `
                            <div class="tile-header">
                                <span class="tile-label">Servidor Plex</span>
                                <span class="badge badge-error"><span class="badge-dot"></span>Desconectado</span>
                            </div>
                            <div class="tile-value">${escapeHtml(err)}</div>
                            <div class="tile-sub">Comprueba el token y la URL</div>
                        `;
                    }

                    let playbackHtml = '';
                    if (data.current_session && data.current_session.title) {
                        const title = data.current_session.title;
                        const artist = data.current_session.artist || '';
                        const album = data.current_session.album || '';
                        const meta = [artist, album].filter(Boolean).join(' - ') || 'Pista de audio';
                        playbackHtml = `
                            <div class="tile-header">
                                <span class="tile-label">Reproducción</span>
                                <span class="badge badge-success"><span class="badge-dot"></span>En reproducción</span>
                            </div>
                            <div class="tile-value" title="${escapeHtml(title)}">${escapeHtml(title)}</div>
                            <div class="tile-sub" title="${escapeHtml(meta)}">${escapeHtml(meta)}</div>
                        `;
                    } else {
                        playbackHtml = `
                            <div class="tile-header">
                                <span class="tile-label">Reproducción</span>
                                <span class="badge badge-neutral"><span class="badge-dot"></span>Inactivo</span>
                            </div>
                            <div class="tile-value">Sin reproducción activa</div>
                            <div class="tile-sub">Ondas animadas en reposo</div>
                        `;
                    }

                    const activeItems = (data.cache && (data.cache.active_items ?? data.cache.memory_active_items)) || 0;
                    const cacheHtml = `
                        <div class="tile-header">
                            <span class="tile-label">Caché y Runtime</span>
                            <span class="badge badge-neutral">Memoria</span>
                        </div>
                        <div class="tile-value">${activeItems} ${activeItems === 1 ? 'elemento en caché' : 'elementos en caché'}</div>
                        <div class="tile-sub">Versión: ${data.version || 'prod'}</div>
                    `;

                    grid.innerHTML = `
                        <div class="status-tile">${serverHtml}</div>
                        <div class="status-tile">${playbackHtml}</div>
                        <div class="status-tile">${cacheHtml}</div>
                    `;

                    // Refrescar las imágenes de previsualización solo si cambia la pista o estado
                    const trackKey = data.current_session ? (data.current_session.title + '::' + (data.current_session.artist || '')) : '__idle__';
                    if (currentPlaybackKey === null || currentPlaybackKey !== trackKey) {
                        currentPlaybackKey = trackKey;
                        const ts = Date.now();
                        document.querySelectorAll('.preview-img').forEach(img => {
                            const theme = img.getAttribute('data-theme');
                            img.src = '/api/now-playing-svg?theme=' + theme + '&height=90&_t=' + ts;
                        });
                    }
                })
                .catch(e => {
                    document.getElementById('last-update').textContent = 'Error de conexión';
                });
        }

        function escapeHtml(text) {
            if (!text) return '';
            const d = document.createElement('div');
            d.textContent = text;
            return d.innerHTML;
        }

        // Variable para controlar si la pista activa cambió
        let currentPlaybackKey = null;

        // Carga inicial y refresco cada 30 segundos
        updateStatus();
        setInterval(updateStatus, 30000);

        // Si el usuario regresa a la pestaña tras tenerla en segundo plano, refrescar
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                updateStatus();
            }
        });
    </script>
</body>
</html>'''


@app.route('/api/status')
def api_status():
    """Endpoint para verificar el estado de Plex y el sistema."""
    token = request.args.get('token')
    user = request.args.get('user')
    force_refresh = request.args.get('refresh', 'false').lower() == 'true'
    allow_video_arg = request.args.get('allow_video')
    if allow_video_arg is not None:
        allow_video = allow_video_arg.lower() in ('true', '1', 'yes')
    else:
        allow_video = os.getenv('ALLOW_VIDEO', 'false').lower() in ('true', '1', 'yes')

    token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()[:12] if token else 'default'
    status_cache_key = f"music2sig:status:{token_hash}:{user or 'any'}:{allow_video}"

    if not force_refresh:
        cached_status = cache_mgr.get(status_cache_key)
        if cached_status:
            try:
                return Response(cached_status, mimetype='application/json')
            except Exception:
                pass

    plex_client = create_plex_client(token)
    status = {
        'plex': {
            'connected': False,
            'server_name': None,
            'sessions_count': 0,
            'error': None
        },
        'current_session': None,
        'cache': cache_mgr.get_stats(),
        'version': GIT_HASH
    }

    if plex_client and plex_client.is_connected():
        server_info = plex_client.get_server_info()
        status['plex']['connected'] = True
        status['plex']['server_name'] = server_info.get('name', 'Unknown')
        status['plex']['sessions_count'] = server_info.get('sessions_count', 0)

        session_data = plex_client.get_current_session(user, allow_video=allow_video)
        if session_data:
            status['current_session'] = {
                'title': session_data.get('title'),
                'artist': session_data.get('artist'),
                'album': session_data.get('album'),
                'type': session_data.get('type'),
                'state': session_data.get('state'),
                'user': session_data.get('user')
            }
    else:
        status['plex']['error'] = 'No se pudo conectar al servidor Plex'

    # Guardar en caché corta (10 segundos) para mitigar consultas concurrentes
    try:
        cache_mgr.set(status_cache_key, json.dumps(status), ttl=10)
    except Exception:
        pass

    return jsonify(status)


@app.route('/api/now-playing')
@app.route('/api/now-playing-svg')
def api_now_playing_svg():
    """Endpoint principal que genera y devuelve el SVG animado de reproducción actual."""
    try:
        # Parámetros validados
        theme = request.args.get('theme', os.getenv('DEFAULT_THEME', 'normal'))

        try:
            width = int(request.args.get('width', os.getenv('IMAGE_WIDTH', 400)))
        except ValueError:
            width = 400
        width = max(200, min(1200, width))

        try:
            height = int(request.args.get('height', os.getenv('IMAGE_HEIGHT', 90)))
        except ValueError:
            height = 90
        height = max(40, min(600, height))

        force_refresh = request.args.get('refresh', 'false').lower() == 'true'
        idle_mode = request.args.get('idle', os.getenv('IDLE_MODE', 'bars')).strip().lower()
        
        marquee_arg = request.args.get('marquee')
        if marquee_arg is not None:
            marquee = marquee_arg.lower() not in ('false', '0', 'no')
        else:
            marquee = os.getenv('MARQUEE_ENABLED', 'true').strip().lower() not in ('false', '0', 'no')

        allow_video_arg = request.args.get('allow_video')
        if allow_video_arg is not None:
            allow_video = allow_video_arg.lower() in ('true', '1', 'yes')
        else:
            allow_video = os.getenv('ALLOW_VIDEO', 'false').lower() in ('true', '1', 'yes')

        token = request.args.get('token')
        allowed_user = request.args.get('user')
        color = request.args.get('color') or request.args.get('text_color')
        subcolor = request.args.get('subcolor') or request.args.get('artist_color')
        bar_color = request.args.get('bar_color')
        cover_dim = request.args.get('cover_dim')
        quality = request.args.get('quality')

        # Clave de caché segura (hash de token para evitar almacenar credenciales en memoria)
        token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()[:12] if token else 'default'
        cache_key = f"music2sig:svg:{token_hash}:{allowed_user or 'any'}:{theme}:{width}:{height}:{idle_mode}:{marquee}:{color or ''}:{subcolor or ''}:{bar_color or ''}:{cover_dim or ''}:{quality or ''}:{allow_video}"

        # Verificar caché si no se solicitó refresco forzado
        if not force_refresh:
            cached_svg = cache_mgr.get(cache_key)
            if cached_svg:
                resp = Response(cached_svg, mimetype='image/svg+xml; charset=utf-8')
                resp.headers['Cache-Control'] = 'public, max-age=5, must-revalidate'
                resp.headers['X-SVG-Version'] = GIT_HASH
                resp.headers['X-Cache'] = 'HIT'
                return resp

        # Crear cliente Plex
        plex_client = create_plex_client(token)
        if not plex_client or not plex_client.token:
            logger.warning("Solicitud recibida sin token de Plex configurado")
            return generate_error_svg("Error: Plex no configurado")

        # Obtener sesión actual en vivo
        session_data = plex_client.get_current_session(allowed_user, allow_video=allow_video)

        # Generar SVG (si no hay música activa, se aplica el modo idle: 'bars' o 'full')
        svg_generator = SVGGenerator(
            width, height, theme,
            text_color=color,
            subtext_color=subcolor,
            bar_color=bar_color,
            cover_max_dim=cover_dim,
            cover_quality=quality
        )
        svg_content = svg_generator.generate_now_playing_svg(session_data, idle_mode=idle_mode, marquee=marquee)

        # Inyectar comentario de versión y timestamp
        timestamp = int(time.time())
        svg_content = svg_content.replace(
            '<svg',
            f'<!-- version:{GIT_HASH} ts:{timestamp} --><svg',
            1
        )

        # Guardar en caché
        cache_mgr.set(cache_key, svg_content, ttl=CACHE_DURATION)

        resp = Response(svg_content, mimetype='image/svg+xml; charset=utf-8')
        if force_refresh:
            resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        else:
            resp.headers['Cache-Control'] = 'public, max-age=5, must-revalidate'
        resp.headers['X-SVG-Version'] = GIT_HASH
        resp.headers['X-Cache'] = 'MISS'
        return resp

    except Exception as e:
        logger.exception("Error inesperado en api_now_playing_svg: %s", e)
        return generate_error_svg(f"Error: {str(e)}")


@app.route('/api/now-playing-png')
def api_now_playing_png():
    """Ruta conservada para compatibilidad regresiva con clientes que enlazaban /api/now-playing-png."""
    return api_now_playing_svg()


@app.route('/api/cache/clear', methods=['GET', 'POST'])
def api_clear_cache():
    """Endpoint para limpiar la caché en memoria."""
    try:
        stats = cache_mgr.clear()
        logger.info("Caché limpiada manualmente: %s", stats)
        return jsonify({
            'success': True,
            'message': 'Caché limpiada exitosamente',
            'details': stats
        })
    except Exception as e:
        logger.exception("Error limpiando caché: %s", e)
        return jsonify({'success': False, 'message': str(e)}), 500


if __name__ == '__main__':
    # Verificar configuración al iniciar
    if not os.getenv('PLEX_TOKEN'):
        logger.warning("Falta variable de entorno PLEX_TOKEN")
        logger.info("Copia .env.example a .env y configura tus credenciales")

    port = int(os.getenv('PORT', 5000))
    logger.info(f"Iniciando Music2Signature en puerto {port} (DEBUG={DEBUG_MODE})")
    app.run(host='0.0.0.0', port=port, debug=DEBUG_MODE)
