import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.tuguia_database import TuGuiaDatabase

def test_connection():
    print("Probando conexion a Tu Guia DB...")

    db = TuGuiaDatabase()
    count = db.count_users()

    if count is not None:
        print(f"Conexion exitosa!")
        print(f"Total de usuarios en Tu Guia: {count}")
    else:
        print("Error en la conexion")

if __name__ == "__main__":
    test_connection()