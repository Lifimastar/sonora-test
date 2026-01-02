"""
Script para iniciar AMBOS servidores con un solo comando.
- Servidor de voz (Pipecat WebRTC) en puerto 7860
- Servidor de chat texto (FastAPI) en puerto 7861
"""
import subprocess
import sys
import os
import signal

def main():
    # Directorio actual
    cwd = os.path.dirname(os.path.abspath(__file__))

    print("🚀 Iniciando servidores de Bot Sonora...")
    print("   - Voz (Pipecat): http://localhost:7860")
    print("   - Chat texto: http://localhost:7861")
    print("   Presiona Ctrl+C para detener ambos.\n")

    # Iniciar ambos procesos
    processes = []
    
    try:
        # Servidor de voz (Pipecat)
        p1 = subprocess.Popen(
            [sys.executable, "bot.py"],
            cwd=cwd,
        )
        processes.append(p1)
        
        # Servidor de chat texto
        p2 = subprocess.Popen(
            [sys.executable, "-m", "app.api.server"],
            cwd=cwd,
        )
        processes.append(p2)
        
        # Esperar a que terminen
        for p in processes:
            p.wait()
            
    except KeyboardInterrupt:
        print("\n⏹️ Deteniendo servidores...")
        for p in processes:
            p.terminate()
        print("✅ Servidores detenidos.")
if __name__ == "__main__":
    main()