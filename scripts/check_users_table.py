import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

print("🔍 Verificando tabla 'users'...")

try:
    # Intentar seleccionar de la tabla users (o perfiles, o lo que sea que use n8n)
    # Si n8n crea usuarios, probablemente los meta en una tabla 'users' o similar.
    # Si no existe, fallará.
    response = supabase.table("users").select("*", count="exact").limit(1).execute()
    print("✅ Tabla 'users' existe.")
    print(f"   Registros: {response.count}")
    if response.data:
        print(f"   Ejemplo: {response.data[0]}")
except Exception as e:
    print(f"❌ Error accediendo a tabla 'users': {e}")
    print("   Es probable que la tabla no exista o tenga otro nombre.")
