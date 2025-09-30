# 🤝 Guía de Contribución

¡Gracias por tu interés en contribuir a Music2Signature! 🎉

## 🚀 Inicio Rápido

1. **Fork y clona** el repositorio
2. **Crea una rama** para tu contribución: `git checkout -b feature/tu-feature`
3. **Configura el entorno**:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   cp .env.example .env  # Configura tus credenciales
   ```
4. **Haz tus cambios** siguiendo las guidelines abajo
5. **Prueba**: `python scripts/test_connection.py && python app.py`
6. **Commit**: `git commit -m "tipo: descripción clara"`
7. **Push y PR**: Abre un Pull Request en GitHub

## 📋 Guidelines de Código

### Estilo
- **Formateo**: Usa Black (`black .`)
- **Linting**: Sigue PEP 8
- **Type hints**: Úsalos cuando sea posible
- **Docstrings**: Documenta funciones públicas

### Commits
Sigue el formato [Conventional Commits](https://conventionalcommits.org/):
```
tipo(scope): descripción

tipos: feat, fix, docs, style, refactor, test, chore
```

### Testing
```bash
# Conexión con Plex
python scripts/test_connection.py

# API completa
python app.py  # Visita localhost:5000

# Linting
black . --check
```

## 🎨 Tipos de Contribuciones

### 🐛 Bugs
- Abre un Issue con pasos para reproducir
- Incluye tu entorno (OS, Python version)

### ✨ Features
- **Nuevos temas**: Edita `api/svg_generator.py`
- **Mejoras de UX**: Interfaz más intuitiva
- **Performance**: Optimizaciones de caché/API
- **Integraciones**: Soporte para más servicios

### 📚 Documentación
- Mejoras en README/CONTRIBUTING
- Guías de configuración
- Ejemplos de uso

## 🏗️ Arquitectura

```
music2signature/
├── api/                 # Lógica de negocio
│   ├── plex_client.py   # Cliente Plex
│   └── svg_generator.py # Generador SVG
├── scripts/            # Utilidades
├── docs/              # Documentación
├── app.py            # Aplicación Flask
└── vercel.json      # Config Vercel
```

## 💡 Ideas para Contribuir

### Principiante
- [ ] Nuevos temas de colores
- [ ] Mejorar mensajes de error
- [ ] Documentación en otros idiomas

### Intermedio
- [ ] Soporte multi-usuario
- [ ] Webhooks en tiempo real
- [ ] Dashboard de configuración

### Avanzado
- [ ] Métricas y analytics
- [ ] Soporte multi-servidor Plex
- [ ] Plugin oficial para Plex

## 🆘 Ayuda

- **Preguntas**: Abre una Discussion en GitHub
- **Bugs**: Abre un Issue
- **Chat**: Únete a nuestras discusiones

## 🙏 Reconocimientos

¡Todos los contribuidores serán reconocidos! Gracias por hacer Music2Signature mejor. ⭐
