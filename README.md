# Sonora Voice Bot

> Bot de voz con IA para el Ecosistema Sonora - Desplegado en Pipecat Cloud

## 🌐 Ecosistema Sonora

| Repo | Descripción | Deploy |
|------|-------------|--------|
| [sonora-frontend](https://github.com/Lifimastar/sonora-frontend) | UI Next.js | Coolify |
| **sonora-test** (este) | Bot de voz Pipecat | Pipecat Cloud |
| sonora-chat | API de chat texto | Coolify |

---

## 🧠 Capacidades del Bot

| Funcionalidad | Herramienta | Archivo |
|---------------|-------------|---------|
| Memoria persistente | `guardar_dato`, `borrar_dato` | `bot_tools.py` |
| Base de conocimiento | `buscar_informacion` | `bot_tools.py`, `rag.py` |
| Contar usuarios TuGuía | `contar_usuarios_tuguia` | `bot_tools.py` |
| Ver cámara | `ver_camara` | `bot_tools.py` |
| Procesar imágenes | Recibe via `user_multimodal_message` | `bot.py` |
| Procesar archivos | Recibe via `user_file_message` | `bot.py` |

---

## 📁 Estructura de Archivos

```
sonora-test/
├── bot.py                      # Entry point, handlers de mensajes
├── pipecat.toml                # Configuración Pipecat Cloud
├── Dockerfile                  # Para build de imagen
└── sonora_app/
    ├── prompts.py              # System prompt del bot
    ├── tools/
    │   └── bot_tools.py        # Herramientas del LLM
    ├── services/
    │   ├── database.py         # Servicio de BD
    │   ├── rag.py              # Búsqueda en base de conocimiento
    │   └── tuguia_database.py  # Base de datos TuGuía
    └── pipeline/
        └── conversation_handler.py # Manejo de conversación
```

---

## 🔧 Handlers de Mensajes (bot.py)

Los mensajes del frontend llegan a `on_app_message` (líneas 238-304):

| Tipo (`data.t`) | Propósito |
|-----------------|-----------|
| `user_text_message` | Texto escrito en llamada |
| `action` | set_conversation_id |
| `user_image` | Imagen legacy (no usado) |
| `user_multimodal_message` | Texto + URLs de imágenes |
| `user_file_message` | Texto + contenido de archivo |

---

## 🚀 Deploy a Pipecat Cloud

```bash
# 1. Build imagen Docker
docker build -t lifimastar/sonora-voice:0.1 .

# 2. Push a Docker Hub
docker push lifimastar/sonora-voice:0.1

# 3. Deploy a Pipecat Cloud
pcc deploy
```

---

## ⚙️ Secrets en Pipecat Cloud

Configurar en el dashboard de Pipecat Cloud:

```
DEEPGRAM_API_KEY=...
OPENAI_API_KEY=...
CARTESIA_API_KEY=...
SUPABASE_URL=...
SUPABASE_SERVICE_ROLE_KEY=...
```

---

## 🐛 Troubleshooting

### Bot no recibe imágenes
- El frontend debe enviar `user_multimodal_message` (guión bajo, no guión)
- Verificar que el handler existe en `bot.py` líneas 276-286

### Bot no recibe archivos
- El frontend debe enviar `user_file_message`
- Verificar handler en `bot.py` líneas 288-299

### Error de imports
- Asegurarse que `sonora_app/` está en PYTHONPATH
- La estructura cambió de `app/` a `sonora_app/` para Pipecat Cloud
