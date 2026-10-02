"""
Music2Signature - Generador de SVG
Genera imágenes SVG animadas para widgets 'Now Playing'
"""
import base64
import html
import io
import logging
import os
import re
import requests
from PIL import Image

try:
    from colorthief import ColorThief
    _COLORTHIEF_AVAILABLE = True
except Exception:
    _COLORTHIEF_AVAILABLE = False

logger = logging.getLogger(__name__)

# Caracteres ilegales en XML 1.0 (caracteres de control excepto tab, LF, CR)
XML_ILLEGAL_CHARS_RE = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\ud800-\udfff\ufffe\uffff]')


def _escape_xml(text) -> str:
    """Escapa texto para inserción segura en XML/SVG y elimina caracteres de control ilegales."""
    if text is None:
        return ''
    cleaned = XML_ILLEGAL_CHARS_RE.sub('', str(text))
    return html.escape(cleaned, quote=True)


class SVGGenerator:
    _thumb_cache = {}
    _MAX_THUMB_CACHE = 100
    _font_cache = {}

    @classmethod
    def _get_font(cls, bold=False, size=14):
        key = (bold, size)
        if key in cls._font_cache:
            return cls._font_cache[key]
        try:
            from PIL import ImageFont
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            font_filename = 'ARIALBD.TTF' if bold else 'ARIAL.TTF'
            font_path = os.path.join(base_dir, 'assets', 'fonts', font_filename)
            if os.path.exists(font_path):
                font = ImageFont.truetype(font_path, size)
                cls._font_cache[key] = font
                return font
        except Exception as e:
            logger.debug(f"No se pudo cargar la fuente local: {e}")
        cls._font_cache[key] = None
        return None

    @classmethod
    def measure_text_width(cls, text: str, bold: bool = False, size: int = 14) -> float:
        if not text:
            return 0.0
        font = cls._get_font(bold=bold, size=size)
        if font and hasattr(font, 'getlength'):
            try:
                return float(font.getlength(text))
            except Exception:
                pass
        char_ratio = 0.62 if bold else 0.54
        return float(len(text) * size * char_ratio)

    NOVATOREM_DURATIONS_MS = [
        692, 881, 812, 949, 773, 802, 817, 699, 575, 538, 826, 843, 649, 606, 930, 714, 859, 506, 544, 659, 770, 896, 867, 700, 671, 639, 751, 525, 865, 785, 734, 576, 641, 785, 840, 979, 797, 752, 512, 659, 853, 568, 813, 656, 884, 646, 825, 668, 710, 585, 825, 775, 626, 522, 827, 861, 554, 772, 559, 677, 651, 548, 952, 816, 519, 541, 683, 889, 844, 535, 587, 896, 592, 680, 508, 954, 853, 582, 553, 618, 552, 990, 803, 749
    ]

    def __init__(self, width=400, height=90, theme='normal', text_color=None, subtext_color=None, bar_color=None,
                 cover_max_dim=None, cover_quality=None):
        self.width = max(200, min(1200, width))
        self.height = max(40, min(600, height))
        self.theme = (theme or 'normal').lower()
        self.cover_max_dim = int(cover_max_dim) if cover_max_dim is not None else None
        self.cover_quality = int(cover_quality) if cover_quality is not None else None

        if self.theme == 'dark':
            self.bg_color = '#161b22'
            self.text_color = '#f0f6fc'
            self.subtext_color = '#c9d1d9'
        elif self.theme == 'transparent-dark':
            self.bg_color = 'transparent'
            self.text_color = '#0b1220'
            self.subtext_color = '#0b1220'  # Alineado con el tono oscuro del título para máxima legibilidad
        elif self.theme in ('transparent-light', 'transparent'):
            self.bg_color = 'transparent'
            self.text_color = '#ffffff'
            self.subtext_color = '#ffffff'
        else:
            self.bg_color = '#ffffff'
            self.text_color = '#0b1220'
            self.subtext_color = '#24292f'

        # Sobrescrituras opcionales de color
        if text_color:
            self.text_color = self._normalize_color(text_color)
        if subtext_color:
            self.subtext_color = self._normalize_color(subtext_color)

        self.custom_bar_color = self._normalize_color(bar_color) if bar_color else None
        self.accent_color = self.custom_bar_color or '#9C27B0'

    def _get_cover_data_url(self, session_data):
        if not session_data:
            return None
        thumb_url = session_data.get('thumb')
        if not thumb_url or not isinstance(thumb_url, str):
            return None
        if not thumb_url.startswith(('http://', 'https://')):
            return None

        cached = SVGGenerator._thumb_cache.get(thumb_url)
        if cached and cached.get('data_url'):
            return cached.get('data_url')

        try:
            headers = {
                'X-Plex-Client-Identifier': os.getenv('PLEX_CLIENT_IDENTIFIER', 'music2signature-app-client'),
                'X-Plex-Product': 'Music2Signature',
                'X-Plex-Device': 'Music2Signature',
                'X-Plex-Device-Name': 'Music2Signature',
            }
            resp = requests.get(thumb_url, headers=headers, timeout=6)
            if resp.status_code == 200 and resp.content:
                try:
                    img = Image.open(io.BytesIO(resp.content)).convert('RGB')
                    max_dim = self.cover_max_dim or int(os.getenv('COVER_MAX_DIM', 100))
                    quality = self.cover_quality or int(os.getenv('COVER_QUALITY', 70))
                    img.thumbnail((max_dim, max_dim), Image.LANCZOS)
                    buf = io.BytesIO()
                    img.save(buf, format='JPEG', quality=quality, optimize=True)
                    b64 = base64.b64encode(buf.getvalue()).decode('ascii')
                    data_url = f'data:image/jpeg;base64,{b64}'

                    if len(SVGGenerator._thumb_cache) >= SVGGenerator._MAX_THUMB_CACHE:
                        oldest_key = next(iter(SVGGenerator._thumb_cache))
                        SVGGenerator._thumb_cache.pop(oldest_key, None)

                    SVGGenerator._thumb_cache[thumb_url] = {
                        'data_url': data_url,
                        'bytes': buf.getvalue(),
                        'palette': None
                    }
                    return data_url
                except Exception:
                    b64 = base64.b64encode(resp.content).decode('ascii')
                    data_url = f'data:image/jpeg;base64,{b64}'
                    if len(SVGGenerator._thumb_cache) >= SVGGenerator._MAX_THUMB_CACHE:
                        oldest_key = next(iter(SVGGenerator._thumb_cache))
                        SVGGenerator._thumb_cache.pop(oldest_key, None)
                    SVGGenerator._thumb_cache[thumb_url] = {'data_url': data_url, 'bytes': resp.content, 'palette': None}
                    return data_url
        except Exception as e:
            logger.debug(f"No se pudo descargar portada de {thumb_url}: {e}")
            return None
        return None

    def _extract_palette(self, session_data, count=6):
        if not session_data:
            return None
        thumb = session_data.get('thumb')
        if not thumb:
            return None
        cached = SVGGenerator._thumb_cache.get(thumb)
        if not cached or not cached.get('bytes'):
            return None

        try:
            if _COLORTHIEF_AVAILABLE:
                buf = io.BytesIO(cached.get('bytes'))
                ct = ColorThief(buf)
                pal = ct.get_palette(color_count=count)
                return [f'rgb({c[0]},{c[1]},{c[2]})' for c in pal]
            else:
                img = Image.open(io.BytesIO(cached.get('bytes'))).convert('RGB')
                avg = img.resize((1, 1), Image.LANCZOS).getpixel((0, 0))
                return [f'rgb({avg[0]},{avg[1]},{avg[2]})']
        except Exception:
            return None

    def _normalize_color(self, color_str: str) -> str:
        """Normaliza una cadena de color CSS para que sea válida en atributos fill."""
        if not color_str:
            return self.accent_color
        s = str(color_str).strip()
        if s.startswith('#') or s.startswith('rgb') or s.startswith('hsl'):
            return s
        # Si es un valor hexadecimal sin # (ej. '9C27B0')
        if re.match(r'^[0-9a-fA-F]{3,8}$', s):
            return f'#{s}'
        return s

    def _generate_text_layer(self, escaped_text: str, raw_text: str, font_size: int, is_bold: bool,
                            x: int, y: int, css_class: str, content_width: int, marquee: bool = True) -> str:
        """
        Genera la capa de texto en SVG. Si el texto sobrepasa el ancho disponible,
        aplica una animación de desplazamiento suave (efecto marquesina / ping-pong)
        que revela todo el contenido sin romper dimensiones ni desbordarse.
        """
        if not escaped_text:
            return ''

        text_width = self.measure_text_width(raw_text, bold=is_bold, size=font_size)

        # Si entra en el ancho disponible o marquee está desactivado, texto estático
        if not marquee or text_width <= content_width:
            return f'<text x="{x}" y="{y}" class="{css_class}">{escaped_text}</text>'

        # Si sobrepasa el ancho, calculamos el exceso en píxeles + 12px de margen estético
        overflow = int(text_width - content_width + 12)

        # Velocidad de lectura confortable: ~26-28 px por segundo
        scroll_duration = max(2.2, overflow / 26.0)
        pause_start = 2.5       # Pausa inicial para comenzar a leer cómodamente
        pause_end = 2.0         # Pausa al llegar al final del texto
        return_duration = max(1.6, scroll_duration * 0.72)  # Retorno ligeramente más ágil
        pause_final = 0.5       # Pausa breve antes de repetir el ciclo

        total_time = pause_start + scroll_duration + pause_end + return_duration + pause_final

        k1 = pause_start / total_time
        k2 = (pause_start + scroll_duration) / total_time
        k3 = (pause_start + scroll_duration + pause_end) / total_time
        k4 = (pause_start + scroll_duration + pause_end + return_duration) / total_time

        values = f"0 0; 0 0; -{overflow} 0; -{overflow} 0; 0 0; 0 0"
        key_times = f"0; {k1:.3f}; {k2:.3f}; {k3:.3f}; {k4:.3f}; 1"
        key_splines = "0 0 1 1; 0.42 0 0.58 1; 0 0 1 1; 0.42 0 0.58 1; 0 0 1 1"

        return f'''<g>
      <animateTransform
        attributeName="transform"
        type="translate"
        values="{values}"
        keyTimes="{key_times}"
        calcMode="spline"
        keySplines="{key_splines}"
        dur="{total_time:.1f}s"
        repeatCount="indefinite" />
      <text x="{x}" y="{y}" class="{css_class}">{escaped_text}</text>
    </g>'''

    def generate_now_playing_svg(self, session_data, idle_mode=None, marquee=None):
        if idle_mode is None:
            idle_mode = os.getenv('IDLE_MODE', 'bars').strip().lower()
        else:
            idle_mode = str(idle_mode).strip().lower()

        if marquee is None:
            marquee_env = os.getenv('MARQUEE_ENABLED', 'true').strip().lower()
            marquee = marquee_env not in ('false', '0', 'no')
        else:
            marquee = bool(marquee)

        raw_title = session_data.get('title') if session_data else None
        has_any_meta = session_data and any(session_data.get(k) and str(session_data.get(k)).strip() for k in ('title', 'artist', 'album'))
        is_idle = not session_data or not has_any_meta

        # Modo 'solo barritas' cuando no hay reproducción activa ni metadatos
        if is_idle and idle_mode in ('bars', 'bars-only', 'barritas'):
            margin_x = 16
            content_width = max(10, self.width - (margin_x * 2))
            num_bars = 96
            bar_color = self.custom_bar_color or self._normalize_color(self.accent_color)
            center_y = max(4, (self.height - 18) / 2)
            bars_svg = self._generate_svg_bars(num_bars, bar_color, margin_x, center_y, content_width)

            return f'''<svg width="{self.width}" height="{self.height}" viewBox="0 0 {self.width} {self.height}" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <style>
            .bg {{ fill: {self.bg_color}; }}
        </style>
    </defs>
  <rect class="bg" width="100%" height="100%" rx="8" />
  {bars_svg}
</svg>'''

        title = raw_title if (raw_title and str(raw_title).strip()) else 'Sin reproducción'
        artist = (session_data.get('artist') if session_data else '') or ''
        album = (session_data.get('album') if session_data else '') or ''
        cover_data = self._get_cover_data_url(session_data)
        palette = self._extract_palette(session_data)
        accent = self.custom_bar_color or (palette[0] if palette else self.accent_color)

        cover_x = 10
        cover_y = 5
        cover_size = 80
        text_x = cover_x + cover_size + 12
        text_y = 20

        raw_title_str = title
        title_esc = _escape_xml(title)
        if artist and album:
            artist_line_raw = f"{artist} - {album}"
            artist_line = f"{_escape_xml(artist)} - {_escape_xml(album)}"
        elif artist:
            artist_line_raw = artist
            artist_line = _escape_xml(artist)
        elif album:
            artist_line_raw = album
            artist_line = _escape_xml(album)
        else:
            artist_line_raw = ''
            artist_line = ''

        num_bars = 96
        bar_color = self._normalize_color(accent)
        right_margin = 10
        content_width = max(10, self.width - text_x - right_margin)
        bars_svg = self._generate_svg_bars(num_bars, bar_color, text_x, text_y + 47, content_width)

        title_markup = self._generate_text_layer(
            escaped_text=title_esc,
            raw_text=raw_title_str,
            font_size=14,
            is_bold=True,
            x=text_x,
            y=text_y,
            css_class="title",
            content_width=content_width,
            marquee=marquee
        )
        artist_markup = self._generate_text_layer(
            escaped_text=artist_line,
            raw_text=artist_line_raw,
            font_size=12,
            is_bold=True,
            x=text_x,
            y=text_y + 18,
            css_class="artist",
            content_width=content_width,
            marquee=marquee
        )

        gradient_stops_compact = (palette or [self.accent_color])[:6]
        stops_compact = ''
        for idx, col in enumerate(gradient_stops_compact):
            offset = int((idx / max(1, (len(gradient_stops_compact) - 1))) * 100)
            stops_compact += f'<stop offset="{offset}%" stop-color="{_escape_xml(col)}" />'

        image_markup = (
            f'<image href="{cover_data}" x="{cover_x}" y="{cover_y}" '
            f'width="{cover_size}" height="{cover_size}" clip-path="url(#coverClip)" preserveAspectRatio="xMidYMid slice" />'
            if cover_data else
            f'<rect x="{cover_x}" y="{cover_y}" width="{cover_size}" height="{cover_size}" rx="6" fill="#ddd" />'
        )

        svg = f'''<svg width="{self.width}" height="{self.height}" viewBox="0 0 {self.width} {self.height}" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <linearGradient id="barsGradientCompact" x1="0%" y1="0%" x2="100%" y2="0%">
            {stops_compact}
        </linearGradient>
        <clipPath id="contentClip">
            <rect x="{text_x}" y="0" width="{content_width}" height="{self.height}" />
        </clipPath>
        <clipPath id="coverClip">
            <rect x="{cover_x}" y="{cover_y}" width="{cover_size}" height="{cover_size}" rx="6" />
        </clipPath>
        <style>
            .bg {{ fill: {self.bg_color}; }}
            .title {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; font-size:14px; font-weight:700; fill: {self.text_color}; }}
            .artist {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; font-size:12px; font-weight:600; fill: {self.subtext_color}; opacity: 0.92; }}
        </style>
    </defs>
  <rect class="bg" width="100%" height="100%" rx="8" />
  {image_markup}
  <g clip-path="url(#contentClip)">
    {title_markup}
    {artist_markup}
    {bars_svg}
  </g>
</svg>'''

        return svg

    def _generate_svg_bars(self, num_bars, bar_color, start_x, start_y, content_width):
        """Genera las barras de onda animadas con elementos rect y animate nativos de SVG."""
        bars_svg = ''
        base_height = 4
        max_height = 18

        bar_width = 2
        spacing = 1

        total_width_needed = num_bars * bar_width + (num_bars - 1) * spacing
        if total_width_needed > content_width:
            max_bars = int((content_width + spacing) / (bar_width + spacing))
            num_bars = max(1, max_bars)

        total_width_needed = num_bars * bar_width + (num_bars - 1) * spacing
        start_offset = max(0, (content_width - total_width_needed) / 2)

        fill_color = self._normalize_color(bar_color)

        for i in range(num_bars):
            x = start_x + start_offset + i * (bar_width + spacing)
            y = start_y + (max_height - base_height)

            duration = self.NOVATOREM_DURATIONS_MS[i % len(self.NOVATOREM_DURATIONS_MS)]
            delay = -800 * i

            values = f"{base_height};{max_height};{base_height}"
            keytimes = "0;0.5;1"

            bar_svg = f'''<rect x="{x}" y="{y - base_height}" width="{bar_width}" height="{base_height}" fill="{fill_color}" opacity="0.55">
  <animate attributeName="height" values="{values}" keyTimes="{keytimes}" dur="{duration}ms" begin="{delay}ms" repeatCount="indefinite" />
  <animate attributeName="opacity" values="0.55;1.0;0.55" keyTimes="{keytimes}" dur="{duration}ms" begin="{delay}ms" repeatCount="indefinite" />
  <animate attributeName="y" values="{y - base_height};{y - max_height};{y - base_height}" keyTimes="{keytimes}" dur="{duration}ms" begin="{delay}ms" repeatCount="indefinite" />
</rect>'''

            bars_svg += bar_svg

        return bars_svg

