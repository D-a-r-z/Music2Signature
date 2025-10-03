import base64
import io
import requests
from PIL import Image

try:
    from colorthief import ColorThief
    _COLORTHIEF_AVAILABLE = True
except Exception:
    _COLORTHIEF_AVAILABLE = False

class SVGGenerator:
    _thumb_cache = {}

    NOVATOREM_DURATIONS_MS = [
        692, 881, 812, 949, 773, 802, 817, 699, 575, 538, 826, 843, 649, 606, 930, 714, 859, 506, 544, 659, 770, 896, 867, 700, 671, 639, 751, 525, 865, 785, 734, 576, 641, 785, 840, 979, 797, 752, 512, 659, 853, 568, 813, 656, 884, 646, 825, 668, 710, 585, 825, 775, 626, 522, 827, 861, 554, 772, 559, 677, 651, 548, 952, 816, 519, 541, 683, 889, 844, 535, 587, 896, 592, 680, 508, 954, 853, 582, 553, 618, 552, 990, 803, 749
    ]

    def __init__(self, width=400, height=100, theme='normal'):
        self.width = width
        self.height = height
        self.theme = theme

        if theme == 'dark':
            self.bg_color = '#161b22'
            self.text_color = '#f0f6fc'
            self.subtext_color = '#16181A'
        elif theme == 'transparent-dark':
            self.bg_color = 'transparent'
            self.text_color = '#0b1220'
            self.subtext_color = '#586273'
        elif theme == 'transparent-light':
            self.bg_color = 'transparent'
            self.text_color = '#ffffff'
            self.subtext_color = '#b6c2d1'
        else:
            self.bg_color = '#ffffff'
            self.text_color = '#0b1220'
            self.subtext_color = '#586273'

        self.accent_color = '#9C27B0'

    def _get_cover_data_url(self, session_data):
        if not session_data:
            return None
        thumb_url = session_data.get('thumb')
        if not thumb_url:
            return None

        cached = SVGGenerator._thumb_cache.get(thumb_url)
        if cached and cached.get('data_url'):
            return cached.get('data_url')

        try:
            resp = requests.get(thumb_url, timeout=6)
            if resp.status_code == 200 and resp.content:
                try:
                    img = Image.open(io.BytesIO(resp.content)).convert('RGB')
                    max_dim = 160
                    img.thumbnail((max_dim, max_dim), Image.LANCZOS)
                    buf = io.BytesIO()
                    img.save(buf, format='JPEG', quality=70, optimize=True)
                    b64 = base64.b64encode(buf.getvalue()).decode('ascii')
                    data_url = f'data:image/jpeg;base64,{b64}'
                    SVGGenerator._thumb_cache[thumb_url] = {'data_url': data_url, 'bytes': buf.getvalue(), 'palette': None}
                    return data_url
                except Exception:
                    b64 = base64.b64encode(resp.content).decode('ascii')
                    data_url = f'data:image/jpeg;base64,{b64}'
                    SVGGenerator._thumb_cache[thumb_url] = {'data_url': data_url, 'bytes': resp.content, 'palette': None}
                    return data_url
        except Exception:
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

    def _generate_css_bars(self, num_bars, bar_color):
        css = ""
        left = 1
        for i in range(num_bars):
            duration_ms = self.NOVATOREM_DURATIONS_MS[i % len(self.NOVATOREM_DURATIONS_MS)]
            delay_ms = -800 * i
            css += f".bar:nth-child({i+1}) {{ left: {left}px; animation-duration: {duration_ms}ms; animation-delay: {delay_ms}ms; }}"
            left += 3
        return css

    def _generate_html_bars(self, num_bars):
        return "".join(["<div class='bar'></div>" for _ in range(num_bars)])

    def generate_now_playing_svg(self, session_data):
        if self.theme in ('bars', 'novatorem', 'only-bars'):
            return self._generate_bars_only_svg(session_data)

        title = (session_data.get('title') if session_data else 'Sin reproducción') or 'Sin reproducción'
        artist = (session_data.get('artist') if session_data else '') or ''
        album = (session_data.get('album') if session_data else '') or ''
        cover_data = self._get_cover_data_url(session_data)
        palette = self._extract_palette(session_data)
        accent = palette[0] if palette else self.accent_color

        cover_x = 10
        cover_y = 5
        cover_size = 80
        text_x = cover_x + cover_size + 12
        text_y = 20

        def esc(t):
            return (t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))

        title_esc = esc(title)
        artist_line = f"{esc(artist)}" + (f" - {esc(album)}" if album else '')

        num_bars = 96
        bar_color = accent.replace('#', '')
        right_margin = 10
        content_width = self.width - text_x - right_margin
        bars_svg = self._generate_svg_bars(num_bars, bar_color, text_x, text_y + 47, content_width)

        gradient_stops_compact = (palette or [self.accent_color])[:6]
        stops_compact = ''
        for idx, col in enumerate(gradient_stops_compact):
            offset = int((idx / max(1, (len(gradient_stops_compact) - 1))) * 100)
            stops_compact += f'<stop offset="{offset}%" stop-color="{col}" />'

        svg = f'''<svg width="{self.width}" height="{self.height}" viewBox="0 0 {self.width} {self.height}" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <linearGradient id="barsGradientCompact" x1="0%" y1="0%" x2="100%" y2="0%">
            {stops_compact}
        </linearGradient>
        <clipPath id="contentClip">
            <rect x="{text_x}" y="0" width="{content_width}" height="{self.height}" />
        </clipPath>
        <style>
            .bg {{ fill: {self.bg_color}; }}
            .title {{ font-family: 'Arial', 'Helvetica', sans-serif; font-size:14px; font-weight:700; fill: {self.text_color}; }}
            .artist {{ font-family: 'Arial', 'Helvetica', sans-serif; font-size:12px; fill: {self.subtext_color}; }}
        </style>
    </defs>
  <rect class="bg" width="100%" height="100%" rx="8" />
  {f'<image href="{cover_data}" x="{cover_x}" y="{cover_y}" width="{cover_size}" height="{cover_size}" preserveAspectRatio="xMidYMid slice" />' if cover_data else f'<rect x="{cover_x}" y="{cover_y}" width="{cover_size}" height="{cover_size}" rx="6" fill="#ddd" />'}
  <g clip-path="url(#contentClip)">
    <text x="{text_x}" y="{text_y}" class="title">{title_esc}</text>
    <text x="{text_x}" y="{text_y + 18}" class="artist">{artist_line}</text>
    {bars_svg}
  </g>
</svg>'''

        return svg

    def _generate_svg_bars(self, num_bars, bar_color, start_x, start_y, content_width):
        """Generate SVG bars using native SVG elements with animate tags"""
        bars_svg = ''
        base_height = 4
        max_height = 18

        # Fixed bar width and spacing
        bar_width = 2
        spacing = 1

        # Calculate how many bars fit in the available space
        total_width_needed = num_bars * bar_width + (num_bars - 1) * spacing
        if total_width_needed > content_width:
            # Reduce number of bars if they don't fit
            max_bars = int((content_width + spacing) / (bar_width + spacing))
            num_bars = max(1, max_bars)

        # Recalculate with actual number of bars
        total_width_needed = num_bars * bar_width + (num_bars - 1) * spacing
        # Center the bars in the available space
        start_offset = (content_width - total_width_needed) / 2

        for i in range(num_bars):
            x = start_x + start_offset + i * (bar_width + spacing)
            y = start_y + (max_height - base_height)  # Position from bottom

            # Generate animation values for wave effect
            duration = self.NOVATOREM_DURATIONS_MS[i % len(self.NOVATOREM_DURATIONS_MS)]
            delay = -800 * i  # Staggered delay

            # Create height animation values (base_height to max_height)
            values = f"{base_height};{max_height};{base_height}"
            keytimes = "0;0.5;1"

            bar_svg = f'''<rect x="{x}" y="{y - base_height}" width="{bar_width}" height="{base_height}" fill="#{bar_color}" opacity="0.35">
  <animate attributeName="height" values="{values}" keyTimes="{keytimes}" dur="{duration}ms" begin="{delay}ms" repeatCount="indefinite" />
  <animate attributeName="opacity" values="0.35;0.95;0.35" keyTimes="{keytimes}" dur="{duration}ms" begin="{delay}ms" repeatCount="indefinite" />
  <animate attributeName="y" values="{y - base_height};{y - max_height};{y - base_height}" keyTimes="{keytimes}" dur="{duration}ms" begin="{delay}ms" repeatCount="indefinite" />
</rect>'''

            bars_svg += bar_svg

        return bars_svg

    def _generate_bars_only_svg(self, session_data):
        palette = self._extract_palette(session_data, count=6) or [self.accent_color]
        gradient_stops = palette[:6]

        left_margin = 8
        right_margin = 8
        usable_width = max(0, self.width - left_margin - right_margin)

        approx_slots = max(8, usable_width // 12)
        num_bars = max(4, min(40, int(approx_slots)))

        gap_ratio = 0.5
        denom = (num_bars + (num_bars - 1) * gap_ratio)
        if denom <= 0:
            bar_width = 3
        else:
            bar_width = max(2, int(usable_width / denom))

        bar_width = max(1, bar_width // 2)

        bar_color = gradient_stops[0].replace('#', '') if gradient_stops[0].startswith('#') else '9C27B0'

        # For bars-only theme, use full width from left_margin to right_margin
        content_width = self.width - left_margin - 8  # 8px right margin to match other themes
        bars_svg = self._generate_svg_bars(num_bars, bar_color, left_margin, int(self.height * 0.85) - 15, content_width)

        stops_markup = ''
        for idx, col in enumerate(gradient_stops):
            offset = int((idx / max(1, (len(gradient_stops) - 1))) * 100)
            stops_markup += f'<stop offset="{offset}%" stop-color="{col}" />'

        svg = f'''<svg width="{self.width}" height="{self.height}" viewBox="0 0 {self.width} {self.height}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="barsGradient" x1="0%" y1="0%" x2="100%" y2="0%">
      {stops_markup}
    </linearGradient>
    <style>
      .bg {{ fill: {self.bg_color}; }}
    </style>
  </defs>
  <rect class="bg" width="100%" height="100%" rx="8" />
  {bars_svg}
</svg>'''

        return svg
