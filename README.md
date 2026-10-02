# Music2Signature

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/D-a-r-z/Music2Signature)

Servicio web en Python/Flask que genera tarjetas SVG animadas mostrando la música que se está reproduciendo actualmente en Plex Media Server. Diseñado para embeber en perfiles de GitHub, firmas de foros o páginas personales como widget "Now Playing".

![Now Playing](https://music2-signature.vercel.app/api/now-playing-svg?theme=transparent-light)

## Características

- SVG dinámico con portada del álbum incrustada en base64, título, artista y álbum.
- Ecualizador animado nativo en SVG con extracción de paleta de color de la carátula.
- Autodescubrimiento de servidores Plex a través de plex.tv o conexión directa por URL local/remota.
- Temas adaptados para fondos oscuros, claros y transparentes.
- Sistema de caché en memoria de alta velocidad con expiración por TTL para despliegues serverless.
- Modo reposo visual con ondas ecualizadoras animadas cuando no hay reproducción activa.
- Sin exposición de credenciales ni tokens en logs o SVG generados.

## Requisitos

- Python 3.8+
- Servidor Plex Media Server accesible y token de autenticación (`PLEX_TOKEN`).

## Instalación local

1. Clonar el repositorio:
   ```bash
   git clone https://github.com/D-a-r-z/Music2Signature.git
   cd Music2Signature
   ```

2. Crear y activar entorno virtual:
   ```bash
   python -m venv .venv
   # Windows PowerShell
   .venv\Scripts\activate
   # Linux / macOS
   source .venv/bin/activate
   ```

3. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

4. Configurar variables de entorno:
   ```bash
   # Windows PowerShell
   Copy-Item .env.example .env
   # Linux / macOS
   cp .env.example .env
   ```
   Editar `.env` y definir al menos `PLEX_TOKEN`.

5. Iniciar la aplicación:
   ```bash
   python app.py
   ```
   Acceder a `http://localhost:5000` para verificar el estado y los temas disponibles.

## Despliegue en Vercel

1. Importar el repositorio en Vercel.
2. Añadir las variables de entorno en el panel del proyecto (**Settings > Environment Variables**):
   - `PLEX_TOKEN`: Token de autenticación de Plex.
   - `DEFAULT_THEME` (opcional): Tema predeterminado (ej. `transparent-light`).
3. El despliegue se gestiona automáticamente mediante `vercel.json`.

## API

### GET `/api/now-playing-svg`
Genera el SVG animado de reproducción actual.

Parámetros opcionales:
- `theme`: `normal`, `dark`, `transparent-light`, `transparent-dark`, `transparent` (default: `normal`).
- `width`: Ancho en píxeles (default: 400, mín: 200, máx: 1200).
- `height`: Alto en píxeles (default: 90, mín: 40, máx: 600).
- `token`: Token de Plex alternativo (si no se define en variables de entorno).
- `user`: Filtrar reproducción por usuario específico de Plex.
- `idle`: `bars` o `full` (default: según `IDLE_MODE` o `bars`). Modo al estar en reposo. `bars` muestra únicamente las ondas de audio animadas centradas (sin caja vacía ni textos); `full` muestra la tarjeta completa con el estado "Sin reproducción".
- `marquee`: `true` o `false` (default: `true`). Activa o desactiva el desplazamiento marquesina animado cuando el título o artista/disco sobrepasan el ancho disponible.
- `color`: Color hexadecimal o CSS para el título principal (ej. `0b1220`, `ffffff`).
- `subcolor`: Color hexadecimal o CSS para el artista y disco (ej. `0b1220`, `ffffff`). En temas transparentes coincide por defecto con el tono del título para máxima legibilidad.
- `bar_color`: Color hexadecimal o CSS para forzar el color de las barras animadas (ej. `000000`, `ffffff`). Si no se indica, se extrae de la portada.
- `refresh`: `true` para omitir la caché de la aplicación y consultar directamente a Plex en ese instante.

Ejemplo:
```
GET /api/now-playing-svg?theme=transparent-light&height=90&idle=bars&marquee=true
```

### GET `/api/now-playing`
Alias directo de `/api/now-playing-svg`. Conveniente para perfiles de GitHub:

```markdown
![Now Playing](https://tu-proyecto.vercel.app/api/now-playing?theme=transparent-light&idle=bars)
```

### GET `/api/status`
Devuelve un JSON con el estado de la conexión a Plex, información del servidor, sesión actual y estadísticas de caché.

### POST / GET `/api/cache/clear`
Invalida la caché interna de la aplicación en memoria.

## Temas disponibles

- `normal`: Fondo blanco sólido (#ffffff) con texto oscuro.
- `dark`: Fondo oscuro (#161b22) con texto blanco y secundario en gris legible (#8b949e).
- `transparent-light` (o `transparent`): Fondo transparente con texto blanco, optimizado para perfiles de GitHub en modo oscuro.
- `transparent-dark`: Fondo transparente con texto oscuro, optimizado para interfaces claras.

## Variables de entorno

| Variable | Descripción | Valor por defecto |
|---|---|---|
| `PLEX_TOKEN` | Token de autenticación de Plex | Requerido |
| `PLEX_URL` | URL directa del servidor Plex (ej. `http://192.168.1.100:32400` o IP pública) | Autodescubierto vía plex.tv |
| `PLEX_USER` | Usuario de Plex para filtrar sesiones | Propietario de la cuenta |
| `IDLE_MODE` | Modo en reposo sin reproducción (`bars` para solo ondas animadas, `full` para tarjeta completa) | `bars` |
| `MARQUEE_ENABLED` | Efecto marquesina animado para textos largos de título y artista | `true` |
| `ALLOW_VIDEO` | Permite mostrar reproducciones de video (películas, series) además de música | `false` |
| `COVER_MAX_DIM` | Dimensión máxima en píxeles de la carátula embebida | `100` |
| `COVER_QUALITY` | Calidad de compresión JPEG de la carátula | `70` |
| `PLEX_CLIENT_IDENTIFIER` | Identificador persistente del cliente en Plex para evitar alertas de nuevo dispositivo | `music2signature-app-client` |
| `PLEX_DEVICE_NAME` | Nombre de dispositivo registrado en Plex Media Server | `Music2Signature` |
| `CACHE_DURATION` | TTL de la caché de tarjetas SVG (segundos) | `60` |
| `DEFAULT_THEME` | Tema visual predeterminado | `normal` |
| `IMAGE_WIDTH` | Ancho predeterminado de la tarjeta | `400` |
| `IMAGE_HEIGHT` | Alto predeterminado de la tarjeta | `90` |
| `DEBUG` | Activa modo depuración | `false` |

## Créditos

- Basado en el concepto de [spotify-github-profile](https://github.com/kittinan/spotify-github-profile) de kittinan.
- Estilos de animación de ondas inspirados en [novatorem](https://github.com/novatorem).