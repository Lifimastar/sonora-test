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
    
    def create_conversation(self, title: str = "Nueva conversacion"):
        """Crea una nueva sesion de conversacion"""
        data = {
            "title": title,
            "metadata": {"source": "pipecat_bot"}
        }
        response = self.client.table("conversations").insert(data).execute()
        if response.data:
            self.conversation_id = response.data[0]['id']
            print(f"📝 Conversacion iniciada: {self.conversation_id}")
            return self.conversation_id
        return None
    
    def add_message(self, role: str, content: str):
        """Guarda un mensaje en la conversacion actual"""
        if not self.conversation_id:
            print("⚠️ No hay conversacion activa para guardar el mensaje")
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
