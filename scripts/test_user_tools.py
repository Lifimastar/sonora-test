import asyncio
import os
import sys
import secrets
import string

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from supabase import create_client, Client
from app.services.database import SUPABASE_URL, SUPABASE_KEY

load_dotenv()

# Cliente Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

async def test_tools():
    print("🧪 Probando herramientas de usuario...")

    # 1. Probar contar usuarios
    print("\n1. Probando contar usuarios...")
    try:
        users_response = supabase.auth.admin.list_users()
        count = 0
        if isinstance(users_response, list):
            count = len(users_response)
        elif hasattr(users_response, 'users'):
            count = len(users_response.users)
        print(f"✅ Total de usuarios: {count}")
    except Exception as e:
        print(f"❌ Error contando usuarios: {e}")

    # 2. Probar crear usuario con rubro
    print("\n2. Probando crear usuario con rubro...")
    try:
        random_id = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(6))
        test_email = f"test_tool_{random_id}@example.com"
        test_password = "Password123!"
        test_rubro = "Gastronomía"

        user = supabase.auth.admin.create_user({
            "email": test_email,
            "password": test_password,
            "email_confirm": True,
            "user_metadata": {"rubro": test_rubro}
        })
        
        print(f"✅ Usuario creado: {user.user.email}")
        print(f"   ID: {user.user.id}")
        print(f"   Rubro: {user.user.user_metadata.get('rubro')}")
        
        # Limpiar: borrar usuario de prueba
        print("\n3. Limpiando usuario de prueba...")
        supabase.auth.admin.delete_user(user.user.id)
        print("✅ Usuario borrado.")
        
    except Exception as e:
        print(f"❌ Error creando usuario: {e}")

    print("\n🎉 Pruebas completadas!")

if __name__ == "__main__":
    asyncio.run(test_tools())
