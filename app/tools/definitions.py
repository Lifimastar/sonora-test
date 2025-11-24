import os
import secrets
import string
import aiohttp
from loguru import logger
from pipecat.services.llm_service import FunctionCallParams
from app.services.rag import get_relevant_context
from app.utils.security import generar_password_segura

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
