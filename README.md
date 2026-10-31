# DocuMind RAG — Asistente Inteligente de Consulta Documental

DocuMind RAG es una solución web de arquitectura **Retrieval-Augmented Generation (RAG)** orientada a la extracción sintética y consulta conversacional sobre documentación técnica, reportes y estados de cuenta. El sistema mitiga alucinaciones en modelos de lenguaje al condicionar las respuestas a citas textuales verificables con número de página.

---

## Equipo y Roles (Metodología Scrum)

* **Al Otsil Winik Jasso Romero:** Líder Técnico — Arquitectura RAG, Prompt Engineering y Orquestación LLM.
* **Diego Mondragón Aparicio:** Ingeniero de Vectores — Gestión de ChromaDB y Búsqueda Semántica por Similitud.
* **Johan Javier Díaz Malagón:** Ingeniero de APIs — Construcción de Endpoints REST y Comunicación Cliente-Servidor.
* **Santiago Valencia Flores:** Frontend & UI — Interfaz Web Interactiva y Componentes de Visualización de Citas.
* **Miguel Cervantes Zabatrico:** Ingeniero de Calidad (QA) — Validación de Chunking, Pruebas de Integración y Métricas RAG.

---

## Arquitectura del Pipeline

1. **Ingesta Híbrida y OCR Multimodal:** Procesamiento de texto plano en archivos `.pdf`, `.docx`, `.xlsx` y `.csv`. En páginas escaneadas o sin capa de texto, se activa un fallback con visión multimodal (`gemini-2.5-flash`).
2. **Chunking Semántico:** Fragmentación recursiva del contenido en bloques de 1,000 caracteres con 150 caracteres de solapamiento (*overlap*) para evitar discontinuidad contextual.
3. **Indexación Vectorial:** Transformación del texto a representaciones vectoriales densas con `gemini-embedding-001` y almacenamiento local persistente en `ChromaDB`.
4. **Control de Flujo (Anti-429):** Mecanismo de subida en minilotes controlados y pausas preventivas para mitigar bloqueos por límite de tasa de llamadas (*Rate Limit*).
5. **Recuperación MMR y Generación:** Búsqueda por Máxima Relevancia Marginal (*Maximal Marginal Relevance*) e inyección dinámica del contexto con metadatos de origen para desplegar citas directas.

---

## Tecnologías Empleadas

* **Lenguaje:** Python 3.10+
* **Framework RAG:** LangChain / LangChain Google GenAI
* **Base de Datos Vectorial:** ChromaDB
* **Modelos de IA:** Google Gemini (`gemini-2.5-flash`, `gemini-embedding-001`)
* **Extracción Documental:** PyMuPDF (fitz), PyPDF, Python-Docx, Pandas
* **Interfaz de Usuario:** Streamlit

---

## Guía de Instalación y Uso

### 1. Clonar el repositorio
```bash
git clone [https://github.com/Johann-crypto725/documind-rag.git](https://github.com/Johann-crypto725/documind-rag.git)
cd documind-rag