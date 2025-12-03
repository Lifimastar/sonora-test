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
import datetime
import os
import time

from app.prompts import SYSTEM_PROMPT
from app.pipeline.loggers import UserLogger, AssistantLogger
from dotenv import load_dotenv
from app.services.database import DatabaseService
from loguru import logger
from app.tools.definitions import buscar_informacion, contar_usuarios_tuguia, crear_usuario_tuguia, contar_usuarios_por_subcategoria, guardar_dato

print("🚀 Starting Pipecat bot...")
print("⏳ Loading models and imports (20 seconds, first run only)\n")

logger.info("Loading Local Smart Turn Analyzer V3...")
from pipecat.audio.turn.smart_turn.local_smart_turn_v3 import LocalSmartTurnAnalyzerV3

logger.info("✅ Local Smart Turn Analyzer V3 loaded")
logger.info("Loading Silero VAD model...")
from pipecat.audio.vad.silero import SileroVADAnalyzer

logger.info("✅ Silero VAD model loaded")

from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.frames.frames import LLMRunFrame, TextFrame, TranscriptionFrame, UserStartedSpeakingFrame, UserStoppedSpeakingFrame

logger.info("Loading pipeline components...")

from pipecat.adapters.schemas.tools_schema import ToolsSchema
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import LLMContextAggregatorPair
from pipecat.processors.frameworks.rtvi import RTVIConfig, RTVIObserver, RTVIProcessor, RTVIAction
from pipecat.runner.types import RunnerArguments
from pipecat.runner.utils import create_transport
from pipecat.services.cartesia.tts import CartesiaTTSService, GenerationConfig
from pipecat.services.deepgram.stt import DeepgramSTTService, LiveOptions
from pipecat.services.llm_service import FunctionCallParams
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.services.openai.tts import OpenAITTSService
from pipecat.transcriptions.language import Language
from pipecat.transports.base_transport import BaseTransport, TransportParams

logger.info("✅ All components loaded successfully!")

load_dotenv(override=True)



