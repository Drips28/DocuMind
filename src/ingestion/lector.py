import os
import io
import base64
import pandas as pd
import fitz  # PyMuPDF
from docx import Document as DocxReader
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

class LectorDocumentos:
    """
    Clase encargada de procesar diferentes formatos de archivos (incluyendo imágenes 
    y PDFs escaneados mediante visión multimodal) y unificar su contenido en objetos 'Document' de LangChain.
    """
    def __init__(self, ruta_archivo: str):
        self.ruta_archivo = ruta_archivo
        self.extension = os.path.splitext(ruta_archivo)[1].lower()
        self.llm_vision = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)

    def procesar(self) -> list[Document]:
        """Detecta la extensión, ejecuta el lector adecuado y divide el texto si es necesario."""
        if not os.path.exists(self.ruta_archivo):
            print(f"❌ Error: El archivo no existe en la ruta: {self.ruta_archivo}")
            return []
            
        documentos_crudos = []
        
        if self.extension == ".pdf":
            documentos_crudos = self._leer_pdf_inteligente()
        elif self.extension == ".docx":
            documentos_crudos = self._leer_docx()
        elif self.extension in [".xlsx", ".csv"]:
            return self._leer_tabla()
        elif self.extension in [".png", ".jpg", ".jpeg"]:
            documentos_crudos = self._leer_imagen()
        else:
            print(f"⚠️ Formato {self.extension} no soportado todavía.")
            return []

        if not documentos_crudos:
            return []

        print("✂️ Dividiendo el texto en fragmentos óptimos para la IA...")
        cortador = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=150,
            length_function=len
        )
        fragmentos_finales = cortador.split_documents(documentos_crudos)
        return fragmentos_finales

    def _leer_pdf_inteligente(self) -> list[Document]:
        """Intenta leer texto normal. Si una página está vacía (escaneada), usa Visión Multimodal."""
        print(f"📖 Leyendo PDF (Modo Inteligente): {os.path.basename(self.ruta_archivo)}...")
        documentos = []
        
        try:
            cargador = PyPDFLoader(self.ruta_archivo)
            docs_normales = cargador.load()
        except Exception:
            docs_normales = []

        doc_fitz = fitz.open(self.ruta_archivo)
        
        for index, pagina_fitz in enumerate(doc_fitz):
            num_pag = index + 1
            texto_extraido = docs_normales[index].page_content if index < len(docs_normales) else ""
            
            if len(texto_extraido.strip()) > 50:
                meta = {"source": self.ruta_archivo, "type": "pdf", "page": num_pag}
                documentos.append(Document(page_content=texto_extraido, metadata=meta))
            else:
                print(f"👁️ Página {num_pag} es una imagen/escaneada. Aplicando Visión Multimodal...")
                pix = pagina_fitz.get_pixmap(dpi=150)
                bytes_imagen = pix.tobytes("png")
                
                mensaje = HumanMessage(
                    content=[
                        {
                            "type": "text",
                            "text": f"Extrae todo el texto, datos y contenido relevante de esta página {num_pag} del documento de forma clara y estructurada."
                        },
                        {
                            "type": "image_url",
                            "image_url": f"data:image/png;base64,{base64.b64encode(bytes_imagen).decode('utf-8')}"
                        }
                    ]
                )
                
                try:
                    respuesta = self.llm_vision.invoke([mensaje])
                    meta = {"source": self.ruta_archivo, "type": "pdf_vision", "page": num_pag}
                    documentos.append(Document(page_content=respuesta.content, metadata=meta))
                except Exception as e:
                    print(f"⚠️ Error procesando la página {num_pag} con visión: {e}")
                    
        return documentos

    def _leer_imagen(self) -> list[Document]:
        print(f"👁️ Analizando Imagen con Visión Multimodal: {os.path.basename(self.ruta_archivo)}...")
        with open(self.ruta_archivo, "rb") as f:
            bytes_imagen = f.read()
            
        mensaje = HumanMessage(
            content=[
                {
                    "type": "text",
                    "text": "Analiza esta imagen detalladamente, extrae todo su texto, tablas, diagramas o información relevante para que pueda ser indexada."
                },
                {
                    "type": "image_url",
                    "image_url": f"data:image/png;base64,{base64.b64encode(bytes_imagen).decode('utf-8')}"
                }
            ]
        )
        
        try:
            respuesta = self.llm_vision.invoke([mensaje])
            meta = {"source": self.ruta_archivo, "type": "image"}
            return [Document(page_content=respuesta.content, metadata=meta)]
        except Exception as e:
            print(f"❌ Error al procesar la imagen: {e}")
            return []

    def _leer_docx(self) -> list[Document]:
        print(f"📖 Leyendo Word: {os.path.basename(self.ruta_archivo)}...")
        doc = DocxReader(self.ruta_archivo)
        texto_completo = "\n".join([párrafo.text for párrafo in doc.paragraphs if párrafo.text.strip()])
        meta = {"source": self.ruta_archivo, "type": "docx"}
        return [Document(page_content=texto_completo, metadata=meta)]

    def _leer_tabla(self) -> list[Document]:
        print(f"📖 Leyendo Tabla: {os.path.basename(self.ruta_archivo)}...")
        if self.extension == ".csv":
            df = pd.read_csv(self.ruta_archivo)
        else:
            df = pd.read_excel(self.ruta_archivo)
            
        documentos = []
        for indice, fila in df.iterrows():
            contenido_fila = " | ".join([f"{col}: {val}" for col, val in fila.items() if pd.notna(val)])
            meta = {"source": self.ruta_archivo, "type": self.extension, "row": indice}
            documentos.append(Document(page_content=contenido_fila, metadata=meta))
            
        return documentos