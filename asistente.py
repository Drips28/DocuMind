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

    def _obtener_inventario_real(self) -> list[str]:
        """Consulta los metadatos completos de ChromaDB para listar todos los archivos indexados."""
        try:
            datos_db = self.vector_store.get(include=["metadatas"])
            metadatas = datos_db.get("metadatas") or []
            archivos = {
                os.path.basename(meta["source"])
                for meta in metadatas
                if isinstance(meta, dict) and meta.get("source")
            }
            return sorted(archivos)
        except Exception:
            return []

    def responder_pregunta(self, pregunta: str):
        # FASE A: Recuperación (Retrieval)
        fragmentos = self.retriever.invoke(pregunta)
        inventario_real = self._obtener_inventario_real()
        
        if not fragmentos and not inventario_real:
            return "No encontré información relevante en tus documentos para responder eso."

        # Fuentes específicas recuperadas para esta consulta
        fuentes_consulta = sorted({
            os.path.basename(doc.metadata.get("source", "Archivo desconocido"))
            for doc in fragmentos
        })
        
        lista_inventario = ", ".join(inventario_real) if inventario_real else "Ninguno"
        total_archivos = len(inventario_real)
        lista_fuentes_consulta = ", ".join(fuentes_consulta) if fuentes_consulta else "Ninguna"
        
        contexto_documentos = "\n\n".join([
            f"[Fuente: {os.path.basename(doc.metadata.get('source', 'Archivo desconocido'))}]\n{doc.page_content}"
            for doc in fragmentos
        ])

        # FASE B: Generación con Prompt del Sistema Dinámico
        prompt_sistema = f"""
        Eres un asistente de inteligencia artificial experto en análisis de datos y documentos.
        
        INVENTARIO REAL DE LA BASE DE DATOS:
        - Total de archivos indexados actualmente: {total_archivos}
        - Lista completa de archivos disponibles: [{lista_inventario}]
        - Archivos consultados para esta respuesta: [{lista_fuentes_consulta}]
        
        Tu misión es responder a la pregunta del usuario utilizando ÚNICAMENTE la información proveída en el "Contexto de los documentos" de abajo, o bien, el "Inventario real de la base de datos" si te preguntan qué documentos posees o cuántos archivos hay.
        Siempre cita el nombre del archivo fuente cuando entregues datos extraídos de un documento.
        
        Si la respuesta a la pregunta no se puede deducir del contexto ni del inventario, di amablemente que no cuentas con esa información. No inventes datos.
        
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
