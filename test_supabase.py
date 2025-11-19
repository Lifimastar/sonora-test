"""
Script de diagnóstico para verificar la base de datos.
"""
import json
import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

print("🔍 Verificando base de datos...\n")

# 1. Contar registros
result = supabase.table("knowledge_base").select("*", count="exact").execute()
print(f"📊 Total de registros: {result.count}")

# 2. Mostrar algunos registros
if result.data:
    print(f"\n📄 Primeros registros:")
    for idx, record in enumerate(result.data[:3], 1):
        print(f"\n{idx}. {record['document_name']}")
        print(f"   Tipo: {record['document_type']}")
        print(f"   Chunk {record['chunk_index']}: {record['chunk_text'][:100]}...")
        
        emb = record['embedding']
        if emb:
            # Si es string, lo convertimos a lista
            if isinstance(emb, str):
                emb = json.loads(emb)
            print(f"   Dimensiones del embedding: {len(emb)} ✅")
            print(f"   Primeros valores: {emb[:3]}")
        else:
            print("   ❌ No tiene embedding")

# 3. Verificar la función RPC
print("\n\n🔧 Verificando función match_documents...")
try:
    # Crear un embedding de prueba (vector de 1536 dimensiones con valores aleatorios)
    test_embedding = [0.1] * 1536
    
    response = supabase.rpc(
        'match_documents',
        {
            'query_embedding': test_embedding,
            'match_threshold': 0.0,  # Umbral muy bajo para ver si devuelve algo
            'match_count': 3
        }
    ).execute()
    
    print(f"✅ Función RPC funciona")
    print(f"   Resultados encontrados: {len(response.data)}")
    
    if response.data:
        print(f"\n   Primer resultado:")
        print(f"   - Documento: {response.data[0].get('document_name')}")
        print(f"   - Similitud: {response.data[0].get('similarity', 0):.2%}")
    
except Exception as e:
    print(f"❌ Error al llamar a la función RPC: {e}")