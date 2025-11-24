"""
Script para indexar documentos en Supabase con embeddings de OpenAI.
Se ejecuta una sola vez o cuando se actualizan los documentos.
"""

import sys
import os
import tiktoken
from dotenv import load_dotenv
from openai import OpenAI

# Add the parent directory to sys.path to allow imports from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.knowledge_base import (
    CONTRATO_TU_GUIA_AR,
    CONTRATO_ASESORES_TU_GUIA_AR,
    TERMINOS_Y_CONDICIONES_ECOSISTEMA,
    POLITICA_PRIVACIDAD,
    POLITICA_COOKIES,
    SOBRE_NOSOTROS
)
from app.services.rag import supabase

load_dotenv()

OPENAI_CLIENT = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Configuración de chunking
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

def count_tokens(text: str) -> int:
    encoding = tiktoken.encoding_for_model("text-embedding-3-small")
    return len(encoding.encode(text))

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP):
    encoding = tiktoken.encoding_for_model("text-embedding-3-small")
    tokens = encoding.encode(text)
    chunks = []
    start = 0
    while start < len(tokens):
        end = start + chunk_size
        chunk_tokens = tokens[start:end]
        chunk_text = encoding.decode(chunk_tokens)
        chunks.append(chunk_text)
        start = end - overlap
    return chunks

def generate_embedding(text: str):
    response = OPENAI_CLIENT.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding

def index_document(document_name: str, document_type: str, content: str):
    print(f"\n📄 Indexando: {document_name}")
    chunks = chunk_text(content)
    print(f"   Dividido en {len(chunks)} chunks")
    
    for idx, chunk in enumerate(chunks):
        print(f"   Procesando chunk {idx + 1}/{len(chunks)}...", end=" ")
        embedding = generate_embedding(chunk)
        embedding_list = [float(x) for x in embedding]
        
        if len(embedding_list) != 1536:
            print(f"❌ ERROR: Embedding tiene {len(embedding_list)} dimensiones")
            continue
        
        metadata = {
            "total_chunks": len(chunks),
            "tokens": count_tokens(chunk)
        }
        
        try:
            result = supabase.rpc(
                'insert_knowledge_chunk',
                {
                    'p_document_name': document_name,
                    'p_document_type': document_type,
                    'p_chunk_text': chunk,
                    'p_chunk_index': idx,
                    'p_embedding': embedding_list,
                    'p_metadata': metadata
                }
            ).execute()
            print("✅")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print(f"✅ {document_name} indexado correctamente")

def clear_knowledge_base():
    print("🗑️  Limpiando base de conocimiento...")
    supabase.table("knowledge_base").delete().neq("id", 0).execute()
    print("✅ Base de conocimiento limpiada")

def main():
    print("🚀 Iniciando indexación de documentos...")
    clear_knowledge_base()
    
    documents = [
        ("Contrato de Adhesión - Tu Guía AR", "contrato_adheridos", CONTRATO_TU_GUIA_AR),
        ("Contrato de Asesores Comerciales", "contrato_asesores", CONTRATO_ASESORES_TU_GUIA_AR),
        ("Términos y Condiciones del Ecosistema", "terminos_condiciones", TERMINOS_Y_CONDICIONES_ECOSISTEMA),
        ("Política de Privacidad", "politica_privacidad", POLITICA_PRIVACIDAD),
        ("Política de Cookies", "politica_cookies", POLITICA_COOKIES),
        ("Sobre Nosotros", "sobre_nosotros", SOBRE_NOSOTROS),
    ]
    
    for doc_name, doc_type, content in documents:
        index_document(doc_name, doc_type, content)
    
    print("\n🎉 ¡Indexación completada!")
    result = supabase.table("knowledge_base").select("id", count="exact").execute()
    print(f"   Total de chunks indexados: {result.count}")

if __name__ == "__main__":
    main()