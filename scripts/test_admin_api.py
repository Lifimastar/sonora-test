import os
import secrets
import string
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

print("🔍 Probando Supabase Admin API...")

try:
    # 1. Listar usuarios (para probar acceso de lectura admin)
    print("\n1. Listando usuarios...")
    # Nota: list_users devuelve un objeto UserResponse, no una lista directa
    users_response = supabase.auth.admin.list_users()
    users = users_response  # En versiones recientes de supabase-py, esto puede ser una lista o un objeto
    
    # Manejar diferentes versiones de la librería
    user_list = []
    if isinstance(users, list):
        user_list = users
    elif hasattr(users, 'users'):
        user_list = users.users
    else:
        print(f"⚠️ Formato de respuesta desconocido: {type(users)}")

    print(f"✅ Éxito. Usuarios encontrados: {len(user_list)}")
    if user_list:
        print(f"   Ejemplo: {user_list[0].email} (Metadata: {user_list[0].user_metadata})")

    # 2. Crear usuario de prueba (para probar acceso de escritura admin)
    print("\n2. Creando usuario de prueba...")
    random_id = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(6))
    test_email = f"test_admin_{random_id}@example.com"
    test_password = "Password123!"
    test_rubro = "Turismo Test"

    user = supabase.auth.admin.create_user({
        "email": test_email,
        "password": test_password,
        "email_confirm": True,
        "user_metadata": {"rubro": test_rubro}
    })
    
    print(f"✅ Usuario creado: {user.user.email}")
    print(f"   ID: {user.user.id}")
    print(f"   Metadata: {user.user.user_metadata}")

    # 3. Borrar usuario de prueba
    print("\n3. Borrando usuario de prueba...")
    supabase.auth.admin.delete_user(user.user.id)
    print("✅ Usuario borrado.")

    print("\n🎉 Prueba completa: La Service Key tiene permisos de Admin Auth.")

except Exception as e:
    print(f"\n❌ Error: {e}")
    print("   Es posible que la Service Key no tenga permisos de Admin o la librería sea diferente.")
