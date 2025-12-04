"""
Servicio para interactuar con Supabase y guardar el historial de chat.
"""
import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

class DatabaseService:
    def __init__(self):
        self.client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.conversation_id = None
        self.user_id = None
    
    def create_conversation(self, title: str = "Nueva conversacion", user_id: str = None):
        """Crea una nueva sesion de conversacion"""
        data = {
            "title": title,
            "metadata": {"source": "pipecat_bot"}
        }

        if user_id:
            data["user_id"] = user_id

        response = self.client.table("conversations").insert(data).execute()

        if response.data:
            self.conversation_id = response.data[0]['id']
            print(f"📝 Conversacion iniciada: {self.conversation_id} (Usuario: {user_id})")
            return self.conversation_id
        return None
    
    def add_message(self, role: str, content: str):
        """Guarda un mensaje en la conversacion actual"""
        if not self.conversation_id:
            print("⚠️ No hay conversacion activa. Creando una nueva automaticamente...")
            self.create_conversation(title="Conversacion Automatica", user_id=self.user_id)
            return
        
        data = {
            "conversation_id": self.conversation_id,
            "role": role,
            "content": content
        }
        try:
            self.client.table("messages").insert(data).execute()
            print(f"💾 mensaje guardado ({role})")
        except Exception as e:
            print(f"❌ error guardando mensaje: {e}")
    
    def get_history(self, limit: int = 50):
        """Recupera el historial (para futuras implementaciones de 'continuar')"""
        if not self.conversation_id:
            return []
        
        response = self.client.table("messages").select("*").eq("conversation_id", self.conversation_id).order("created_at", desc=False).limit(limit).execute()

        return response.data
    
    def get_conversation_history(self, conversation_id: str):
        """Recupera el historial formateado para el LLM"""
        try:
            response = self.client.table("messages").select("role, content").eq("conversation_id", conversation_id).is_("deleted_at", "null").order("created_at").execute()

            return response.data if response.data else []
        except Exception as e:
            print(f"❌ Error recuperando historial: {e}")
            return []

    def save_memory(self, key: str, value: str):
        """Guarda un dato persistente para el usuario actual"""
        if not self.user_id:
            print("No se puede guardar memoria: user_id no definido")
            return False
        
        data = {
            "user_id": self.user_id,
            "key": key,
            "value": value
        }

        try:
            self.client.table("user_memory").upsert(data, on_conflict="user_id, key").execute()
            print(f"Memoria guardada: {key} = {value}")
            return True
        except Exception as e:
            print(f"Error guardando memoria: {e}")
            return False
    
    def get_all_memories(self):
        """Recupera todas las memorias del usuario"""
        if not self.user_id:
            return {}
        
        try:
            response = self.client.table("user_memory").select("key, value").eq("user_id", self.user_id).execute()
            return {item['key']: item['value'] for item in response.data}
        except Exception as e:
            print(f"Error recuperando memorias: {e}")
            return {}
        
    def delete_memory(self, key: str):
        """Borra un dato persistente del usuario actual"""
        if not self.user_id:
            print("⚠️ No se puede borrar memoria: user_id no definido")
            return False
            
        try:
            self.client.table("user_memory").delete().eq("user_id", self.user_id).eq("key", key).execute()
            print(f"🗑️ Memoria borrada: {key}")
            return True
        except Exception as e:
            print(f"❌ Error borrando memoria: {e}")
            return False
    
    def ensure_user_exists(self, user_id: str):
        """Asegura que el usuario exista en la tabla users para evitar errores de FK"""
        try:
            # Solo insertamos el ID. Si ya existe, no hacemos nada (on_conflict='id').
            # En Supabase-py, upsert maneja esto.
            data = {"id": user_id} 
            self.client.table("users").upsert(data).execute()
        except Exception as e:
            # Si falla, logueamos pero NO detenemos el bot, para ver si la conversación pasa igual
            # (aunque si la FK es estricta, fallará luego en create_conversation)
            print(f"⚠️ Warning: No se pudo sincronizar usuario {user_id}: {e}")