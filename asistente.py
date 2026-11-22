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
            search_type="similarity",
            search_kwargs={"k": 5}
        )
        
        # Límites explícitos para evitar bloqueos prolongados en la interfaz
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-3.8-flash",
            temperature=0,
            timeout=60,
            max_retries=1
        )

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

        # Manejo diferenciado de excepciones de la API
        try:
            respuesta_ia = self.llm.invoke(prompt_sistema)
            contenido = respuesta_ia.content
            
            # Extraer solo el texto limpio si Gemini devuelve bloques estructurados
            if isinstance(contenido, list):
                textos = [
                    bloque.get("text", "") 
                    for bloque in contenido 
                    if isinstance(bloque, dict) and bloque.get("type") == "text"
                ]
                return "\n".join(textos)
                
            return contenido
        except Exception as e:
            error_str = str(e)
            print(f"⚠️ Error detectado en la API de Google: {error_str}")
            
            if any(code in error_str for code in ("429", "503", "504", "RESOURCE_EXHAUSTED", "UNAVAILABLE", "DEADLINE_EXCEEDED")):
                return (
                    "⚠️ **Servicio temporalmente ocupado (429 / 503 / 504)**\n\n"
                    "Los servidores de Gemini están saturados o se alcanzó el límite de cuota gratuita. "
                    "Espera unos segundos y vuelve a intentar tu consulta."
                )
            if any(code in error_str for code in ("401", "403", "API_KEY", "PERMISSION_DENIED")):
                return (
                    "⚠️ **Error de autenticación con la API**\n\n"
                    "Verifica que `GOOGLE_API_KEY` en tu archivo `.env` sea válida y esté activa."
                )
            if "404" in error_str or "NOT_FOUND" in error_str:
                return (
                    "⚠️ **Modelo no
git checkout -b fix/timeout-y-manejo-errores

cat << 'EOF' > asistente.py
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
            search_type="similarity",
            search_kwargs={"k": 5}
        )
        
        # Límites explícitos para evitar bloqueos prolongados en la interfaz
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-3.8-flash",
            temperature=0,
            timeout=60,
            max_retries=1
        )

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

        # Manejo diferenciado de excepciones de la API
        try:
            respuesta_ia = self.llm.invoke(prompt_sistema)
            contenido = respuesta_ia.content
            
            # Extraer solo el texto limpio si Gemini devuelve bloques estructurados
            if isinstance(contenido, list):
                textos = [
                    bloque.get("text", "") 
                    for bloque in contenido 
                    if isinstance(bloque, dict) and bloque.get("type") == "text"
                ]
                return "\n".join(textos)
                
            return contenido
        except Exception as e:
            error_str = str(e)
            print(f"⚠️ Error detectado en la API de Google: {error_str}")
            
            if any(code in error_str for code in ("429", "503", "504", "RESOURCE_EXHAUSTED", "UNAVAILABLE", "DEADLINE_EXCEEDED")):
                return (
                    "⚠️ **Servicio temporalmente ocupado (429 / 503 / 504)**\n\n"
                    "Los servidores de Gemini están saturados o se alcanzó el límite de cuota gratuita. "
                    "Espera unos segundos y vuelve a intentar tu consulta."
                )
            if any(code in error_str for code in ("401", "403", "API_KEY", "PERMISSION_DENIED")):
                return (
                    "⚠️ **Error de autenticación con la API**\n\n"
                    "Verifica que `GOOGLE_API_KEY` en tu archivo `.env` sea válida y esté activa."
                )
            if "404" in error_str or "NOT_FOUND" in error_str:
                return (
                    "⚠️ **Modelo no disponible (404)**\n\n"
                    "El modelo configurado no fue encontrado en la API de Google. Revisa la configuración en `asistente.py`."
                )
            return (
                "⚠️ **Error inesperado al procesar la consulta**\n\n"
                f"Detalle técnico: `{error_str}`"
            )
