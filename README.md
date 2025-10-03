# 🎵 Music2Signature

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/D-a-r-z/Music2Signature)

Music2Signature es una aplicación web que genera imágenes SVG animadas y estilizadas mostrando la música que se está reproduciendo actualmente en un servidor Plex Media Server. Perfecto para usar en perfiles de GitHub, firmas de foros, o cualquier integración web que requiera un indicador visual de "Now Playing".

> **Estado Actual**: Actualmente solo compatible con Plex Media Server. La integración con Spotify está planificada para futuras versiones cuando haya tiempo disponible.

![Now Playing](https://music2-signature.vercel.app/api/now-playing-svg?theme=transparent-light)

## 🚀 Despliegue Rápido

¿Quieres probar Music2Signature sin instalar nada? Usa el botón de arriba para crear tu propia instancia en Vercel. Una vez configurado tu token de Plex, tendrás una URL personalizada para usar en tu perfil de GitHub.

## ✨ Características

- **SVG Animado**: Genera imágenes SVG con portada del álbum, título, artista y álbum, más un ecualizador animado
- **Descubrimiento Automático**: Encuentra tu servidor Plex automáticamente usando tu token de autenticación
- **Múltiples Temas**: Soporte para temas claro, oscuro, transparente y compacto
- **Barras Animadas**: 96 barras delgadas que ocupan el ancho completo con animaciones wave-like
- **Caché Inteligente**: Soporte opcional para Redis con fallback automático a caché en memoria
- **Despliegue Fácil**: Configurado para Vercel con un solo clic
- **API RESTful**: Endpoints limpios para integración

## 🚀 Instalación Rápida

### Prerrequisitos
- Python 3.8+
- Token de Plex (obtén el tuyo en https://plex.tv)

### Pasos

1. **Clona el repositorio**
   ```bash
   git clone https://github.com/D-a-r-z/Music2Signature.git
   cd Music2Signature
   ```

2. **Configura el entorno virtual**
   ```bash
   python -m venv .venv
   # Windows PowerShell
   .venv\Scripts\activate
   # Linux/Mac
   source .venv/bin/activate
   ```

3. **Instala dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configura variables de entorno**
   Crea un archivo `.env`:
   ```env
   PLEX_TOKEN=tu_token_de_plex_aqui
   # Opcional: Redis para caché persistente
   # REDIS_URL=redis://localhost:6379/0
   ```

5. **Ejecuta la aplicación**
   ```bash
   python app.py
   ```
   Visita `http://localhost:5000` para probar

## 🌐 Despliegue

### Vercel (Recomendado)
1. Conecta tu repositorio de GitHub a Vercel
2. Configura las variables de entorno en el dashboard de Vercel
3. ¡Listo! Tu API estará disponible en `https://tu-proyecto.vercel.app`

### Otros Servicios
El proyecto es compatible con cualquier plataforma que soporte Python/Flask (Heroku, Railway, etc.)

## 📡 API Endpoints

### GET `/api/now-playing-svg`
Genera el SVG animado principal.

**Parámetros de Query:**
- `theme` (opcional): `normal`, `dark`, `transparent`, `bars` (default: `normal`)
- `width` (opcional): Ancho en píxeles (default: 400)
- `height` (opcional): Alto en píxeles (default: 100)
- `token` (opcional): Token de Plex (si no está en env)
- `user` (opcional): Usuario específico de Plex

**Ejemplo:**
```
GET /api/now-playing-svg?theme=transparent&height=90
```

### GET `/api/now-playing`
Alias público que devuelve el SVG (útil para embeber en READMEs).

### GET `/api/status`
Devuelve el estado de la conexión con Plex y información de la sesión actual.

### POST `/api/cache/clear`
Limpia la caché (útil para desarrollo).

## 🎨 Uso en GitHub

### En tu perfil de GitHub
Añade esto a tu `README.md`:

```markdown
### 🎵 Now Playing
![Now Playing](https://tu-dominio.vercel.app/api/now-playing?theme=transparent)
```

### Temas disponibles
- **`normal`**: Tema con fondo claro
- **`dark`**: Tema con fondo oscuro
- **`transparent-dark`**: Fondo transparente con letras oscuras (para fondos claros)
- **`transparent-light`**: Fondo transparente con letras blancas (para fondos oscuros)
- **`bars`**: Solo las barras animadas, sin texto

## ⚙️ Configuración Avanzada

### Variables de Entorno
| Variable | Descripción | Default |
|----------|-------------|---------|
| `PLEX_TOKEN` | Token de autenticación de Plex | *requerido* |
| `REDIS_URL` | URL de Redis para caché | *opcional* |
| `DEFAULT_THEME` | Tema por defecto | `normal` |
| `IMAGE_WIDTH` | Ancho por defecto | `400` |
| `IMAGE_HEIGHT` | Alto por defecto | `100` |
| `DEBUG` | Modo debug | `false` |

### Caché
- **Sin Redis**: Caché en memoria (se pierde al reiniciar)
- **Con Redis**: Caché persistente y compartido entre instancias

## 🔒 Privacidad

Por diseño, las imágenes públicas generadas no muestran información sensible de tu cuenta Plex. Toda la información mostrada es pública y relacionada con la reproducción actual.

## 🤝 Contribuir

¡Las contribuciones son bienvenidas! Lee [CONTRIBUTING.md](CONTRIBUTING.md) para más detalles.

### Áreas de contribución
- 🐛 Corrección de bugs
- ✨ Nuevas funcionalidades
- 🎨 Nuevos temas visuales
- 📚 Mejoras en documentación
- 🧪 Tests adicionales

##  Agradecimientos

- [Plex Media Server](https://plex.tv) por su excelente API
- [kittinan](https://github.com/kittinan/spotify-github-profile) por el proyecto spotify-github-profile que inspiró este trabajo
- [novatorem](https://github.com/novatorem/novatorem) por el proyecto novatorem y sus animaciones wave-like
- Comunidad de GitHub por la inspiración
- Todos los contribuidores que hacen este proyecto mejor

---

⭐ Si te gusta el proyecto, ¡dale una estrella en GitHub!