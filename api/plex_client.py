"""
Music2Signature - Cliente Plex
Conexión, descubrimiento y sondeo del servidor Plex Media Server
"""
import os
import time
import logging
import requests
import plexapi
from plexapi.server import PlexServer
from plexapi.myplex import MyPlexAccount

logger = logging.getLogger(__name__)

# ==============================================================================
# Identidad estática y persistente para Plex
# ==============================================================================
# En entornos Serverless / Cloud (Vercel, AWS Lambda, Docker), cada contenedor
# efímero tiene una IP interna (169.254.x.x) y una MAC virtual aleatoria.
# Si no fijamos una identidad estática, PlexAPI genera un Client-Identifier y
# Device-Name nuevo por cada ejecución, disparando notificaciones de "Nuevo dispositivo"
# en los teléfonos y clientes del usuario.
DEFAULT_CLIENT_ID = 'music2signature-app-client'
DEFAULT_DEVICE_NAME = 'Music2Signature'
DEFAULT_PRODUCT = 'Music2Signature'
DEFAULT_PLATFORM = 'Web'

CLIENT_IDENTIFIER = os.getenv('PLEX_CLIENT_IDENTIFIER', DEFAULT_CLIENT_ID)
DEVICE_NAME = os.getenv('PLEX_DEVICE_NAME', DEFAULT_DEVICE_NAME)
PRODUCT_NAME = 'Music2Signature'
PLATFORM_NAME = 'Web'
VERSION_STR = '1.0.0'

# Configurar plexapi globalmente con identidad estática
plexapi.X_PLEX_IDENTIFIER = CLIENT_IDENTIFIER
plexapi.X_PLEX_PRODUCT = PRODUCT_NAME
plexapi.X_PLEX_VERSION = VERSION_STR
plexapi.X_PLEX_DEVICE = DEVICE_NAME
plexapi.X_PLEX_DEVICE_NAME = DEVICE_NAME
plexapi.X_PLEX_PLATFORM = PLATFORM_NAME
plexapi.X_PLEX_PLATFORM_VERSION = '1.0'
plexapi.X_PLEX_PROVIDES = 'controller'
plexapi.BASE_HEADERS = plexapi.reset_base_headers()

STATIC_PLEX_HEADERS = {
    'X-Plex-Platform': PLATFORM_NAME,
    'X-Plex-Platform-Version': '1.0',
    'X-Plex-Provides': 'controller',
    'X-Plex-Product': PRODUCT_NAME,
    'X-Plex-Version': VERSION_STR,
    'X-Plex-Device': DEVICE_NAME,
    'X-Plex-Device-Name': DEVICE_NAME,
    'X-Plex-Client-Identifier': CLIENT_IDENTIFIER,
    'X-Plex-Language': 'en',
    'X-Plex-Sync-Version': '2',
    'X-Plex-Features': 'external-media',
}

# Actualizar BASE_HEADERS in-place en todos los submódulos de plexapi (evita que copias importadas usen MAC aleatoria)
for _mod in (plexapi, getattr(plexapi, 'server', None), getattr(plexapi, 'myplex', None), getattr(plexapi, 'client', None)):
    if _mod and hasattr(_mod, 'BASE_HEADERS') and isinstance(_mod.BASE_HEADERS, dict):
        _mod.BASE_HEADERS.update(STATIC_PLEX_HEADERS)

def _patched_plex_headers(self, **kwargs):
    """Garantiza que toda llamada de PlexServer o MyPlexAccount envíe siempre la identidad persistente."""
    headers = STATIC_PLEX_HEADERS.copy()
    token = getattr(self, '_token', None)
    if token:
        headers['X-Plex-Token'] = token
    headers.update(kwargs)
    return headers

PlexServer._headers = _patched_plex_headers
MyPlexAccount._headers = _patched_plex_headers


def get_default_plex_headers(token=None, accept='application/json'):
    """Retorna las cabeceras estándar de identificación de dispositivo para Plex."""
    headers = {
        'Accept': accept,
        'X-Plex-Product': PRODUCT_NAME,
        'X-Plex-Version': VERSION_STR,
        'X-Plex-Client-Identifier': CLIENT_IDENTIFIER,
        'X-Plex-Platform': PLATFORM_NAME,
        'X-Plex-Platform-Version': '1.0',
        'X-Plex-Device': DEVICE_NAME,
        'X-Plex-Device-Name': DEVICE_NAME,
        'X-Plex-Provides': 'controller',
    }
    if token:
        headers['X-Plex-Token'] = token
    return headers


