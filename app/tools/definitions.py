from app.services.database import SUPABASE_URL, SUPABASE_KEY, DatabaseService
from app.services.tuguia_database import TuGuiaDatabase
from app.pipeline.vision_processor import VisionCaptureProcessor
from supabase import create_client, Client
from pipecat.services.llm_service import FunctionCallParams
from loguru import logger
import secrets
import string
from app.utils.security import generar_password_segura
from app.services.rag import get_relevant_context
from app.context import current_user_id
from pipecat.processors.aggregators.llm_context import LLMContext

# Cliente Supabase para operaciones administrativas (crear usuarios, contar)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class BotTools:
    def __init__(self, db_service: DatabaseService, vision_processor: VisionCaptureProcessor = None):
        """
        Inicializa las herramientas con el servicio de base de datos de la sesión actual.
        """
        self.db_service = db_service
        self.vision_processor = vision_processor
        self.context: LLMContext | None = None
    
    def set_context(self, context: LLMContext):
        """Permite inyectar el contexto del LLM post-inicializacion."""
        self.context = context

    async def buscar_informacion(self, params: FunctionCallParams):
        """
        Busca información relevante en la base de conocimiento.
        """
        try:
            query = params.arguments.get("query") or params.arguments.get("pregunta")
        
            if not query:
                resultado = {
                    "success": False,
                    "mensaje": "Error: No se especificó qué buscar."
                }
            else:
                logger.info(f"🔍 Buscando en RAG: {query}")
                context = get_relevant_context(query)
                
                resultado = {
                    "success": True,
                    "informacion": context,
                    "mensaje": "Información encontrada."
            }
        
            await params.result_callback(resultado)
        
        except Exception as e:
            logger.error(f"❌ Error en búsqueda RAG: {e}")
            await params.result_callback({
                "success": False,
                "error": str(e)
            })

    async def contar_usuarios_tuguia(self, params: FunctionCallParams):
        """Cuenta usuarios registrados en la base de datos de Tu Guia AR."""
        try:
            logger.info("📊 Contando usuarios de Tu Guia...")
            tuguia_db = TuGuiaDatabase()
            count = tuguia_db.count_users()

            if count is not None:
                respuesta = {
                    "success": True,
                    "total_usuarios": count,
                    "mensaje": f"Hay {count} usuarios registrados en Tu Guia AR."
                }
            else:
                respuesta = {
                    "success": False,
                    "error": "No se pudo obtener el conteo"
                }
            
            await params.result_callback(respuesta)
        except Exception as e:
            logger.error(f" Error: {e}")
            await params.result_callback({
                "success": False,
                "error": str(e)
            })

    async def crear_usuario_tuguia(self, params: FunctionCallParams):
        """Crea un nuevo usuario en la base de datos de Tu Guía AR."""
        try:
            logger.info("Creando usuario en Tu Guia...")
            args = params.arguments
            email = args.get("email")
            password = args.get("password")
            first_name = args.get("first_name")
            last_name = args.get("last_name")
            phone = args.get("phone")
            account_type = args.get("account_type", "personal")

            if not all([email, password, first_name, last_name, phone]):
                await params.result_callback({
                    "success": False,
                    "error": "Faltan datos obligatorios: email, password, nombre, apellido y telefono"
                })
                return
            
            tuguia_db = TuGuiaDatabase()
            result = tuguia_db.create_user(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                account_type=account_type
            )

            if result["success"]:
                mensaje = f"Usuario creado exitosamente en Tu Guia. Email: {email}, Nombre: {result['full_name']}"
            else:
                mensaje = f"Error al crear usuario: {result['error']}"
                logger.error(f"{mensaje}")
            
            result["mensaje"] = mensaje
            await params.result_callback(result)

        except Exception as e:
            logger.error(f"Error: {e}")
            await params.result_callback({
                "success": False,
                "error": str(e)
            })

    async def contar_usuarios_por_subcategoria(self, params: FunctionCallParams):
        """Cuenta usuarios por subcategoria."""
        try:
            logger.info("Contando usuarios por subcategoria...")
            args = params.arguments
            subcategory_names = args.get("subcategory_names")

            if not subcategory_names:
                await params.result_callback({
                    "success": False,
                    "error": "Faltan subcategorias"
                })
                return

            tuguia_db = TuGuiaDatabase()
            result = tuguia_db.count_users_by_subcategory(subcategory_names)

            if result["success"]:
                mensajes = []
                for nombre, info in result['results'].items():
                    if info['found']:
                        mensajes.append(f"{nombre}: {info['count']} usuarios")
                    else:
                        mensajes.append(f"{nombre}: no encontrada")
                mensaje = ". ".join(mensajes)
            else:
                mensaje = f"Error: {result['error']}"
            
            result["mensaje"] = mensaje
            await params.result_callback(result)
    
        except Exception as e:
            logger.error(f"Error: {e}")
            await params.result_callback({
                "success": False,
                "error": str(e)
            })

    async def guardar_dato(self, params: FunctionCallParams):
        """Guarda un dato en la memoria a largo plazo del usuario actual."""
        try:
            logger.info("Guardando dato en memoria...")
            args = params.arguments
            key = args.get("key")
            value = args.get("value")

            if not key or not value:
                await params.result_callback({
                    "success": False,
                    "error": "Se requiere clave y valor"
                })
                return
            
            success = self.db_service.save_memory(key, value)

            if success:
                await params.result_callback({
                    "success": True,
                    "mensaje": f"Entendido. He guardado que '{key}' es '{value}'."
                })
            else:
                await params.result_callback({
                    "success": False,
                    "error": "Error de base de datos"
                })

        except Exception as e:
            logger.error(f"Error: {e}")
            await params.result_callback({"success": False, "error": str(e)})
            
    async def borrar_dato(self, params: FunctionCallParams):
        """Borra un dato específico de la memoria."""
        try:
            logger.info("🗑️ Borrando dato de memoria...")
            args = params.arguments
            key = args.get("key")
            
            if not key:
                await params.result_callback({
                    "success": False,
                    "error": "Falta key."
                })
                return
            
            success = self.db_service.delete_memory(key)
            
            if success:
                await params.result_callback({
                    "success": True,
                    "mensaje": f"Dato '{key}' borrado."
                })
            else:
                await params.result_callback({
                    "success": False,
                    "error": "Error al borrar"
                })

        except Exception as e:
            logger.error(f"Error: {e}")
            await params.result_callback({"success": False, "error": str(e)})

    async def ver_camara(self, params: FunctionCallParams):
        """
        Toma una foto y la agrega al contexto visual del LLM.
        """
        try:
            if not self.vision_processor:
                await params.result_callback({
                    "success": False,
                    "error": "Procesador de vision no disponible"
                })
                return
            
            if not self.vision_processor.has_image():
                await params.result_callback({
                    "success": False,
                    "mensaje": "No hay imagen disponible. Asegurate de que tu camara este encendida."
                })
                return
            
            image_base64 = self.vision_processor.get_last_image_base64()

            if self.context:
                logger.info("Inyectando imagen al contexto del LLM")

                self.context.add_message({
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Esta es una captura de lo que ve mi camara ahora mismo. Usala para responder."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                })

                await params.result_callback({
                    "success": True,
                    "description": "Imagen capturada y enviada a tu contexto visual.",
                    "mensaje": "Ya tengo la imagen. La estoy analizando."
                })

            else:
                await params.result_callback({
                    "success": False,
                    "error": "Error: Contexto del LLM no vinculado a las herramientas."
                })

        except Exception as e:
            logger.error(f"Error obteniendo imagen de camara: {e}")
            await params.result_callback({
                "success": False,
                "error": str(e)
            })