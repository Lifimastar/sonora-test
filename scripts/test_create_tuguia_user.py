import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.tuguia_database import TuGuiaDatabase

def test_create_user():
    print("🧪 Probando creación de usuario en Tu Guía...")
    
    db = TuGuiaDatabase()
    result = db.create_user(
        email="test@tuguia.com",
        password=os.environ.get("GENERIC_PASSWORD"),
        first_name="Juan",
        last_name="Pérez",
        phone="+54 11 1234 5678",
        account_type="personal"
    )
    
    if result["success"]:
        print(f"✅ Usuario creado: {result['full_name']}")
        print(f"📧 Email: {result['email']}")
        print(f"🆔 ID: {result['user_id']}")
    else:
        print(f"❌ Error: {result['error']}")

if __name__ == "__main__":
    test_create_user()