# 🎵 Music2Signature

**[Español](#español)** | **[English](#english)**

---

## 🚀 Demo en Vivo

**Deploy en Vercel**: https://plex2-sign.vercel.app/

![Plex Now Playing](https://plex2-sign.vercel.app/api/now-playing-svg?theme=normal)

---

# Español

## 📋 Descripción

Music2Signature es un generador de firmas dinámicas que muestra el contenido multimedia que estás reproduciendo actualmente desde tu servidor Plex Media Server. Similar al popular [spotify-github-profile](https://github.com/kittinan/spotify-github-profile), pero diseñado específicamente para usuarios de Plex.

Perfecto para:
- 🐙 **README del Perfil de GitHub**
- 💬 **Firmas de Foros**
- 📱 **Integración en Redes Sociales**
- 🎯 **Marca Personal**

## ✨ Características

### 🎨 Múltiples Formatos
- **SVG (Animado)**: Barras de ecualizador dinámicas con animaciones suaves
- **PNG (Estático)**: Imágenes limpias y estáticas con visualización de ecualizador

### 🌓 Soporte de Temas
- **Normal**: Fondo blanco limpio con acentos azules
- **Oscuro**: Fondo claro con texto oscuro para compatibilidad universal

### 🎵 Tipos de Media
- **Música**: Información de artista, álbum y canción con ecualizador animado
- **Series de TV**: Título de la serie, temporada, episodio con ecualizador estático
- **Películas**: Título de la película e información

### 🔧 Características Técnicas
- **Detección Automática del Servidor**: Usa la API de Plex Account para descubrir automáticamente el servidor externo
- **Extracción Dinámica de Colores**: Extrae colores de las portadas de álbumes para barras de ecualizador personalizadas
- **Manejo Inteligente de Texto**: Desplazamiento horizontal (marquee) para títulos largos
- **Imágenes de Alta Calidad**: Procesamiento a 120x120px para visualización nítida a 80x80px
- **Caché**: Caché eficiente de imágenes para reducir la carga del servidor

## 📖 Uso

### Perfil de GitHub

Añade esto a tu README del perfil de GitHub:

```markdown
![Plex Now Playing](https://tu-url-vercel.vercel.app/api/now-playing-svg?theme=normal)
```

### Firmas de Foro

Para fondos claros:
```markdown
![Plex Now Playing](https://tu-url-vercel.vercel.app/api/now-playing-svg?theme=dark)
```

### Endpoints Disponibles

- **SVG (Animado)**:
  - Normal: `/api/now-playing-svg?theme=normal`
  - Oscuro: `/api/now-playing-svg?theme=dark`

- **PNG (Estático)**:
  - Normal: `/api/now-playing-png?theme=normal`
  - Oscuro: `/api/now-playing-png?theme=dark`

### Soporte Multi-Usuario

Para deployments compartidos o filtrado de usuario específico:

- **Con token específico**: `?token=tu_token_de_plex`
- **Con usuario específico**: `?user=nombre_de_usuario`
- **Combinado**: `?token=tu_token_de_plex&user=nombre_de_usuario`

Ejemplo:
```markdown
![Plex Now Playing](https://tu-url-vercel.vercel.app/api/now-playing-svg?token=tu_token&user=tu_usuario)
```

## 🛠️ Instalación

### Requisitos
- Token de Plex (obtenido desde https://support.plex.tv/articles/204059436/)
- Client ID de Imgur (opcional, para hosting de imágenes)

> Nota: La integración con Imgur se ha retirado como comportamiento por defecto debido a problemas de consistencia en entornos serverless (p. ej. Vercel) y la complejidad adicional que añadía. Plex provee miniaturas directamente y la mayoría de despliegues funcionan sin Imgur. Si necesitas cache persistente para mejorar latencia, considera usar una solución centralizada como Redis o un CDN.

### Instalación

1. **Clonar el repositorio**
```bash
git clone https://github.com/D-a-r-z/Music2Signature.git
cd Music2Signature
```

2. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

3. **Configurar variables de entorno**
Crear un archivo `.env`:
```env
PLEX_TOKEN=tu_token_de_plex_aqui
IMGUR_CLIENT_ID=tu_client_id_de_imgur_aqui
```

**📝 Filtrado automático de usuario:**
La aplicación filtra automáticamente el contenido por el usuario asociado a tu token de Plex. Cada usuario solo verá su propio contenido por defecto.

4. **Ejecutar localmente**
```bash
python app.py
```

Visita `http://localhost:5000` para ver el dashboard.

---

## 🌐 Despliegue

### Vercel (Recomendado)

1. **Hacer fork de este repositorio**
2. **Conectar a Vercel**
3. **Configurar variables de entorno**:
   - `PLEX_TOKEN`: Tu token de Plex
   - `IMGUR_CLIENT_ID`: Tu client ID de Imgur

**🔒 Filtrado automático de usuario:**
La aplicación filtra automáticamente el contenido por el usuario asociado a tu token de Plex. No se necesita configuración adicional.

La aplicación detectará automáticamente la URL externa de tu servidor Plex usando la API de Plex Account.

## ⚙️ Configuración

### Variables de entorno requeridas

```env
# Plex (Requerido)
PLEX_TOKEN=tu_token_de_plex
PLEX_URL=http://tu-servidor-plex:32400  # Opcional

# Imgur (Opcional, para hosting de imágenes)
IMGUR_CLIENT_ID=tu_client_id_de_imgur

# Configuración (Opcional)
DEFAULT_THEME=normal
IMAGE_WIDTH=400
IMAGE_HEIGHT=90
DEBUG=false
```

### Cómo obtener el token de Plex

1. Ve a [plex.tv](https://plex.tv)
2. Inicia sesión en tu cuenta
3. Ve a **Settings** > **Network**
4. Copia el **Token** de la URL

## 📖 Documentación

### Endpoints disponibles

| Endpoint | Descripción |
|----------|-------------|
| `/` | Página principal con demo |
| `/api/now-playing` | Imagen principal (usa miniaturas de Plex o hosting externo si está configurado) |
| `/api/now-playing-svg` | SVG animado |
| `/api/now-playing-png` | PNG estático |
| `/api/status` | Estado del sistema |
| `/api/cache/clear` | Limpiar cache |

### Parámetros URL

| Parámetro | Descripción | Valores |
|-----------|-------------|---------|
| `theme` | Tema visual | `normal`, `dark` |
| `width` | Ancho de imagen | Número (ej: `400`) |
| `height` | Alto de imagen | Número (ej: `90`) |
| `token` | Token de Plex | Token personal |
| `user` | Usuario específico | Nombre de usuario |
| `refresh` | Forzar actualización | `true` |

## 🎨 Personalización

### Temas personalizados

Puedes crear tus propios temas modificando `api/svg_generator.py`:

```python
'custom_theme': {
    'bg_color': '#ffffff',
    'text_color': '#333333',
    'accent_color': '#ff6b6b',
    'font_family': 'Arial, sans-serif',
    'font_size_title': '14px',
    'font_size_subtitle': '11px',
}
```

### Colores dinámicos

El sistema extrae automáticamente colores de las carátulas de álbumes para crear ecualizadores personalizados.

## 🔧 Desarrollo

### Estructura del proyecto

```
Music2Signature/
├── api/                    # Módulos principales
│   ├── plex_client.py     # Cliente Plex
│   ├── svg_generator.py   # Generador SVG animado
│   ├── image_generator.py # Generador PNG estático
│   └── imgur_client.py    # Cliente Imgur (opcional, para hosting externo)
├── assets/                # Recursos
│   └── fonts/            # Fuentes personalizadas
├── app.py                # Aplicación Flask
├── requirements.txt      # Dependencias
└── vercel.json          # Configuración Vercel
```

### Tecnologías utilizadas

- **Python 3.8+**
- **Flask** - Framework web
- **PlexAPI** - Cliente Plex
- **Pillow (PIL)** - Procesamiento de imágenes
- **ColorThief** - Extracción de colores
- **Vercel** - Hosting

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

## 🙏 Agradecimientos

- [Plex](https://plex.tv) por la excelente API
- [Vercel](https://vercel.com) por el hosting gratuito
- [Imgur](https://imgur.com) por el hosting de imágenes

## 📞 Soporte

Si tienes problemas o preguntas:

1. Revisa la [documentación](docs/setup.md)
2. Busca en [Issues](https://github.com/tu-usuario/Music2Signature/issues)
3. Crea un nuevo Issue si no encuentras solución

---

# English

## 📋 Description

Music2Signature is a dynamic signature generator that displays your currently playing media from Plex Media Server. Similar to the popular [spotify-github-profile](https://github.com/kittinan/spotify-github-profile), but designed specifically for Plex users.

Perfect for:
- 🐙 **GitHub Profile README**
- 💬 **Forum Signatures**
- 📱 **Social Media Integration**
- 🎯 **Personal Branding**

---

## ✨ Features

### 🎨 Multiple Formats
- **SVG (Animated)**: Dynamic equalizer bars with smooth animations
- **PNG (Static)**: Clean, static images with equalizer visualization

### 🌓 Theme Support
- **Normal**: Clean white background with blue accents
- **Dark**: Light background with dark text for universal compatibility

### 🎵 Media Types
- **Music**: Artist, album, and track information with animated equalizer
- **TV Shows**: Show title, season, episode with static equalizer
- **Movies**: Movie title and information

### 🔧 Technical Features
- **Auto Server Detection**: Uses Plex Account API for automatic external server discovery
- **Dynamic Color Extraction**: Extracts colors from album art for personalized equalizer bars
- **Smart Text Handling**: Horizontal scrolling (marquee) for long titles
- **High-Quality Images**: 120x120px processing for sharp 80x80px display
- **Caching**: Efficient image caching to reduce server load

---

## 🛠️ Setup

### Requirements
- Plex token (obtained from https://support.plex.tv/articles/204059436/)
- Imgur Client ID (optional, for image hosting)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/D-a-r-z/Music2Signature.git
cd Music2Signature
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables**
Create a `.env` file:
```env
PLEX_TOKEN=your_plex_token_here
IMGUR_CLIENT_ID=your_imgur_client_id_here
```

**📝 Automatic user filtering:**
The app automatically filters content by the user associated with your Plex token. Each user will only see their own content by default.

4. **Run locally**
```bash
python app.py
```

Visit `http://localhost:5000` to see the dashboard.

---

## 🌐 Deployment

### Vercel (Recommended)

1. **Fork this repository**
2. **Connect to Vercel**
3. **Set environment variables**:
   - `PLEX_TOKEN`: Your Plex token
   - `IMGUR_CLIENT_ID`: Your Imgur client ID

**🔒 Automatic user filtering:**
The app automatically filters content by the user associated with your Plex token. No additional configuration needed.

The app will automatically detect your Plex server's external URL using the Plex Account API.

---

## 📖 Usage

### GitHub Profile

Add this to your GitHub profile README:

```markdown
![Plex Now Playing](https://your-vercel-url.vercel.app/api/now-playing-svg?theme=normal)
```

### Forum Signatures

For light backgrounds:
```markdown
![Plex Now Playing](https://your-vercel-url.vercel.app/api/now-playing-svg?theme=dark)
```

### Available Endpoints

- **SVG (Animated)**:
  - Normal: `/api/now-playing-svg?theme=normal`
  - Dark: `/api/now-playing-svg?theme=dark`

- **PNG (Static)**:
  - Normal: `/api/now-playing-png?theme=normal`
  - Dark: `/api/now-playing-png?theme=dark`

### Multi-User Support

For shared deployments or specific user filtering:

- **With specific token**: `?token=your_plex_token`
- **With specific user**: `?user=username`
- **Combined**: `?token=your_plex_token&user=username`

Example:
```markdown
![Plex Now Playing](https://your-vercel-url.vercel.app/api/now-playing-svg?token=your_token&user=your_username)
```

---

## 🤝 Acknowledgments

- [kittinan/spotify-github-profile](https://github.com/kittinan/spotify-github-profile) - Inspiration and base concept
- [novatorem.svg](https://github.com/kittinan/spotify-github-profile/blob/master/img/novatorem.svg) - Animated equalizer bars style
- [PlexAPI](https://github.com/pkkid/python-plexapi) - Python library for Plex API

---

## 📄 License

This project is under the MIT License. See [LICENSE](LICENSE) for more details.

---

## 🔗 Links

- **GitHub**: https://github.com/D-a-r-z/Music2Signature
- **Live Demo**: https://plex2-sign.vercel.app/
- **Vercel Deploy**: [![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/D-a-r-z/Music2Signature)

---

⭐ **¡Dale una estrella si te gusta el proyecto!** ⭐