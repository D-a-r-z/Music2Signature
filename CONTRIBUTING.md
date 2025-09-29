# Contribuir a Music2Signature

¡Gracias por tu interés en contribuir a Music2Signature! 🎉

## 🚀 Cómo Contribuir

### 1. Fork del Repositorio
```bash
git clone https://github.com/tu-usuario/music2signature.git
cd music2signature
```

### 2. Crear Rama para tu Feature
```bash
git checkout -b feature/nueva-funcionalidad
```

### 3. Configurar Entorno de Desarrollo
```bash
cp .env.example .env
# Editar .env con tus credenciales
pip install -r requirements.txt
```

### 4. Probar tu Código
```bash
python scripts/test_connection.py
python app.py
```

### 5. Commit y Push
```bash
git add .
git commit -m "feat: descripción de tu cambio"
git push origin feature/nueva-funcionalidad
```

### 6. Crear Pull Request
Ve a GitHub y crea un Pull Request con:
- Descripción clara del cambio
- Screenshots si es relevante
- Pruebas realizadas

## 🎨 Tipos de Contribuciones Bienvenidas

### 🐛 Bug Fixes
- Reporta bugs usando GitHub Issues
- Incluye pasos para reproducir
- Especifica tu entorno (OS, Python version, etc.)

### ✨ Nuevas Funcionalidades
- **Nuevos temas visuales**
- **Soporte para más tipos de media**
- **Integración con otros servicios**
- **Mejoras de rendimiento**

### 📚 Documentación
- Mejoras en README
- Guías de configuración
- Ejemplos de uso
- Traducciones

### 🎨 Nuevos Temas
Para añadir un nuevo tema, edita `api/image_generator.py`:

```python
'mi_tema': {
    'bg_color': '#color_fondo',
    'text_color': '#color_texto',
    'accent_color': '#color_acento',
    'progress_bg': '#color_barra_fondo',
    'progress_fg': '#color_barra_progreso',
    'font_title_size': 16,
    'font_subtitle_size': 12,
    'font_time_size': 10,
}
```

## 📋 Guidelines de Código

### Estilo de Código
- Usar **Black** para formateo: `black .`
- Seguir **PEP 8**
- Usar **type hints** cuando sea posible
- Documentar funciones con docstrings

### Estructura de Commits
```
tipo(scope): descripción corta

Descripción más detallada si es necesaria

- feat: nueva funcionalidad
- fix: corrección de bug
- docs: cambios en documentación
- style: formateo, no cambios de código
- refactor: refactorización
- test: añadir/modificar tests
```

### Testing
```bash
# Probar conexiones
python scripts/test_connection.py

# Probar aplicación
python app.py
# Ve a http://localhost:5000

# Linting
flake8 .
black . --check
```

## 🏗️ Arquitectura del Proyecto

```
music2signature/
├── api/
│   ├── plex_client.py      # Conexión con Plex
│   ├── image_generator.py  # Generación de imágenes
│   └── imgur_client.py     # Subida a Imgur
├── docs/
│   └── setup.md           # Documentación
├── scripts/
│   └── test_connection.py # Scripts de prueba
├── app.py                 # Aplicación principal
├── requirements.txt       # Dependencias
├── vercel.json           # Configuración Vercel
└── README.md
```

## 🤝 Proceso de Review

1. **Automated checks** deben pasar
2. **Manual review** por mantenedores
3. **Testing** en diferentes entornos
4. **Merge** una vez aprobado

## 💡 Ideas para Contribuir

### Fácil (Good First Issues)
- [ ] Añadir nuevos temas de colores
- [ ] Mejorar mensajes de error
- [ ] Añadir más emojis según tipo de media
- [ ] Documentación en otros idiomas

### Intermedio
- [ ] Soporte para múltiples usuarios
- [ ] Cache más inteligente
- [ ] Webhooks de Plex para updates en tiempo real
- [ ] Integración con otros servicios de imágenes

### Avanzado
- [ ] Dashboard web para configuración
- [ ] Métricas y analytics
- [ ] Soporte para múltiples servidores Plex
- [ ] Plugin para Plex Media Server

## 🆘 Necesitas Ayuda?

- 💬 Abre una **Discussion** para preguntas generales
- 🐛 Abre un **Issue** para bugs
- 📧 Contacta a los mantenedores

## 🙏 Reconocimientos

Todos los contribuidores serán añadidos al README. ¡Gracias por hacer Music2Signature mejor! 🎉
