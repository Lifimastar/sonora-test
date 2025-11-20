"""
Script para verificar que las tablas necesarias existen en Supabase.
"""
import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

def check_setup():
    print("🕵️ Verificando configuración de base de datos...")
    
    try:
        client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # 1. Intentar insertar una conversación de prueba
        print("   Intentando crear conversación de prueba...", end=" ")
        data = {"title": "Test de verificación", "metadata": {"test": True}}
        response = client.table("conversations").insert(data).execute()
        
        if response.data:
            conv_id = response.data[0]['id']
            print("✅")
            
            # 2. Intentar insertar un mensaje de prueba
            print("   Intentando guardar mensaje de prueba...", end=" ")
            msg_data = {
                "conversation_id": conv_id,
                "role": "system",
                "content": "Verificación exitosa"
            }
            client.table("messages").insert(msg_data).execute()
            print("✅")
            
            # 3. Limpiar datos de prueba
            print("   Limpiando datos de prueba...", end=" ")
            client.table("conversations").delete().eq("id", conv_id).execute()
            print("✅")
            
            print("\n🎉 ¡Todo listo! Las tablas existen y tienen permisos de escritura.")
            return True
            
    except Exception as e:
        print("\n❌ ERROR: Algo falló.")
        print(f"Detalle: {e}")
        print("\nPosibles causas:")
        print("1. No ejecutaste el script SQL en Supabase.")
        print("2. Las credenciales en .env no son correctas.")
        print("3. Las tablas tienen nombres diferentes.")
        return False

if __name__ == "__main__":
    check_setup()