# Bot Sonora - Backend

Backend del asistente de voz y texto para el Ecosistema Red Futura.

## 🚀 Tecnologías

- **Python 3.11+** con `uv` package manager
- **Pipecat** - Framework de voz en tiempo real
- **FastAPI** - API REST para chat de texto
- **OpenAI** - LLM (GPT-4o-mini) y visión
- **Deepgram** - Speech-to-Text
- **Cartesia** - Text-to-Speech
- **Supabase** - Base de datos y almacenamiento

## ✨ Características

- ✅ Chat de voz en tiempo real (WebRTC)
- ✅ Chat de texto sin llamada
- ✅ Subida de imágenes (con descripción por IA)
- ✅ Subida de archivos de texto (.txt, .md, .json)
- ✅ Integración con herramientas (buscar info, guardar datos, etc.)
- ✅ Memoria persistente por usuario
- ✅ Historial de conversaciones

## 📦 Instalación

```bash
# Instalar uv si no lo tienes
pip install uv

# Instalar dependencias
uv sync

# Configurar variables de entorno
cp env.example .env
# Edita .env con tu API keys
```

## 🔧 Ejecución

### Desarrollo Local (Un solo comando)

```bash
uv run python start.py
```

Esto inicia **ambos servidores**:
- **Puerto 7860**: Servidor de voz (Pipecat/WebRTC)
- **Puerto 7861**: API de chat de texto (FastAPI)

### Solo servidor de voz

```bash
uv run bot.py
```

### Solo API de texto

```bash
uv run -m uvicorn app.api.server:app --host 0.0.0.0 --port 7861
```

## 🐳 Docker

```bash
# Construir y ejecutar
docker-compose up --build

# Solo construir
docker-compose build

# Ejecutar en background
docker-compose up -d
```

## 🔑 Variables de Entorno

```env
# APIs de IA
DEEPGRAM_API_KEY=...
OPENAI_API_KEY=...
CARTESIA_API_KEY=...

# Base de datos principal (sonoraDB)
SUPABASE_URL=...
SUPABASE_SERVICE_KEY=...

# Base de datos secundaria (Tu Guía)
TUGUIA_SUPABASE_URL=...
TUGUIA_SUPABASE_SERVICE_KEY=...
```

## 📁 Estructura

```
pipecat-quickstart/
├── bot.py              # Servidor de voz (Pipecat)
├── start.py            # Script unificado (voz + texto)
├── app/
│   ├── api/            # Endpoints FastAPI
│   │   ├── chat_api.py # Chat de texto + upload
│   │   └── server.py   # Servidor FastAPI
│   ├── services/       # Servicios (DB, RAG, TuGuía)
│   ├── prompts.py      # System prompt del bot
│   └── tools/          # Herramientas del LLM
├── Dockerfile
└── docker-compose.yml
```

## 🔗 API Endpoints

### Chat de Texto
- `POST /api/chat` - Enviar mensaje de texto
- `POST /api/upload` - Subir imagen o archivo

### Voz (WebRTC)
- `POST /api/offer` - Iniciar conexión WebRTC
- `GET /client` - Cliente web de prueba

## 📝 Notas

- El timeout de OpenAI está configurado a 30 segundos
- Tamaño máximo de archivo: 10MB
- Las imágenes se procesan con GPT-4o-mini Vision
