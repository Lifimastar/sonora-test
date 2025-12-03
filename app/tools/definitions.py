from app.services.database import SUPABASE_URL, SUPABASE_KEY, DatabaseService
from app.services.tuguia_database import TuGuiaDatabase
from supabase import create_client, Client
from pipecat.services.llm_service import FunctionCallParams
from loguru import logger
import secrets
import string
from app.utils.security import generar_password_segura
from app.services.rag import get_relevant_context

# Cliente Supabase para operaciones administrativas (crear usuarios, contar)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

async def buscar_informacion(params: FunctionCallParams):
    """
    Busca información relevante en la base de conocimiento.
    
    IMPORTANTE: Debes proporcionar el argumento 'query' con la pregunta específica.
    Ejemplo: buscar_informacion(query="¿Cuáles son las obligaciones del adherido?")
    
    Usa esta función SIEMPRE que el usuario pregunte sobre:
    - Contratos (adheridos o asesores)
    - Términos y condiciones
    - Servicios, obligaciones, derechos o prohibiciones
    - Información de contacto o legal
    
    :param params: Parámetros de la llamada. DEBE incluir 'query'.
    """
    try:
        # Extraer la pregunta o tema de búsqueda
        query = params.arguments.get("query") or params.arguments.get("pregunta")
        
        if not query:
            # Si no hay query, intentar usar el último mensaje del usuario o pedir aclaración
            resultado = {
                "success": False,
                "mensaje": "Error: No se especificó qué buscar. Por favor llama a la función con el argumento 'query'."
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

async def contar_usuarios_tuguia(params: FunctionCallParams):
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
                "error": "No se pudo obtener el conteo de usuarios"
            }
        
        await params.result_callback(respuesta)
    
    except Exception as e:
        logger.error(f" Error: {e}")
        await params.result_callback({
            "success": False,
            "error": str(e)
        })

async def crear_usuario_tuguia(params: FunctionCallParams):
    """
    Crea un nuevo usuario en la base de datos de Tu Guía AR.
    
    Requiere: email, password, first_name, last_name, phone, account_type
    """
    try:
        logger.info("Creando usuario en Tu Guia...")

        # obtener argumentos
        args = params.arguments
        email = args.get("email")
        password = args.get("password")
        first_name = args.get("first_name")
        last_name = args.get("last_name")
        phone = args.get("phone")
        account_type = args.get("account_type", "personal")

        # validar campos obligatorios
        if not all([email, password, first_name, last_name, phone]):
            await params.result_callback({
                "success": False,
                "error": "Faltan datos obligatorios: email, password, nombre, apellido y telefono"
            })
            return
        
        # crear usuario
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

async def contar_usuarios_por_subcategoria(params: FunctionCallParams):
    """
    Cuenta usuarios por subcategoria especifica en Tu Guia AR.

    Args:
        subcategory_names: Esta funcion REQUIERE que se especifiquen subcategorias.
    """
    try:
        logger.info("Contando usuarios por subcategoria...")

        args = params.arguments
        subcategory_names = args.get("subcategory_names", None)

        # Validar que se proporcionaron subcategorias
        if not subcategory_names:
            await params.result_callback({
                "success": False,
                "error": "Debes especificar al menos una subcategoria. Pregunta al usuario que subcategoria le interesa."
            })
            return

        tuguia_db = TuGuiaDatabase()
        result = tuguia_db.count_users_by_subcategory(subcategory_names)

        if result["success"]:
            # formatear mensaje
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

async def guardar_dato(params: FunctionCallParams):
    """
    Guarda un dato en la memoria a largo plazo.
    
    IMPORTANTE: Esta función requiere DOS argumentos obligatorios: 'key' y 'value'.
    
    Args:
        key (str): El nombre o etiqueta del dato. Ejemplos: "precio_dolar", "nombre_usuario", "fecha_cita".
        value (str): El valor o contenido del dato. Ejemplos: "1200 pesos", "Juan Perez", "2023-10-27".
    """
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
        
        db = DatabaseService()
        import os
        db.user_id = os.getenv("TEST_USER_ID")

        success = db.save_memory(key, value)

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
        
