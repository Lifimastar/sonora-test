import asyncio
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from supabase import create_client, Client
from app.services.database import SUPABASE_URL, SUPABASE_KEY

load_dotenv()

# Cliente Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

async def test_count_by_rubro():
    print("🧪 Probando contar usuarios por rubro...")

    try:
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
        
        # Mostrar resultados
        print(f"\n✅ Total de usuarios: {len(user_list)}")
        print("\n📊 Desglose por rubro:")
        for rubro, count in sorted(rubro_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"   - {rubro}: {count}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_count_by_rubro())
