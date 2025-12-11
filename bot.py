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

from app.actions.conversation_handler import ConversationActionHandler
from app.tools.bot_tools import BotTools
from app.context import current_user_id
from app.prompts import SYSTEM_PROMPT
from app.pipeline.loggers import UserLogger, AssistantLogger
from app.pipeline.vision_processor import VisionCaptureProcessor
from dotenv import load_dotenv
from app.services.database import DatabaseService
from loguru import logger
import sys

logger.remove()
logger.add(sys.stderr, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>")

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
    db_service = DatabaseService()
    vision_processor = VisionCaptureProcessor(capture_interval=2.0)
    bot_tools = BotTools(db_service, vision_processor)
    user_logger = UserLogger(db_service)
    assistant_logger = AssistantLogger(db_service)
    

    live_options = LiveOptions(
        model="nova-2",
        language=Language.ES_419,
        smart_format=True,
        punctuate=True,
        interim_results=True,
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
        bot_tools.buscar_informacion,
        bot_tools.contar_usuarios_tuguia,
        bot_tools.crear_usuario_tuguia,
        bot_tools.contar_usuarios_por_subcategoria,
        bot_tools.guardar_dato,
        bot_tools.borrar_dato,
        bot_tools.ver_camara
    ])

    # registrar la funcion de busqueda 
    llm.register_function(
        "buscar_informacion",
        bot_tools.buscar_informacion,
        start_callback=None,
        cancel_on_interruption=False
    )

    # registrar la funcion de contar usuarios de Tu Guia
    llm.register_function(
        "contar_usuarios_tuguia",
        bot_tools.contar_usuarios_tuguia,
        start_callback=None,
        cancel_on_interruption=False
    )

    # registrar la funcion de crear usuarios en Tu Guía
    llm.register_function(
        "crear_usuario_tuguia",
        bot_tools.crear_usuario_tuguia,
        start_callback=None,
        cancel_on_interruption=False
    )

    # registrar la funcion de contar usuarios por subcategoria
    llm.register_function(
        "contar_usuarios_por_subcategoria",
        bot_tools.contar_usuarios_por_subcategoria,
        start_callback=None,
        cancel_on_interruption=False
    )

    # guardar en memoria
    llm.register_function("guardar_dato", bot_tools.guardar_dato)

    # borrar de memoria
    llm.register_function("borrar_dato", bot_tools.borrar_dato)

    # registrar la funcion de ver camara
    llm.register_function(
        "ver_camara",
        bot_tools.ver_camara,
        start_callback=None,
        cancel_on_interruption=False
    )

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
    ]

    context = LLMContext(messages, tools=tools)
    context_aggregator = LLMContextAggregatorPair(context)
    bot_tools.set_context(context)
    conversation_handler = ConversationActionHandler(db_service, context)
    rtvi = RTVIProcessor(config=RTVIConfig(config=[]))
    
    action = RTVIAction(
        service="system",
        action="set_conversation_id",
        name="set_conversation_id",
        handler=conversation_handler.handle_action,
        result="bool"
    )

    rtvi.register_action(action)

    pipeline = Pipeline(
        [
            transport.input(),  # Microfono
            vision_processor, # frames de video
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
            allow_interruptions=True,
            enable_metrics=True,
            enable_usage_metrics=True,
        ),
        observers=[RTVIObserver(rtvi)],
    )

    conversation_handler.set_task(task)

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
                        await conversation_handler.handle_action(None, None, args)
            
            # 3. Interceptar IMAGENES del usuario
            if message.get("label") == "rtvi-ai" and message.get("type") == "client-message":
                data = message.get("data", {})
                if data.get("t") == "user_image":
                    image_base64 = data.get("d", {}).get("image")
                    if image_base64:
                        logger.info("Recibida imagen del usuario procesando...")
                        await conversation_handler.handle_user_image(image_base64)
                        return
                        
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

    vad_analyzer = SileroVADAnalyzer(params=VADParams(
        confidence=0.8, # Sensibilidad mas baja (requiere voz mas clara)
        min_speech_duration_ms=300, # Ignorar ruidos cortos (clicks, golpes)
        min_silence_duration_ms=500
    ))

    transport_params = {
        "daily": lambda: DailyParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            vad_analyzer=vad_analyzer,
            transcription_enabled=True,
        ),
        "webrtc": lambda: TransportParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            camera_in_enabled=True,
            vad_analyzer=vad_analyzer,
        ),
    }

    transport = await create_transport(runner_args, transport_params)

    await run_bot(transport, runner_args)


if __name__ == "__main__":
    from pipecat.runner.run import main

    main()
