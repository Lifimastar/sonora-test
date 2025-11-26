from app.services.database import SUPABASE_URL, SUPABASE_KEY
from supabase import create_client, Client
from pipecat.services.llm_service import FunctionCallParams
from loguru import logger
import secrets
import string
from app.utils.security import generar_password_segura
from app.services.rag import get_relevant_context

# Cliente Supabase para operaciones administrativas (crear usuarios, contar)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

async def crear_usuario_supabase(params: FunctionCallParams):
    """Crea un usuario en Supabase Auth directamente.
    
    Args:
        params: Parámetros de la llamada a función que contiene:
            - email (opcional): Email del usuario.
            - password (opcional): Contraseña del usuario.
            - rubro (opcional): Rubro o actividad del usuario (ej: Turismo, Gastronomía).
    """
    try:
        # extraer argumentos del LLM
        email = params.arguments.get("email", None)
        password = params.arguments.get("password", None)
        rubro = params.arguments.get("rubro", "No especificado")

        # generar email aleatorio si no se proporciona
        if not email:
            random_id = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(8))
            email = f"usuario_{random_id}@sonora.com"
        
        # generar contrasena segura si no se proporciona
        if not password:
            password = generar_password_segura()
        
        logger.info(f"👤 Creando usuario: {email} | Rubro: {rubro}")

        # Crear usuario usando Admin API de Supabase
        user_attributes = {
            "email": email,
            "password": password,
            "email_confirm": True,
            "user_metadata": {"rubro": rubro}
        }
        
        user = supabase.auth.admin.create_user(user_attributes)
        
        # preparar respuesta exitosa
        respuesta = {
            "success": True,
            "email": email,
            "password": password,
            "rubro": rubro,
            "id": user.user.id,
            "mensaje": f"Usuario creado exitosamente. Email: {email}, Rubro: {rubro}"
        }
        
        # devuelve el resultado al LLM
        await params.result_callback(respuesta)

    except Exception as e:
        logger.error(f"❌ Error creando usuario: {e}")
        await params.result_callback({
            "success": False,
            "error": f"Error al crear usuario: {str(e)}"
        })

async def contar_usuarios(params: FunctionCallParams):
    """Cuenta el número total de usuarios registrados en el sistema.
    
    Usa esta función cuando pregunten "¿cuántos usuarios hay?" o estadísticas similares.
    """
    try:
        logger.info("📊 Contando usuarios...")
        
        # Listar usuarios (la paginación por defecto suele ser 50, para más precisión habría que paginar)
        # Para este caso simple, asumimos que list_users trae los suficientes o usamos el total si la API lo provee
        users_response = supabase.auth.admin.list_users()
        
        # Manejar respuesta según versión de librería
        count = 0
        if isinstance(users_response, list):
            count = len(users_response)
        elif hasattr(users_response, 'users'):
            count = len(users_response.users)
        
        respuesta = {
            "success": True,
            "total_usuarios": count,
            "mensaje": f"Hay un total de {count} usuarios registrados en la base de datos."
        }
        
        await params.result_callback(respuesta)
        
    except Exception as e:
        logger.error(f"❌ Error contando usuarios: {e}")
        await params.result_callback({
            "success": False,
            "error": f"Error al contar usuarios: {str(e)}"
        })

async def contar_usuarios_por_rubro(params: FunctionCallParams):
    """Cuenta usuarios agrupados por rubro (categoría de negocio).
    
    Usa esta función cuando pregunten:
    - "¿Cuántos usuarios hay por rubro?"
    - "¿Cuántos usuarios de turismo hay?"
    - "Dame estadísticas por categoría"
    - "¿Qué rubros tienen más usuarios?"
    """
    try:
        logger.info("📊 Contando usuarios por rubro...")
        
        # Listar todos los usuarios
        users_response = supabase.auth.admin.list_users()
        
        # Obtener lista de usuarios
        user_list = []
        if isinstance(users_response, list):
            user_list = users_response
        elif hasattr(users_response, 'users'):
            user_list = users_response.users
        
        # Contar por rubro
        rubro_counts = {}
        for user in user_list:
            rubro = user.user_metadata.get('rubro', 'No especificado')
            rubro_counts[rubro] = rubro_counts.get(rubro, 0) + 1
        
        # Formatear mensaje
        total = len(user_list)
        desglose = ", ".join([f"{rubro}: {count}" for rubro, count in sorted(rubro_counts.items(), key=lambda x: x[1], reverse=True)])
        
        respuesta = {
            "success": True,
            "total_usuarios": total,
            "usuarios_por_rubro": rubro_counts,
            "mensaje": f"Total de {total} usuarios. Desglose por rubro: {desglose}"
        }
        
        await params.result_callback(respuesta)
        
    except Exception as e:
        logger.error(f"❌ Error contando usuarios por rubro: {e}")
        await params.result_callback({
            "success": False,
            "error": f"Error al contar usuarios por rubro: {str(e)}"
        })


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