class PlexClient:
    _active_session_cache = {}    # key -> {'data': session_dict, 'ts': epoch}
    _SESSION_CACHE_TTL = 5        # segundos de caché para llamadas agrupadas
    _discovered_cache = {}        # token -> {'url': ..., 'resource': ..., 'owner': ..., 'server_version': ..., 'ts': ...}
    _DISCOVERY_TTL = 300          # 5 minutos para reusar autodescubrimiento
    _server_instance_cache = {}   # (token, url) -> PlexServer

    def __init__(self, token=None, url=None):
        self.token = token or os.getenv('PLEX_TOKEN')
        self.url = url or os.getenv('PLEX_URL')
        self.server = None
        self._resource = None
        self.server_version = None
        self.owner_username = os.getenv('PLEX_USER')

        if self.token:
            if not self.url:
                self._discover_server_and_owner()
            else:
                # Si tenemos URL pero no owner_username, intentar descubrirlo silenciosamente
                if not self.owner_username:
                    self._discover_owner_only()

            if self.url:
                cache_key = (self.token, self.url)
                cached_server = PlexClient._server_instance_cache.get(cache_key)
                if cached_server:
                    self.server = cached_server
                else:
                    try:
                        self.server = PlexServer(self.url, self.token, timeout=5)
                        PlexClient._server_instance_cache[cache_key] = self.server
                    except Exception as e:
                        self.server = None
                        logger.warning(f"Error conectando a PlexServer ({self.url}): {e}")

    def _discover_owner_only(self):
        """Intenta descubrir el nombre de usuario del propietario sin cambiar la URL configurada."""
        headers = get_default_plex_headers(self.token, accept='application/json')
        try:
            acct = requests.get('https://plex.tv/users/account', headers=headers, timeout=5)
            if acct.status_code == 200:
                try:
                    self.owner_username = acct.json().get('username')
                except ValueError:
                    try:
                        account = MyPlexAccount(token=self.token)
                        self.owner_username = account.username
                    except Exception:
                        pass
        except Exception as e:
            logger.debug(f"No se pudo obtener usuario propietario: {e}")

    def _discover_server_and_owner(self):
        """Descubre automáticamente el servidor Plex y el usuario propietario."""
        now = time.time()
        cached = PlexClient._discovered_cache.get(self.token)
        if cached and (now - cached.get('ts', 0)) < PlexClient._DISCOVERY_TTL:
            self.url = cached.get('url')
            self._resource = cached.get('resource')
            self.server_version = cached.get('server_version')
            self.owner_username = cached.get('owner')
            return

        headers = get_default_plex_headers(self.token, accept='application/json')
        logger.debug("Descubriendo servidores Plex vía plex.tv API...")
        try:
            resp = requests.get('https://plex.tv/api/v2/resources', headers=headers, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                first_server_resource = None
                fallback_local_url = None

                for resource in data:
                    if resource.get('provides') == 'server' and resource.get('connections'):
                        if not first_server_resource:
                            first_server_resource = resource

                        # Preferir conexión externa
                        for conn in resource['connections']:
                            uri = conn.get('uri')
                            if not uri:
                                continue
                            if conn.get('local') is False:
                                self.url = uri
                                break
                            elif not fallback_local_url:
                                fallback_local_url = uri

                        if self.url:
                            self._resource = resource
                            break

                # Si no se encontró conexión externa, usar la conexión local como fallback
                if not self.url and fallback_local_url:
                    self.url = fallback_local_url
                    self._resource = first_server_resource

                if self._resource:
                    self.server_version = (
                        self._resource.get('productVersion') or
                        self._resource.get('platformVersion') or
                        self._resource.get('version')
                    )
                    owner = self._resource.get('owner')
                    if owner and owner.get('username'):
                        self.owner_username = owner.get('username')

                if not self.owner_username:
                    self._discover_owner_only()

                if self._resource and self.url:
                    PlexClient._discovered_cache[self.token] = {
                        'url': self.url,
                        'resource': self._resource,
                        'server_version': self.server_version,
                        'owner': self.owner_username,
                        'ts': time.time()
                    }

            else:
                logger.debug(f"Respuesta no exitosa al descubrir servidores: {resp.status_code}")
        except Exception as e:
            logger.warning(f"Error descubriendo servidor Plex: {e}")

    def is_connected(self):
        return self.server is not None

    def get_server_info(self):
        if not self.server:
            name = None
            version = None
            sessions = 0
            if self._resource:
                name = self._resource.get('name')
                version = self.server_version
            return {'name': name, 'sessions_count': sessions, 'version': version}

        name = getattr(self.server, 'friendlyName', None)
        try:
            sessions = len(self.server.sessions())
        except Exception:
            sessions = 0
        try:
            version = (
                getattr(self.server, 'version', None) or
                getattr(self.server, 'productVersion', None) or
                getattr(self.server, 'platformVersion', None)
            )
        except Exception:
            version = None
        if not version:
            version = self.server_version
        return {'name': name, 'sessions_count': sessions, 'version': version}

    def _normalize_thumb_url(self, thumb):
        """Normaliza una ruta de miniatura a URL absoluta con token si es necesario."""
        if not thumb:
            return None
        if thumb.startswith(('http://', 'https://')):
            return thumb
        if not self.url:
            return None

        token = self._resource.get('accessToken') if self._resource else None
        token = token or self.token
        sep = '&' if '?' in thumb else '?'
        token_param = f"{sep}X-Plex-Token={token}" if token else ''
        return f"{self.url.rstrip('/')}{thumb}{token_param}"

    def get_current_session(self, user=None, force_refresh=False, allow_video=None):
        if not self.server:
            return None

        if allow_video is None:
            allow_video = os.getenv('ALLOW_VIDEO', 'false').strip().lower() in ('true', '1', 'yes')

        filter_user = (user or self.owner_username or '').strip().lower()
        cache_key = f"{self.token[-6:] if self.token else ''}:{filter_user or 'any'}:{allow_video}"

        if not force_refresh:
            cached = PlexClient._active_session_cache.get(cache_key)
            if cached and (time.time() - cached.get('ts', 0)) < PlexClient._SESSION_CACHE_TTL:
                return cached.get('data')

        try:
            sessions = self.server.sessions()
        except Exception as e:
            logger.warning(f"Error consultando sesiones activas de Plex: {e}")
            PlexClient._server_instance_cache.pop((self.token, self.url), None)
            return None

        if not sessions:
            PlexClient._active_session_cache[cache_key] = {'data': None, 'ts': time.time()}
            return None

        candidates = []
        for session in sessions:
            # Obtener nombre de usuario de la sesión de manera segura
            session_user = None
            user_attr = getattr(session, 'user', None)
            if user_attr:
                session_user = getattr(user_attr, 'title', None) or getattr(user_attr, 'name', None)
                if not session_user and not hasattr(user_attr, '__dict__'):
                    session_user = str(user_attr)
            if not session_user and hasattr(session, 'usernames') and session.usernames:
                session_user = session.usernames[0]

            # Si se especificó usuario, descartar si no coincide
            if filter_user:
                current_u = (session_user or '').strip().lower()
                if current_u != filter_user:
                    continue

            title = getattr(session, 'title', None)
            itype = (getattr(session, 'type', None) or '').lower()
            list_type = (getattr(session, 'listType', None) or '').lower()
            state = getattr(session, 'state', None)

            # Descartar sesiones que no sean música/audio (películas, series, clips, fotos)
            # Salvo que se configure explícitamente ALLOW_VIDEO=true
            if not allow_video:
                if itype in ('movie', 'episode', 'clip', 'video', 'trailer', 'photo', 'picture') or list_type == 'video':
                    continue
                if itype and itype not in ('track', 'song', 'audio'):
                    continue

            artist = getattr(session, 'grandparentTitle', None) or getattr(session, 'originalTitle', None) or None
            album = getattr(session, 'parentTitle', None) or None

            thumb = None
            for attr in ('thumb', 'parentThumb', 'grandparentThumb', 'art'):
                val = getattr(session, attr, None)
                if val:
                    thumb = val
                    break

            thumb_url = self._normalize_thumb_url(thumb)

            # Puntuación para elegir la mejor sesión en caso de múltiples reproducciones:
            score = 0
            if itype in ('track', 'song', 'audio') or artist:
                score += 10
            if state == 'playing':
                score += 5
            elif state == 'paused':
                score += 2

            item = {
                'title': title,
                'artist': artist,
                'album': album,
                'thumb': thumb_url,
                'type': itype or 'track',
                'state': state,
                'user': session_user
            }
            candidates.append((score, item))

        if not candidates:
            PlexClient._active_session_cache[cache_key] = {'data': None, 'ts': time.time()}
            return None

        # Ordenar por puntuación descendente y devolver la más relevante
        candidates.sort(key=lambda x: x[0], reverse=True)
        best_item = candidates[0][1]
        PlexClient._active_session_cache[cache_key] = {'data': best_item, 'ts': time.time()}
        return best_item


def create_plex_client(token=None, url=None):
    return PlexClient(token, url)

