
import os
import time
import requests
import xml.etree.ElementTree as ET
import random
import json
from plexapi.server import PlexServer
from plexapi.myplex import MyPlexAccount

try:
    import redis
    _REDIS_AVAILABLE = True
except Exception:
    _REDIS_AVAILABLE = False


class PlexClient:
    def __init__(self, token=None):
        self.token = token or os.getenv('PLEX_TOKEN')
        self.url = None
        self.server = None
        self._resource = None
        self.server_version = None
        self.owner_username = None

        # Historial cache
        self._history_cache = None  # {'items': [...], 'ts': epoch}
        self._history_ttl = int(os.getenv('HISTORY_CACHE_TTL', '60'))
        self._redis = None
        if _REDIS_AVAILABLE:
            try:
                redis_url = os.getenv('REDIS_URL')
                if redis_url:
                    self._redis = redis.Redis.from_url(redis_url)
            except Exception:
                self._redis = None

        if self.token:
            self._discover_server_and_owner()
            if self.url:
                try:
                    self.server = PlexServer(self.url, self.token)
                except Exception as e:
                    self.server = None
                    print(f"Error conectando a Plex: {e}")

    def _discover_server_and_owner(self):
        headers = {
            'Accept': 'application/json',
            'X-Plex-Token': self.token,
            'X-Plex-Client-Identifier': 'Music2Signature'
        }
        print(f"[DEBUG] Usando token: {self.token}")
        try:
            resp = requests.get('https://plex.tv/api/v2/resources', headers=headers, timeout=10)
            print(f"[DEBUG] Status code respuesta Plex: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                # Buscar el primer servidor con conexión externa
                for resource in data:
                    if resource.get('provides') == 'server' and resource.get('connections'):
                        for conn in resource['connections']:
                            if conn.get('uri') and conn.get('local') is False:
                                self.url = conn['uri']
                                break
                        if self.url:
                            self._resource = resource
                            self.server_version = resource.get('productVersion') or resource.get('platformVersion') or resource.get('version')
                            owner = resource.get('owner')
                            if owner and owner.get('username'):
                                self.owner_username = owner.get('username')
                                print(f"[DEBUG] Usuario propietario detectado (from resource): {self.owner_username}")
                            else:
                                # fallback: consultar /users/account
                                try:
                                    acct = requests.get('https://plex.tv/users/account', headers=headers, timeout=10)
                                    if acct.status_code == 200:
                                        try:
                                            acct_json = acct.json()
                                            self.owner_username = acct_json.get('username')
                                            print(f"[DEBUG] Usuario propietario detectado (from account): {self.owner_username}")
                                        except ValueError:
                                            try:
                                                account = MyPlexAccount(token=self.token)
                                                self.owner_username = account.username
                                                print(f"[DEBUG] Usuario propietario detectado (from MyPlexAccount): {self.owner_username}")
                                            except Exception as e:
                                                print(f"[DEBUG] MyPlexAccount fallback falló: {e}")
                                except Exception as e:
                                    print(f"[DEBUG] No se pudo obtener usuario desde /users/account: {e}")
                            break
            else:
                print(f"[DEBUG] Respuesta no exitosa de Plex: {resp.text}")
        except Exception as e:
            print(f"Error descubriendo servidor Plex: {e}")

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
            version = getattr(self.server, 'version', None) or getattr(self.server, 'productVersion', None) or getattr(self.server, 'platformVersion', None)
        except Exception:
            version = None
        if not version:
            version = self.server_version
        return {'name': name, 'sessions_count': sessions, 'version': version}

    def get_current_session(self, user=None):
        if not self.server:
            return None
        sessions = self.server.sessions()
        filter_user = user or self.owner_username
        for session in sessions:
            session_user = getattr(session.user, 'title', None)
            if filter_user and session_user != filter_user:
                continue

            # Intentar extraer metadata común: artist (grandparentTitle), album (parentTitle), thumb
            title = getattr(session, 'title', None)
            itype = getattr(session, 'type', None)
            state = getattr(session, 'state', None)
            artist = getattr(session, 'grandparentTitle', None) or getattr(session, 'originalTitle', None) or None
            album = getattr(session, 'parentTitle', None) or None
            # thumb puede estar en varias propiedades
            thumb = None
            for attr in ('thumb', 'parentThumb', 'grandparentThumb', 'art'):
                val = getattr(session, attr, None)
                if val:
                    thumb = val
                    break
            # Normalizar thumb a URL completa si es relativo
            token = self._resource.get('accessToken') if self._resource else None
            token = token or self.token
            if thumb and not thumb.startswith('http') and self.url:
                thumb = self.url.rstrip('/') + thumb + (f"?X-Plex-Token={token}" if token else '')

            return {
                'title': title,
                'artist': artist,
                'album': album,
                'thumb': thumb,
                'type': itype,
                'state': state,
                'user': session_user
            }
        return None

    def get_recent_playback_history(self, user=None, limit=25, offset=0):
        """
        Obtener historial reciente de reproducción (solo música).
        Devuelve un único elemento (dict) con claves: title, artist, user, thumb, type, state
        """
        if not self.url:
            return None

        token = self._resource.get('accessToken') if self._resource else None
        token = token or self.token

        cache_key = f"music2sig:history:{user or self.owner_username or 'unknown'}"

        # intentar leer cache (redis -> memoria)
        try:
            if self._redis:
                cached = self._redis.get(cache_key)
                if cached:
                    items = json.loads(cached)
                    if items:
                        print(f"[CACHE-HIT][redis] {cache_key} ({len(items)} items)")
                        if offset is None or (isinstance(offset, str) and offset.lower() == 'random'):
                            idx = random.randrange(len(items))
                        elif isinstance(offset, int) or (isinstance(offset, str) and offset.isdigit()):
                            idx = int(offset) % len(items)
                        else:
                            idx = random.randrange(len(items))
                        return items[idx]
            if self._history_cache:
                ts = self._history_cache.get('ts', 0)
                if int(time.time()) - ts < self._history_ttl:
                    items = self._history_cache.get('items') or []
                    if items:
                        print(f"[CACHE-HIT][mem] {cache_key} ({len(items)} items)")
                        if offset is None or (isinstance(offset, str) and offset.lower() == 'random'):
                            idx = random.randrange(len(items))
                        elif isinstance(offset, int) or (isinstance(offset, str) and offset.isdigit()):
                            idx = int(offset) % len(items)
                        else:
                            idx = random.randrange(len(items))
                        return items[idx]
        except Exception:
            pass

        # Reutilizar la nueva función que devuelve la lista completa
        items = self.get_recent_playback_list(user=user, limit=limit)
        if not items:
            return None

        # seleccionar item según offset/aleatorio
        try:
            if offset is None or (isinstance(offset, str) and offset.lower() == 'random'):
                idx = random.randrange(len(items))
            elif isinstance(offset, int) or (isinstance(offset, str) and offset.isdigit()):
                idx = int(offset) % len(items)
            else:
                idx = random.randrange(len(items))
        except Exception:
            idx = random.randrange(len(items))
        return items[idx]

    def get_recent_playback_list(self, user=None, limit=25):
        """
        Devuelve la lista completa normalizada de items de historial (no selecciona uno).
        Cada item es un dict con: title, artist, album, user, thumb, type, state
        """
        if not self.url:
            return []

        token = self._resource.get('accessToken') if self._resource else None
        token = token or self.token

        candidates = ['/status/sessions/history/all', '/system/history/all', '/library/recentlyViewed', '/library/recentlyViewedItems', '/library/recentlyViewedItems?type=10']
        headers = {'Accept': 'application/xml'}
        params = {'X-Plex-Token': token, 'limit': limit, 'type': 10}
        items = []
        for ep in candidates:
            try:
                url = self.url.rstrip('/') + ep
                resp = requests.get(url, headers=headers, params=params, timeout=8)
                if resp.status_code != 200:
                    continue
                text = resp.text.strip()
                if text.startswith('<'):
                    try:
                        root = ET.fromstring(text)
                    except Exception:
                        continue
                    for child in root:
                        attrib = child.attrib
                        itype = attrib.get('type', '').lower()
                        is_music = itype in ('track', 'song', 'audio') or ('grandparentTitle' in attrib)
                        if not is_music:
                            continue
                        title = attrib.get('title') or attrib.get('originalTitle')
                        artist = attrib.get('grandparentTitle') or ''
                        album = attrib.get('parentTitle') or ''
                        thumb = attrib.get('thumb')
                        if thumb and not thumb.startswith('http'):
                            thumb = self.url.rstrip('/') + thumb + (f"?X-Plex-Token={token}" if token else '')
                        items.append({'title': title, 'artist': artist, 'album': album, 'user': user or self.owner_username, 'thumb': thumb, 'type': itype or 'track', 'state': 'stopped'})
                        if len(items) >= limit:
                            break
                    if items:
                        break
                else:
                    try:
                        data = resp.json()
                    except Exception:
                        continue
                    candidates_list = data if isinstance(data, list) else data.get('items') or data.get('MediaContainer') or []
                    for entry in candidates_list:
                        if not isinstance(entry, dict):
                            continue
                        itype = (entry.get('type') or '').lower()
                        is_music = itype in ('track', 'song', 'audio') or entry.get('grandparentTitle')
                        if not is_music:
                            continue
                        title = entry.get('title') or entry.get('originalTitle')
                        artist = entry.get('grandparentTitle') or ''
                        album = entry.get('parentTitle') or ''
                        thumb = entry.get('thumb')
                        if thumb and not thumb.startswith('http'):
                            thumb = self.url.rstrip('/') + thumb + (f"?X-Plex-Token={token}" if token else '')
                        items.append({'title': title, 'artist': artist, 'album': album, 'user': user or self.owner_username, 'thumb': thumb, 'type': itype or 'track', 'state': 'stopped'})
                        if len(items) >= limit:
                            break
                    if items:
                        break
            except Exception as e:
                print(f"Warning: fallo leyendo historial desde {ep}: {e}")
                continue

        # escribir caché
        try:
            cache_key_write = f"music2sig:history:{self.owner_username or 'unknown'}"
            if self._redis:
                self._redis.setex(cache_key_write, self._history_ttl, json.dumps(items))
                print(f"[CACHE-SET][redis] {cache_key_write} ({len(items)} items) ttl={self._history_ttl}s")
            else:
                self._history_cache = {'items': items, 'ts': int(time.time())}
                print(f"[CACHE-SET][mem] {cache_key_write} ({len(items)} items) ttl={self._history_ttl}s")
        except Exception:
            pass

        return items

    def clear_history_cache(self, user=None):
        key = f"music2sig:history:{user or self.owner_username or 'unknown'}"
        try:
            if self._redis:
                self._redis.delete(key)
                print(f"[CACHE-CLEAR][redis] {key}")
            self._history_cache = None
            print(f"[CACHE-CLEAR][mem] {key}")
            return True
        except Exception as e:
            print(f"[CACHE-CLEAR][err] {e}")
            return False


def create_plex_client(token=None):
    return PlexClient(token)


    def clear_history_cache(self, user=None):
        """Invalidar la caché del historial para un usuario (o global)."""
        key = f"music2sig:history:{user or self.owner_username or 'unknown'}"
        try:
            if self._redis:
                self._redis.delete(key)
                print(f"[CACHE-CLEAR][redis] {key}")
            # invalidar memoria local
            self._history_cache = None
            print(f"[CACHE-CLEAR][mem] {key}")
            return True
        except Exception as e:
            print(f"[CACHE-CLEAR][err] {e}")
            return False

        # seleccionar item según offset (para rotar) o aleatoriamente
        try:
            if offset is None or (isinstance(offset, str) and offset.lower() == 'random'):
                idx = random.randrange(len(items))
            elif isinstance(offset, int) or (isinstance(offset, str) and offset.isdigit()):
                idx = int(offset) % len(items)
            else:
                idx = random.randrange(len(items))
        except Exception:
            idx = random.randrange(len(items))

        return items[idx]

def create_plex_client(token=None):
    return PlexClient(token)
