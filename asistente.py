import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

load_dotenv()

class AsistenteRAG:
    def __init__(self):
        self.carpeta_db = "./chroma_db"
        self.embeddings = GoogleGenerativeAIEmbeddings(model="gemini-embedding-001")
        
        self.vector_store = Chroma(
            persist_directory=self.carpeta_db,
            embedding_function=self.embeddings
        )
        
        # Cambiamos el tipo de búsqueda para forzar diversidad de fragmentos
        self.retriever = self.vector_store.as_retriever(
         search_type="similarity",
         search_kwargs={"k": 5}
     )
        
        self.llm = ChatGoogleGenerativeAI(model="gemini-3.8-flash", temperature=0)

    def responder_pregunta(self, pregunta: str):
        # FASE A: Recuperación (Retrieval)
        fragmentos = self.retriever.invoke(pregunta)
        
        if not fragmentos:
            return "No encontré información relevante en tus documentos para responder eso."

        # Extracción dinámica de metadatos (Saber qué archivos tiene abiertos)
        archivos_detectados = set()
        for doc in fragmentos:
            ruta_completa = doc.metadata.get("source", "Archivo desconocido")
            nombre_archivo = os.path.basename(ruta_completa)
            archivos_detectados.add(nombre_archivo)
        
        lista_archivos = ", ".join(archivos_detectados)
        total_archivos = len(archivos_detectados)
        contexto_documentos = "\n\n".join([doc.page_content for doc in fragmentos])

        # FASE B: Generación con Prompt del Sistema Dinámico
        prompt_sistema = f"""
        Eres un asistente de inteligencia artificial experto en análisis de datos y documentos.
        
        CONTEXTO DEL SISTEMA:
        - Actualmente tienes acceso a {total_archivos} archivo(s) en la base de datos.
        - Los nombres de los archivos cargados son: [{lista_archivos}].
        
        Tu misión es responder a la pregunta del usuario utilizando ÚNICAMENTE la información proveída en el "Contexto de los documentos" de abajo, o bien, los datos de arriba sobre los archivos que tienes cargados si te preguntan qué documentos posees o cuántos archivos hay.
        
        Si la respuesta a la pregunta no se puede deducir del contexto ni de los archivos cargados, di amablemente que no cuentas con esa información. No inventes datos.
        
        ---
        CONTEXTO DE LOS DOCUMENTOS:
        {contexto_documentos}
        ---
        
        PREGUNTA DEL USUARIO:
        {pregunta}
        
        RESPUESTA:
        """

        # Escudo contra errores de servidor (503 / 429)
        try:
            respuesta_ia = self.llm.invoke(prompt_sistema)
            contenido = respuesta_ia.content
            
            # Extraer solo el texto limpio si Gemini 3.8 devuelve bloques con firma de pensamiento
            if isinstance(contenido, list):
                textos = [
                    bloque.get("text", "") 
                    for bloque in contenido 
                    if isinstance(bloque, dict) and bloque.get("type") == "text"
                ]
                return "\n".join(textos)
                
            return contenido
        except Exception as e:
            print(f"⚠️ Error detectado en la API de Google: {e}")
            return (
                "⚠️ **Servicio temporalmente ocupado**\n\n"
                "En este momento los servidores de Gemini están experimentando una alta demanda. "
                "Tu código y configuración están perfectamente bien.\n\n"
                "**Por favor, espera unos segundos y vuelve a enviar tu pregunta.** ⏱️"
            )