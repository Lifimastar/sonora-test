# Sonora Test - Bot de Voz

Bot de voz con Pipecat Framework desplegado en Pipecat Cloud.

## Ecosistema Sonora

Este backend es parte de un sistema de 3 repositorios:

| Repositorio | Descripción | Despliegue |
|-------------|-------------|------------|
| [sonora-frontend](https://github.com/Lifimastar/sonora-frontend) | Frontend Next.js | Coolify |
| **sonora-test** (este) | Bot de voz Pipecat | Pipecat Cloud |
| [sonora-chat](https://github.com/Lifimastar/sonora-chat) | API de chat | Coolify |

**Flujo:** Usuario → sonora-frontend → Pipecat Cloud → sonora-test → Supabase

## Tecnologías

- **Framework:** Pipecat (pipecat-ai)
- **Lenguaje:** Python 3.10+
- **STT:** Deepgram
- **LLM:** OpenAI GPT-4
- **TTS:** Cartesia
- **Transporte:** DailyTransport (producción) / SmallWebRTCTransport (local)
- **DB:** Supabase

## Estructura del Proyecto

```
sonora-test/
├── bot.py                    # Bot principal (entry point)
├── sonora_app/               # Módulo de la aplicación
│   ├── __init__.py
│   ├── actions/              # Acciones del bot
│   │   └── conversation_handler.py
│   └── llm.py                # Configuración del LLM
├── pcc-deploy.toml           # Configuración de Pipecat Cloud
├── pyproject.toml            # Dependencias Python (UV)
├── Dockerfile                # Para build de imagen Docker
└── .env                      # Variables de entorno (NO COMMITEAR)
```

## Configuración

### Variables de Entorno (.env)

```env
# APIs de AI
DEEPGRAM_API_KEY=xxx
OPENAI_API_KEY=xxx
CARTESIA_API_KEY=xxx

# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=xxx
```

### pcc-deploy.toml

```toml
[image]
name = "lifimastar/sonora-voice"
tag = "0.1"

[deploy]
agent_name = "sonora-voice"
secret_set = "sonora-secrets"
```

## Desarrollo Local

```bash
# Instalar dependencias con UV
uv sync

# Ejecutar bot localmente (SmallWebRTC)
uv run python bot.py --local

# O con variables de entorno
DEEPGRAM_API_KEY=xxx OPENAI_API_KEY=xxx uv run python bot.py --local
```

## Despliegue a Pipecat Cloud

### 1. Build de la imagen Docker

```bash
docker build -t lifimastar/sonora-voice:0.1 .
```

### 2. Push a Docker Hub

```bash
docker push lifimastar/sonora-voice:0.1
```

### 3. Deploy a Pipecat Cloud

```bash
pcc deploy
```

### 4. Verificar estado

```bash
pcc agent list
pcc agent logs sonora-voice
```

## Arquitectura del Bot

```
┌─────────────────────────────────────────────────────────────┐
│                       Pipeline Pipecat                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Audio In → Deepgram STT → LLM (OpenAI) → Cartesia TTS → Audio Out
│                  │              │              │                   │
│                  ▼              ▼              ▼                   │
│            Transcript    Context/Tools    TTS Audio              │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │    Supabase     │
                    │  (Persistencia) │
                    └─────────────────┘
```

## Flujo de Mensajes

1. **Frontend envía `set_conversation_id`**
   ```json
   {
     "action": "set_conversation_id",
     "arguments": {
       "conversation_id": "uuid",
       "user_id": "uuid"
     }
   }
   ```

2. **Bot recibe y configura** el ID de conversación

3. **Bot saluda** al usuario (mensaje inicial configurado)

4. **Conversación normal** - mensajes van y vienen

5. **Mensajes se guardan** en Supabase automáticamente

## Manejo de Actions

El bot puede recibir acciones del frontend via `sendClientMessage`:

```python
# En bot.py, líneas ~256-263
if action_data.get("action") == "set_conversation_id":
    args = action_data.get("arguments", {})
    logger.info(f"Interceptado set_conversation_id: {args}")
    # Configura el conversation_id para persistencia
```

## Secretos en Pipecat Cloud

Los secretos se configuran en el Dashboard de Pipecat Cloud:

1. Ir a **Settings** → **Secrets**
2. Crear conjunto de secretos llamado `sonora-secrets`
3. Agregar las claves API (DEEPGRAM, OPENAI, CARTESIA, SUPABASE)

## Comandos Útiles

```bash
# Ver agentes
pcc agent list

# Ver logs en tiempo real
pcc agent logs sonora-voice -f

# Reiniciar agente
pcc agent restart sonora-voice

# Eliminar agente
pcc agent delete sonora-voice

# Ver deployments
pcc deployment list
```

## Problemas Comunes

| Problema | Causa | Solución |
|----------|-------|----------|
| `No module pipecat.transports.daily` | Falta dependencia | Agregar `daily` a extras de pipecat-ai |
| `Circular import` | Imports de app.* en top-level | Mover imports dentro de funciones |
| Bot no responde | Secretos no configurados | Verificar en Pipecat Cloud Dashboard |
| STUN 401 | Usando TURN servers manuales | Dejar que Pipecat Cloud maneje TURN |

## Notas Importantes

- La imagen Docker usa `dailyco/pipecat-base:latest` como base
- Los imports de `sonora_app.*` deben ser dentro de `run_bot()`, no a nivel de módulo
- El `create_transport` se encarga de elegir el transporte correcto según el entorno
- Pipecat Cloud maneja automáticamente los servidores TURN/STUN
