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
        self.retriever = self.vector_store.as_retriever(
            search_type="mmr",
            search_kwargs={"k": 4, "fetch_k": 8}
        )
        self.llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)

    def responder_pregunta(self, pregunta: str):
        fragmentos = self.retriever.invoke(pregunta)
        
        if not fragmentos:
            return "No encontré información relevante en tus documentos para responder eso."

        archivos_detectados = set()
        for doc in fragmentos:
            ruta_completa = doc.metadata.get("source", "Archivo desconocido")
            archivos_detectados.add(os.path.basename(ruta_completa))

        lista_archivos = ", ".join(archivos_detectados)
        total_archivos = len(archivos_detectados)
        contexto_documentos = "\n\n".join([doc.page_content for doc in fragmentos])

        prompt_sistema = f"""
        Eres un asistente de inteligencia artificial experto en análisis de datos y documentos.
        
        CONTEXTO DEL SISTEMA:
        - Actualmente tienes acceso a {total_archivos} archivo(s) en la base de datos.
        - Los nombres de los archivos cargados son: [{lista_archivos}].
        
        Tu misión es responder a la pregunta del usuario utilizando ÚNICAMENTE la información proveída en el "Contexto de los documentos" de abajo.
        
        Si la respuesta no se puede deducir del contexto, di amablemente que no cuentas con esa información. No inventes datos.
        
        ---
        CONTEXTO DE LOS DOCUMENTOS:
        {contexto_documentos}
        ---
        
        PREGUNTA DEL USUARIO:
        {pregunta}
        
        RESPUESTA:
        """

        try:
            respuesta_ia = self.llm.invoke(prompt_sistema)
            return respuesta_ia.content
        except Exception as e:
            print(f"⚠️ Error detectado en la API de Google: {e}")
            return "⚠️ El servicio está temporalmente saturado. Por favor, reintenta en unos segundos."