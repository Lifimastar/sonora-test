from loguru import logger
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.pipeline.task import PipelineTask
from pipecat.frames.frames import LLMRunFrame
from app.services.database import DatabaseService

class ConversationActionHandler:
    def __init__(self, db_service: DatabaseService, context: LLMContext):
        self.db_service = db_service
        self.context = context
        self.task: PipelineTask | None = None

    def set_task(self, task: PipelineTask):
        self.task = task

    async def handle_action(self, processor, service, arguments):
        conversation_id = arguments.get("conversation_id")
        user_id = arguments.get("user_id")

        if user_id:
            logger.info(f"Configurando usuario: {user_id}")
            # Importar aquí para evitar probelas de referencia circular si las hubiera
            from app.context import current_user_id
            current_user_id.set(user_id)
            self.db_service.user_id = user_id
            self.db_service.ensure_user_exists(user_id)
        
        logger.info(f"🔄 Configurando conversación: {conversation_id}")

        memories = self.db_service.get_all_memories()
        if memories:
            memory_list = [f"- {k}: {v}" for k, v in memories.items()]
            memory_text = "\nDATOS RECORDADOS:\n" + "\n".join(memory_list)
            logger.info(f"Memorias cargadas: {len(memories)}")
        
            self.context.add_message({
                "role": "system",
                "content": f"Informacion persistente que debe recordar:\n{memory_text}"
            })
        
        messages_to_send = []
        
        if conversation_id:
            # CASO 1: Reanudar conversación existente
            self.db_service.conversation_id = conversation_id
            logger.info("✅ ID de conversación establecido.")
            
            # Cargar historial
            history = self.db_service.get_conversation_history(conversation_id)
            
            if history:
                logger.info(f"📜 Inyectando {len(history)} mensajes al contexto")
                # Inyectar historial en el contexto del LLM
                for msg in history:
                    self.context.add_message({
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
            self.db_service.conversation_id = None # Asegurar que esté limpio
            messages_to_send = [
                {"role": "system", "content": "Saluda brevemente como asistente de Red Futura."}
            ]

        # Disparar el saludo AHORA
        if messages_to_send:
            logger.info(f"📨 Enviando instrucciones al LLM: {messages_to_send}")
            for msg in messages_to_send:
                self.context.add_message(msg)
            
            if self.task:
                await self.task.queue_frame(LLMRunFrame())
            else:
                logger.error("❌ Task no seteado en ConversationActionHandler, no se puede enviar LLMRunFrame")
        
        return True

    async def handle_user_image(self, image_base64: str):
        """Maneja imagenes subidas por el usuario."""
        if not image_base64:
            return
        
        logger.info(f"Recibida imagen del usuario. Tamano: {len(image_base64)} caracteres")

        self.context.add_message({
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "He subido una imagen. Analizala."
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image_base64
                    }
                }
            ]
        })

        if self.task:
            await self.task.queue_frame(LLMRunFrame())
        else:
            logger.error("Task no disponible para procesar imagen")
