"""
Servicio RAG para búsqueda semántica en la base de conocimiento.
"""

import os
from typing import List, Dict
from dotenv import load_dotenv
from openai import OpenAI
from supabase import create_client, Client

load_dotenv()

# Configuración
OPENAI_CLIENT = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def generate_query_embedding(query: str) -> List[float]:
    """Genera embedding para la consulta del usuario"""
    response = OPENAI_CLIENT.embeddings.create(
        model="text-embedding-3-small",
        input=query
    )
    return response.data[0].embedding

def search_knowledge_base(
    query: str, 
    match_threshold: float = 0.78,
    match_count: int = 3
) -> List[Dict]:
    """
    Busca en la base de conocimiento usando similitud semántica.
    
    Args:
        query: Pregunta del usuario
        match_threshold: Umbral mínimo de similitud (0-1)
        match_count: Número máximo de resultados
    
    Returns:
        Lista de chunks relevantes con metadata
    """
    # Generar embedding de la consulta
    query_embedding = generate_query_embedding(query)
    
    # Buscar en Supabase usando la función match_documents
    response = supabase.rpc(
        'match_documents',
        {
            'query_embedding': query_embedding,
            'match_threshold': match_threshold,
            'match_count': match_count
        }
    ).execute()
    
    return response.data

def format_context_for_llm(search_results: List[Dict]) -> str:
    """
    Formatea los resultados de búsqueda para el LLM.
    
    Args:
        search_results: Resultados de la búsqueda
    
    Returns:
        Contexto formateado como string
    """
    if not search_results:
        return "No se encontró información relevante en la base de conocimiento."
    
    context_parts = []
    
    for idx, result in enumerate(search_results, 1):
        doc_name = result.get('document_name', 'Documento desconocido')
        chunk_text = result.get('chunk_text', '')
        similarity = result.get('similarity', 0)
        
        context_parts.append(
            f"[Fuente {idx}: {doc_name} (relevancia: {similarity:.2%})]\n{chunk_text}"
        )
    
    return "\n\n---\n\n".join(context_parts)

def get_relevant_context(query: str) -> str:
    """
    Función principal para obtener contexto relevante.
    """
    # Buscar documentos relevantes
    # BAJAMOS EL UMBRAL DE 0.75 A 0.5
    results = search_knowledge_base(query, match_threshold=0.5, match_count=5)
    
    # Formatear para el LLM
    context = format_context_for_llm(results)
    
    return context

# Función de prueba
if __name__ == "__main__":
    # Prueba el servicio RAG
    test_query = "¿Cuáles son las obligaciones de un adherido?"
    
    print(f"🔍 Buscando: {test_query}\n")
    context = get_relevant_context(test_query)
    print("📄 Contexto encontrado:")
    print(context)