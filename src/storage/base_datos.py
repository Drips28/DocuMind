import os
import time
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from src.ingestion.lector import LectorDocumentos

load_dotenv()

class GestorVectorial:
    def __init__(self, carpeta_db: str = "./chroma_db"):
        self.carpeta_db = carpeta_db
        self.embeddings = GoogleGenerativeAIEmbeddings(model="gemini-embedding-001")
        self.vector_store = None

    def guardar_archivo_en_db(self, ruta_archivo: str):
        """Lee cualquier archivo, lo fragmenta y lo guarda en ChromaDB en bloques para evitar el Error 429."""
        lector = LectorDocumentos(ruta_archivo)
        fragmentos = lector.procesar()
        
        if not fragmentos:
            print(f"⚠️ No se generaron fragmentos para el archivo: {ruta_archivo}")
            return
            
        print(f"🧠 Preparando la indexación de {len(fragmentos)} fragmentos...")
        
        vector_store = Chroma(
            persist_directory=self.carpeta_db,
            embedding_function=self.embeddings
        )
        
        tamano_bloque = 50
        for i in range(0, len(fragmentos), tamano_bloque):
            bloque = fragmentos[i : i + tamano_bloque]
            tamanio_minilote = 5
            for j in range(0, len(bloque), tamanio_minilote):
                minilote = bloque[j : j + tamanio_minilote]
                frag_inicio = i + j
                frag_fin = frag_inicio + len(minilote)
                
                print(f"📥 Subiendo minilote {j // tamanio_minilote + 1} (Fragmentos {frag_inicio} al {frag_fin})...")
                vector_store.add_documents(documents=minilote)
                
                if j + tamanio_minilote < len(bloque):
                    print("⏱️ Esperando 4 segundos para evitar el límite de la API...")
                    time.sleep(4)
                    
        print("💾 ¡Base de datos unificada y guardada con éxito!")

    def buscar_similitud(self, pregunta: str, cantidad_resultados: int = 3):
        """Busca los fragmentos de texto más parecidos a la pregunta del usuario."""
        if not self.vector_store:
            self.vector_store = Chroma(
                persist_directory=self.carpeta_db,
                embedding_function=self.embeddings
            )
            
        print(f"🔍 Buscando en la base de datos: '{pregunta}'")
        resultados = self.vector_store.similarity_search(pregunta, k=cantidad_resultados)
        return resultados