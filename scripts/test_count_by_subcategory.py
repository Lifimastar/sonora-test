import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.tuguia_database import TuGuiaDatabase

def test_count():
    print("🧪 Probando conteo por subcategoría...")
    
    db = TuGuiaDatabase()
    
    # Probar una subcategoría
    print("\n🔍 Una subcategoría:")
    result = db.count_users_by_subcategory("Fotógrafos")
    print(result)
    
    # Probar varias subcategorías
    print("\n🔍 Varias subcategorías:")
    result = db.count_users_by_subcategory(["Fotógrafos", "Arquitectos", "Médicos"])
    print(result)

if __name__ == "__main__":
    test_count()