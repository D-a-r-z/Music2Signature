# Guía de Configuración de Music2Signature

## 📋 Requisitos Previos

1. **Servidor Plex Media Server** funcionando y accesible
2. **Token de autenticación de Plex**
3. (Opcional) **Cuenta en Imgur** para obtener Client ID (solo si quieres usar hosting externo de miniaturas)
4. **Cuenta en Vercel** (opcional, para deployment en la nube)

## 🔑 Obtener Token de Plex

### Método 1: Desde la interfaz web
1. Ve a tu servidor Plex: `http://TU_SERVIDOR:32400/web`
2. Abre las herramientas de desarrollador (F12)
3. Ve a la pestaña "Network"
4. Recarga la página
5. Busca cualquier petición y mira los headers
6. Copia el valor del header `X-Plex-Token`

### Método 2: Desde la URL
1. Ve a: `http://TU_SERVIDOR:32400/web/index.html#!/settings/account`
2. En la URL verás algo como: `...&X-Plex-Token=AQUI_ESTA_TU_TOKEN`

### Método 3: Usando curl (Linux/Mac)
```bash
curl -X POST 'https://plex.tv/users/sign_in.xml' \
  -H 'X-Plex-Client-Identifier: Music2Signature' \
  -d 'user[login]=TU_EMAIL&user[password]=TU_PASSWORD'
```

## 🖼️ Configurar Imgur (opcional)

Si quieres usar Imgur como hosting externo para miniaturas, sigue estos pasos. Si no, Plex proveerá directamente las miniaturas y no es necesario configurar Imgur.

1. Ve a [Imgur API](https://api.imgur.com/oauth2/addclient) y registra una nueva aplicación. Copia el **Client ID** generado.

## ⚙️ Configuración Local

### 1. Clonar y configurar
```bash
git clone https://github.com/tu-usuario/music2signature.git
cd music2signature
cp .env.example .env
```

### 2. Editar .env
```bash
# Configuración del servidor Plex
PLEX_URL=http://192.168.1.100:32400  # Cambia por tu IP/URL
PLEX_TOKEN=tu-token-de-plex-aqui
## 🖼️ Miniaturas y hosting (opcional)
# Configuración de Imgur
Por defecto Music2Signature usa las miniaturas proporcionadas por tu Plex Media Server; no es necesario configurar Imgur. Si por alguna razón necesitas un hosting externo para miniaturas (por ejemplo para servirlas desde un CDN), puedes integrar un servicio externo, pero no es obligatorio.

# Configuración opcional
CACHE_DURATION=60
IMAGE_WIDTH=400
IMAGE_HEIGHT=90
DEFAULT_THEME=default

# Para desarrollo local
DEBUG=true
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Probar localmente
```bash
python app.py
```

Ve a `http://localhost:5000` para verificar que todo funciona.

## 🚀 Deployment en Vercel

### 1. Instalar Vercel CLI
```bash
npm i -g vercel
```

### 2. Login en Vercel
```bash
vercel login
```

### 3. Configurar variables de entorno
```bash
vercel env add PLEX_URL
vercel env add PLEX_TOKEN
```

### 4. Hacer deployment
```bash
vercel --prod
```

## 🔧 Configuración Avanzada

### Variables de entorno disponibles

| Variable | Descripción | Valor por defecto |
|----------|-------------|-------------------|
| `PLEX_URL` | URL del servidor Plex | Requerido |
| `PLEX_TOKEN` | Token de autenticación | Requerido |
| `IMGUR_CLIENT_ID` | Client ID de Imgur | Opcional |
| `CACHE_DURATION` | Duración del cache en segundos | 60 |
| `IMAGE_WIDTH` | Ancho de la imagen | 400 |
| `IMAGE_HEIGHT` | Alto de la imagen | 90 |
| `DEFAULT_THEME` | Tema por defecto | default |
| `DEBUG` | Modo debug | false |
| `PORT` | Puerto para desarrollo local | 5000 |

### Temas disponibles
- `transparent` - Fondo transparente para embeber sobre otras superficies
- `default` - Tema clásico con fondo oscuro
- `dark` - Tema GitHub dark
- `compact` - Versión más compacta
- `minimal` - Diseño minimalista claro

## 🐛 Resolución de Problemas

### Error: "No se pudo conectar a Plex"
- Verifica que `PLEX_URL` sea correcta
- Asegúrate de que el servidor Plex esté funcionando
- Verifica que el token sea válido

### Nota: Imgur (opcional)
- Si configuras `IMGUR_CLIENT_ID`, el proyecto podrá subir miniaturas a Imgur.
- Si no lo configuras, Plex servirá las miniaturas directamente y la funcionalidad principal seguirá funcionando.

### La imagen no se actualiza
- Usa `?refresh=true` para forzar actualización
- En algunos sistemas puede fallar la carga de fuentes
- El sistema automáticamente usa fuentes por defecto como fallback

## 🔒 Seguridad
- El token de Plex da acceso completo a tu servidor
- Considera usar un usuario dedicado con permisos limitados

Una vez desplegado, añade esto a tu `README.md` del perfil:
```

![Music2Signature](https://tu-deployment.vercel.app/api/now-playing?theme=dark&width=500)
```
