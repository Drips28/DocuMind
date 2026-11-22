import os
import time
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from lector import LectorDocumentos

# Cargamos la API Key desde el archivo .env
load_dotenv()

class GestorVectorial:
    def __init__(self, carpeta_db: str = "./chroma_db"):
        self.carpeta_db = carpeta_db
        
        # ✅ REGRESAMOS AL QUE SÍ FUNCIONA SINFONÍA CON LANGCHAIN
        self.embeddings = GoogleGenerativeAIEmbeddings(model="gemini-embedding-001")
        self.vector_store = None

    def guardar_archivo_en_db(self, ruta_archivo: str):
        """Lee cualquier archivo, lo fragmenta y lo guarda en ChromaDB en bloques para evitar el Error 429."""
        # Instanciamos tu lector modular existente
        lector = LectorDocumentos(ruta_archivo)
        fragmentos = lector.procesar()
        
        if not fragmentos:
            print(f"⚠️ No se generaron fragmentos para el archivo: {ruta_archivo}")
            return
        
        print(f"🧠 Preparando la indexación de {len(fragmentos)} fragmentos...")
        
        # Inicializamos Chroma apuntando a tu carpeta local
        vector_store = Chroma(
            persist_directory=self.carpeta_db,
            embedding_function=self.embeddings
        )
        
        # CONTROL DE FLUJO: Subimos en bloques de 50 fragmentos
        tamano_bloque = 50
        
        for i in range(0, len(fragmentos), tamano_bloque):
            bloque = fragmentos[i : i + tamano_bloque]
            
            # ✅ CORREGIDO: Cambiamos el iterador interno a 'j' para evitar conflictos de índices
            tamanio_minilote = 5  # Enviamos de 5 en 5 fragmentos
            for j in range(0, len(bloque), tamanio_minilote):
                minilote = bloque[j : j + tamanio_minilote]
                
                # ✅ CORREGIDO: Cálculo matemático exacto para el rastreo en consola
                frag_inicio = i + j
                frag_fin = frag_inicio + len(minilote)
                
                print(
                    f"📥 Subiendo minilote {j // tamanio_minilote + 1} (Fragmentos {frag_inicio} al {frag_fin})..."
                )
                # Guardamos este minilote en Chroma
                vector_store.add_documents(documents=minilote)
                # ⏱️ Pausa de 4 segundos para que la API de Google "respire"
                if j + tamanio_minilote < len(bloque):
                    print("⏱️ Esperando 4 segundos para evitar el límite de la API...")
                    time.sleep(4)
                
        print("💾 ¡Base de datos unificada y guardada con éxito!")

    def buscar_similitud(self, pregunta: str, cantidad_resultados: int = 3):
        """Busca los fragmentos de texto más parecidos a la pregunta del usuario."""
        # Si no se ha cargado en esta sesión, conectamos con la carpeta existente
        if not self.vector_store:
            self.vector_store = Chroma(
                persist_directory=self.carpeta_db,
                embedding_function=self.embeddings
            )
        
        print(f"🔍 Buscando en la base de datos: '{pregunta}'")
        # Realiza la búsqueda matemática por significado (similitud semántica)
        resultados = self.vector_store.similarity_search(pregunta, k=cantidad_resultados)
        return resultados

# --- Zona de Pruebas ---
if __name__ == "__main__":
    gestor = GestorVectorial()
    
    # 1. PRUEBA DE GUARDADO
    archivo_a_procesar = "documentos/BBVA 03 26.pdf" 
    gestor.guardar_archivo_en_db(archivo_a_procesar)
    
    # 2. PRUEBA DE BÚSQUEDA al estilo Google
    pregunta_prueba = "Cual es el numero de cuenta o cliente" 
    
    print("\n--------------------------------------------------")
    fragmentos_encontrados = gestor.buscar_similitud(pregunta_prueba)
    
    print(f"\n🎯 Se encontraron {len(fragmentos_encontrados)} fragmentos relevantes:")
    for i, doc in enumerate(fragmentos_encontrados):
        print(f"\n[Resultado {i+1}] (Fuente: {doc.metadata.get('source')})")
        print(f"Contenido: {doc.page_content[:250]}...")