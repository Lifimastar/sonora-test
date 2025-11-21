#
# Copyright (c) 2024–2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""Pipecat Quickstart Example.

The example runs a simple voice AI bot that you can connect to using your
browser and speak with it. You can also deploy this bot to Pipecat Cloud.

Required AI services:
- Deepgram (Speech-to-Text)
- OpenAI (LLM)
- Cartesia (Text-to-Speech)

Run the bot using::

    uv run bot.py
"""

import aiohttp
import os
import secrets
import string

from conversation_logger import UserLogger, AssistantLogger
from dotenv import load_dotenv
from database_service import DatabaseService
from loguru import logger
from rag_service import get_relevant_context

print("🚀 Starting Pipecat bot...")
print("⏳ Loading models and imports (20 seconds, first run only)\n")

logger.info("Loading Local Smart Turn Analyzer V3...")
from pipecat.audio.turn.smart_turn.local_smart_turn_v3 import LocalSmartTurnAnalyzerV3

logger.info("✅ Local Smart Turn Analyzer V3 loaded")
logger.info("Loading Silero VAD model...")
from pipecat.audio.vad.silero import SileroVADAnalyzer

logger.info("✅ Silero VAD model loaded")

from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.frames.frames import LLMRunFrame

logger.info("Loading pipeline components...")

from pipecat.adapters.schemas.tools_schema import ToolsSchema
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import LLMContextAggregatorPair
from pipecat.processors.frameworks.rtvi import RTVIConfig, RTVIObserver, RTVIProcessor
from pipecat.runner.types import RunnerArguments
from pipecat.runner.utils import create_transport
from pipecat.services.cartesia.tts import CartesiaTTSService
from pipecat.services.deepgram.stt import DeepgramSTTService, LiveOptions
from pipecat.services.llm_service import FunctionCallParams
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.services.openai.tts import OpenAITTSService
from pipecat.transcriptions.language import Language
from pipecat.transports.base_transport import BaseTransport, TransportParams

logger.info("✅ All components loaded successfully!")

load_dotenv(override=True)

def generar_password_segura(longitud=16):
    """Genera una contrasena segura aleatoria."""
    caracteres = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(secrets.choice(caracteres) for _ in range(longitud))
    return password

async def crear_usuario_supabase(params: FunctionCallParams):
    """Crea un usuario en Supabase a través del webhook de n8n.
    
    Esta función crea un nuevo usuario en Supabase. Puede generar email y password 
    aleatorios o usar los proporcionados por el usuario.
    
    Args:
        params: Parámetros de la llamada a función que contiene:
            - email (opcional): Email del usuario. Si no se proporciona, se genera uno 
              aleatorio con formato usuario_XXXXXXXX@sonora.com
            - password (opcional): Contraseña del usuario. Si no se proporciona, se 
              genera una contraseña segura aleatoria.
    
    Returns:
        Un diccionario con el resultado de la creación del usuario.
    """
    try:
        # extraer argumentos del LLM
        email = params.arguments.get("email", None)
        password = params.arguments.get("password", None)

        # generar email aleatorio si no se proporciona
        if not email:
            random_id = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(8))
            email = f"usuario_{random_id}@sonora.com"
        
        # generar contrasena segura si no se proporciona
        if not password:
            password = generar_password_segura()
        
        # URL del webhook de n8n
        webhook_url = os.getenv("N8N_WEBHOOK_URL")

        # preparar el mensaje para n8n
        mensaje = f"crear usuario con email {email} y password {password}"

        # llamar al webhook
        async with aiohttp.ClientSession() as session:
            async with session.post(
                webhook_url,
                json={"pregunta": mensaje},
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    resultado = await response.json()

                    # preparar respuesta exitosa
                    respuesta = {
                        "success": True,
                        "email": email,
                        "password": password,
                        "mensaje": f"Usuario {email} creado exitosamente.",
                        "respuesta_n8n": resultado.get("respuesta", "")
                    }
                else:
                    respuesta = {
                        "success": False,
                        "error": f"Error al crear usuario: HTTP {response.status}"
                    }
        
        # devuelve el resultado al LLM
        await params.result_callback(respuesta)

    except Exception as e:
        # manejar errores
        await params.result_callback({
            "success": False,
            "error": f"Error al crear usuario: {str(e)}"
        })


async def buscar_informacion(params: FunctionCallParams):
    """
    Busca información relevante en la base de conocimiento sobre contratos, términos y servicios.
    
    Usa esta función SIEMPRE que el usuario pregunte sobre:
    - Contratos (adheridos o asesores)
    - Términos y condiciones
    - Servicios, obligaciones, derechos o prohibiciones
    - Información de contacto o legal
    
    :param params: Parámetros de la llamada, debe incluir 'query' en los argumentos.
    """
    try:
        # Extraer la pregunta o tema de búsqueda
        query = params.arguments.get("query") or params.arguments.get("pregunta")
        
        if not query:
            # Si no hay query, intentar usar el último mensaje del usuario o pedir aclaración
            resultado = {
                "success": False,
                "mensaje": "No se especificó qué buscar."
            }
        else:
            logger.info(f"🔍 Buscando en RAG: {query}")
            # Buscar en la base de conocimiento
            context = get_relevant_context(query)
            
            resultado = {
                "success": True,
                "informacion": context,
                "mensaje": "Información encontrada. Úsala para responder al usuario."
            }
        
        # Devolver el resultado al LLM
        await params.result_callback(resultado)
        
    except Exception as e:
        logger.error(f"❌ Error en búsqueda RAG: {e}")
        await params.result_callback({
            "success": False,
            "error": str(e)
        })

async def run_bot(transport: BaseTransport, runner_args: RunnerArguments):
    logger.info(f"Starting bot")

    # inicializar db y crear conversacion
    db_service = DatabaseService()

    TEST_USER_ID = os.getenv("TEST_USER_ID")

    conversation_id = db_service.create_conversation(
        title="Llamada Pipecat con Usuario",
        user_id=TEST_USER_ID)

    # crear el logger
    user_logger = UserLogger(db_service)
    assistant_logger = AssistantLogger(db_service)

    # STT en espanol
    live_options = LiveOptions(
        model="nova-2",
        language=Language.ES_419,
        interim_results=True,
        smart_format=True,
        punctuate=True
    )

    stt = DeepgramSTTService(
        api_key=os.getenv("DEEPGRAM_API_KEY"), 
        live_options=live_options,
    )

    # tts = CartesiaTTSService(
    #     api_key=os.getenv("CARTESIA_API_KEY"),
    #     voice_id="15d0c2e2-8d29-44c3-be23-d585d5f154a1",
    #     model="sonic-2",
    #     params=CartesiaTTSService.InputParams(
    #         language=Language.ES,
    #         speed="normal",
    #     ),
    # )

    tts = OpenAITTSService(
        api_key=os.getenv("OPENAI_API_KEY"),
        voice="nova",
    )

    llm = OpenAILLMService(api_key=os.getenv("OPENAI_API_KEY"))

    # crear el esquima de herramientas pasando la funcion directamente
    tools = ToolsSchema(standard_tools=[
        crear_usuario_supabase,
        buscar_informacion
        ])

    # registrar la funcion de crear usuarios
    llm.register_function(
        "crear_usuario_supabase",
        crear_usuario_supabase,
        start_callback=None,
        cancel_on_interruption=False
    )

    # registrar la funcion de busqueda 
    llm.register_function(
        "buscar_informacion",
        buscar_informacion,
        start_callback=None,
        cancel_on_interruption=False
    )

    messages = [
        {
            "role": "system",
            "content": """Eres un asistente experto y amigable del Ecosistema Red Futura (que incluye Tu Guía AR).

            CAPACIDADES:
            1. 🔍 BUSCAR INFORMACIÓN: Tienes acceso a una base de conocimiento completa con contratos, términos y condiciones.
            - Cuando te pregunten sobre reglas, servicios, obligaciones, contratos o términos legales, DEBES usar la función `buscar_informacion`.
            - NO inventes información legal. Búscala siempre.

            2. 👤 CREAR USUARIOS: Puedes registrar nuevos usuarios en el sistema.
            - Usa la función [crear_usuario_supabase](cci:1://file:///c:/Users/luisf/ProyectosPython/bot-sonora/pipecat-quickstart/bot.py:78:0-146:10).
            - Si no te dan un email, genera uno aleatorio.
            - Siempre genera contraseña segura.

            INSTRUCCIONES DE INTERACCIÓN:
            - Tu objetivo es ayudar y resolver dudas con precisión.
            - Si usas `buscar_informacion`, basa tu respuesta EXCLUSIVAMENTE en lo que encuentres.
            - Si la búsqueda no arroja resultados, dilo honestamente y ofrece contactar a soporte (contacto@redesfutura.com).
            - Mantén un tono profesional pero cercano y amable.
            - Habla siempre en español.

            IMPORTANTE:
            - Para preguntas simples de saludo ("hola", "quién eres"), responde directamente sin buscar.
            - Para CUALQUIER pregunta sobre el servicio o contratos, USA LA HERRAMIENTA DE BÚSQUEDA.""",
        },
    ]

    context = LLMContext(messages, tools=tools)
    context_aggregator = LLMContextAggregatorPair(context)

    rtvi = RTVIProcessor(config=RTVIConfig(config=[]))

    pipeline = Pipeline(
        [
            transport.input(),  # Microfono
            rtvi,  # RTVI processor
            stt, # Audio -> Texto (User)
            user_logger, # capturar user
            context_aggregator.user(),  # Agregar user al contexto
            llm,  # Contexto -> Texto (Assistant)
            assistant_logger, # capturar asistente
            tts,  # Texto -> Audio
            transport.output(),  # Altavoz
            context_aggregator.assistant(),  # Agrega assistant al contexto
        ]
    )

    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            enable_metrics=True,
            enable_usage_metrics=True,
        ),
        observers=[RTVIObserver(rtvi)],
    )

    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        logger.info(f"Client connected")
        # Kick off the conversation.
        messages.append({"role": "system", "content": "Saluda y preséntate como el asistente inteligente de Red Futura. Menciona que puedes ayudar con dudas sobre contratos, servicios o crear cuentas de usuario."})
        await task.queue_frames([LLMRunFrame()])

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info(f"Client disconnected")
        await task.cancel()

    runner = PipelineRunner(handle_sigint=runner_args.handle_sigint)

    await runner.run(task)


async def bot(runner_args: RunnerArguments):
    """Main bot entry point for the bot starter."""

    transport_params = {
        "daily": lambda: DailyParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            vad_analyzer=SileroVADAnalyzer(params=VADParams(stop_secs=0.2)),
            turn_analyzer=LocalSmartTurnAnalyzerV3(),
        ),
        "webrtc": lambda: TransportParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            vad_analyzer=SileroVADAnalyzer(params=VADParams(stop_secs=0.2)),
            turn_analyzer=LocalSmartTurnAnalyzerV3(),
        ),
    }

    transport = await create_transport(runner_args, transport_params)

    await run_bot(transport, runner_args)


if __name__ == "__main__":
    from pipecat.runner.run import main

    main()
