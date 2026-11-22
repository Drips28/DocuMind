# DocuMind RAG — Asistente Inteligente de Consulta Documental

DocuMind RAG es una aplicación web local construida con arquitectura **Retrieval-Augmented Generation (RAG)** que permite cargar documentos heterogéneos (PDF nativos, PDF escaneados, Word, Excel, CSV e imágenes), indexarlos en una base vectorial persistente (**ChromaDB**) y realizar consultas en lenguaje natural fundamentadas estrictamente en el contenido cargado.

## Arquitectura del Proyecto

```text
DocuMind/
├── app.py                  # Interfaz conversacional en Streamlit y gestión de estado
├── asistente.py            # Orquestador RAG, inventario real en ChromaDB y manejo de errores
├── base_datos.py           # GestorVectorial: embeddings, minilotes anti-429 y prevención de duplicados
├── lector.py               # LectorDocumentos: extracción multiformato + fallback OCR multimodal
├── indexar_todo.py         # Script de indexación masiva para la carpeta ./documentos
├── pdf_a_excel.py          # Utilidad auxiliar para extraer movimientos bancarios de PDF a Excel
├── iniciar.bat             # Lanzador portable en un clic para Windows
├── requirements.txt        # Dependencias del proyecto
├── .env.example            # Plantilla de variables de entorno
└── .streamlit/
    └── config.toml         # Tema visual oscuro (#00E5FF)
```

## Características Técnicas

* **Ingesta multiformato y OCR multimodal:** Soporta `.pdf`, `.docx`, `.xlsx`, `.csv`, `.png`, `.jpg` y `.jpeg`. Si una página PDF tiene menos de 50 caracteres nativos, se renderiza a 150 DPI con `PyMuPDF` y se procesa con visión multimodal (`gemini-3.8-flash`).
* **Chunking semántico:** `RecursiveCharacterTextSplitter` (`chunk_size=1000`, `chunk_overlap=150`).
* **Persistencia vectorial local:** Embeddings con `gemini-embedding-001` almacenados en `./chroma_db` mediante minilotes de 5 fragmentos con pausas preventivas y reemplazo automático para evitar duplicados.
* **Resiliencia y trazabilidad:** Recuperación por similitud (`k=5`), `timeout=60s`, `max_retries=1`, etiquetado de fuente por fragmento y manejo diferenciado de errores HTTP (429/503/504, 401/403, 404).

## Instalación y Uso

### 1. Clonar el repositorio y configurar credenciales
```bash
git clone [https://github.com/Drips28/DocuMind.git](https://github.com/Drips28/DocuMind.git)
cd DocuMind
cp .env.example .env
```
Edita `.env` y coloca tu clave real en `GOOGLE_API_KEY`.

### 2. Ejecutar la aplicación
* **En Windows (un clic):** Ejecuta `iniciar.bat`. El script crea el entorno virtual `venv`, instala dependencias y abre Streamlit automáticamente.
* **En macOS / Linux:**
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
  streamlit run app.py
  ```

### 3. Indexación masiva opcional (CLI)
Coloca archivos dentro de `./documentos` y ejecuta:
```bash
python indexar_todo.py
```

## Equipo de Desarrollo

* **Al Otsil Winik Jasso Romero** — Líder Técnico / Arquitectura
* **Diego Mondragón Aparicio** — Ingeniero de Vectores
* **Johan Javier Díaz Malagón** — Ingeniero de Integración / Backend
* **Santiago Valencia Flores** — Frontend & UI/UX
* **Miguel Zabat Cervantes Rico** — Ingeniero de Calidad / QA