async def run_bot(transport: BaseTransport, runner_args: RunnerArguments):
    logger.info(f"Starting bot")

    # inicializar db
    db_service = DatabaseService()

    TEST_USER_ID = os.getenv("TEST_USER_ID")
    db_service.user_id = TEST_USER_ID

    # conversation_id = db_service.create_conversation(
    #     title="Llamada Pipecat con Usuario",
    #     user_id=TEST_USER_ID)

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

    tts = CartesiaTTSService(
        api_key=os.getenv("CARTESIA_API_KEY"),
        voice_id="5c5ad5e7-1020-476b-8b91-fdcbe9cc313c", # Voz: Daniela (Mexicana/Latina)
        model="sonic-multilingual",
        params=CartesiaTTSService.InputParams(
            generation_config=GenerationConfig(
                emotion="positivity:high",
                speed=1.0
            )
        ),
    )

    # tts = OpenAITTSService(
    #     api_key=os.getenv("OPENAI_API_KEY"),
    #     voice="nova",
    #     model="tts-1",
    # )

    llm = OpenAILLMService(api_key=os.getenv("OPENAI_API_KEY"), model="gpt-4o")

    # crear el esquema de herramientas
    tools = ToolsSchema(standard_tools=[
        buscar_informacion,
        contar_usuarios_tuguia,
        crear_usuario_tuguia,
        contar_usuarios_por_subcategoria,
        guardar_dato
    ])

    # registrar la funcion de busqueda 
    llm.register_function(
        "buscar_informacion",
        buscar_informacion,
        start_callback=None,
        cancel_on_interruption=False
    )

    # registrar la funcion de contar usuarios de Tu Guia
    llm.register_function(
        "contar_usuarios_tuguia",
        contar_usuarios_tuguia,
        start_callback=None,
        cancel_on_interruption=False
    )

    # registrar la funcion de crear usuarios en Tu Guía
    llm.register_function(
        "crear_usuario_tuguia",
        crear_usuario_tuguia,
        start_callback=None,
        cancel_on_interruption=False
    )

    # registrar la funcion de contar usuarios por subcategoria
    llm.register_function(
        "contar_usuarios_por_subcategoria",
        contar_usuarios_por_subcategoria,
        start_callback=None,
        cancel_on_interruption=False
    )

    # registrar la nueva tool
    llm.register_function("guardar_dato", guardar_dato)

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
    ]

    context = LLMContext(messages, tools=tools)
    context_aggregator = LLMContextAggregatorPair(context)

    # definir la accion que ejecutara el handler
    async def set_conversation_action(processor, service, arguments):
        conversation_id = arguments.get("conversation_id")
        logger.info(f"🔄 Configurando conversación: {conversation_id}")

        memories = db_service.get_all_memories()
        if memories:
            memory_list = [f"- {k}: {v}" for k, v in memories.items()]
            memory_text = "\nDATOS RECORDADOS:\n" + "\n".join(memory_list)
            logger.info(f"Memorias cargadas: {len(memories)}")
        
            context.add_message({
                "role": "system",
                "content": f"Informacion persistente que debe recordar:\n{memory_text}"
            })
        
        messages_to_send = []
        
        if conversation_id:
            # CASO 1: Reanudar conversación existente
            db_service.conversation_id = conversation_id
            logger.info("✅ ID de conversación establecido.")
            
            # Cargar historial
            history = db_service.get_conversation_history(conversation_id)
            
            if history:
                logger.info(f"📜 Inyectando {len(history)} mensajes al contexto")
                # Inyectar historial en el contexto del LLM
                for msg in history:
                    context.add_message({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
                
                # Saludo de re-conexión
                messages_to_send = [
                    {"role": "system", "content": "El usuario ha vuelto. Saluda brevemente (ej: 'Hola de nuevo') y pregunta en qué quedaron."}
                ]
            else:
                 messages_to_send = [{"role": "system", "content": "Saluda al usuario."}]

        else:
            # CASO 2: Nueva conversación
            logger.info("✨ Iniciando nueva sesión.")
            db_service.conversation_id = None # Asegurar que esté limpio
            messages_to_send = [
                {"role": "system", "content": "Saluda brevemente como asistente de Red Futura."}
            ]

        # Disparar el saludo AHORA
        if messages_to_send:
            logger.info(f"📨 Enviando instrucciones al LLM: {messages_to_send}")
            for msg in messages_to_send:
                context.add_message(msg)
            await task.queue_frame(LLMRunFrame())
        
        return True

    rtvi = RTVIProcessor(config=RTVIConfig(config=[]))
    
    action = RTVIAction(
        service="system",
        action="set_conversation_id",
        name="set_conversation_id",
        handler=set_conversation_action,
        result="bool"
    )

    rtvi.register_action(action)

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
        logger.info(f"Client connected. Waiting for conversation config...")
        # NO enviamos mensajes aquí. Esperamos la acción del frontend.

    @transport.event_handler("on_app_message")
    async def on_app_message(transport, message, sender):
        logger.info(f"📨 App message received: {message}")
        try:
            # 1. Interceptar mensajes de texto del usuario
            if message.get("label") == "rtvi-ai" and message.get("type") == "client-message":
                data = message.get("data", {})
                if data.get("t") == "user_text_message":
                    text = data.get("d", {}).get("text")
                    if text:
                        logger.info(f"💬 Texto recibido del usuario: {text}")
                        # Inyectar frames para simular un turno de usuario
                        await task.queue_frame(UserStartedSpeakingFrame())
                        await task.queue_frame(TranscriptionFrame(text=text, user_id="user", timestamp=datetime.datetime.now().isoformat()))
                        await task.queue_frame(UserStoppedSpeakingFrame())
                        return

            # 2. Interceptar set_conversation_id
            if message.get("label") == "rtvi-ai" and message.get("type") == "client-message":
                data = message.get("data", {})
                if data.get("t") == "action":
                    action_data = data.get("d", {})
                    if action_data.get("action") == "set_conversation_id":
                        args = action_data.get("arguments", {})
                        logger.info(f"⚡ Interceptado set_conversation_id manualmente: {args}")
                        await set_conversation_action(None, None, args)
        except Exception as e:
            logger.error(f"Error processing app message: {e}")
            import traceback
            logger.error(traceback.format_exc())

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
            vad_analyzer=SileroVADAnalyzer(params=VADParams(stop_secs=0.8)),
        ),
        "webrtc": lambda: TransportParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            vad_analyzer=SileroVADAnalyzer(params=VADParams(stop_secs=0.8)),
        ),
    }

    transport = await create_transport(runner_args, transport_params)

    await run_bot(transport, runner_args)


if __name__ == "__main__":
    from pipecat.runner.run import main

    main()
