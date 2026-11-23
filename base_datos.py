import os
import time
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from lector import LectorDocumentos

load_dotenv()


class GestorVectorial:
    def __init__(self, carpeta_db: str = "./chroma_db"):
        self.carpeta_db = carpeta_db
        self.embeddings = GoogleGenerativeAIEmbeddings(model="gemini-embedding-001")
        self.vector_store = None

    def _obtener_vector_store(self) -> Chroma:
        """Devuelve una instancia reutilizable de ChromaDB para evitar bloqueos de SQLite."""
        if not self.vector_store:
            self.vector_store = Chroma(
                persist_directory=self.carpeta_db,
                embedding_function=self.embeddings
            )
        return self.vector_store

    def eliminar_archivo_de_db(self, nombre_o_ruta: str) -> int:
        """Elimina todos los fragmentos previos asociados a un archivo por su nombre base."""
        vector_store = self._obtener_vector_store()
        nombre_objetivo = os.path.basename(nombre_o_ruta)

        datos = vector_store.get(include=["metadatas"])
        ids = datos.get("ids") or []
        metadatas = datos.get("metadatas") or []

        ids_a_borrar = [
            doc_id
            for doc_id, meta in zip(ids, metadatas)
            if isinstance(meta, dict) and os.path.basename(meta.get("source", "")) == nombre_objetivo
        ]

        if ids_a_borrar:
            vector_store.delete(ids=ids_a_borrar)
            print(f"🧹 Se eliminaron {len(ids_a_borrar)} fragmentos previos de '{nombre_objetivo}' para evitar duplicados.")
        return len(ids_a_borrar)

    def guardar_archivo_en_db(self, ruta_archivo: str, reemplazar: bool = True):
        """Lee cualquier archivo, lo fragmenta y lo guarda en ChromaDB en bloques para evitar el Error 429."""
        vector_store = self._obtener_vector_store()

        if reemplazar:
            self.eliminar_archivo_de_db(ruta_archivo)
        else:
            datos = vector_store.get(include=["metadatas"])
            nombre_objetivo = os.path.basename(ruta_archivo)
            metadatas = datos.get("metadatas") or []
            ya_existe = any(
                isinstance(meta, dict) and os.path.basename(meta.get("source", "")) == nombre_objetivo
                for meta in metadatas
            )
            if ya_existe:
                print(f"⏭️ '{nombre_objetivo}' ya estaba indexado en ChromaDB. Saltando...")
                return

        lector = LectorDocumentos(ruta_archivo)
        fragmentos = lector.procesar()

        if not fragmentos:
            print(f"⚠️ No se generaron fragmentos para el archivo: {ruta_archivo}")
            return

        print(f"🧠 Preparando la indexación de {len(fragmentos)} fragmentos...")

        tamano_bloque = 50
        tamanio_minilote = 5

        for i in range(0, len(fragmentos), tamano_bloque):
            bloque = fragmentos[i : i + tamano_bloque]

            for j in range(0, len(bloque), tamanio_minilote):
                minilote = bloque[j : j + tamanio_minilote]
                frag_inicio = i + j
                frag_fin = frag_inicio + len(minilote)

                print(
                    f"📥 Subiendo minilote {j // tamanio_minilote + 1} (Fragmentos {frag_inicio} al {frag_fin})..."
                )
                vector_store.add_documents(documents=minilote)

                if j + tamanio_minilote < len(bloque):
                    print("⏱️ Esperando 4 segundos para evitar el límite de la API...")
                    time.sleep(4)

        print("💾 ¡Base de datos unificada y guardada con éxito!")

    def buscar_similitud(self, pregunta: str, cantidad_resultados: int = 3):
        """Busca los fragmentos de texto más parecidos a la pregunta del usuario."""
        vector_store = self._obtener_vector_store()
        print(f"🔍 Buscando en la base de datos: '{pregunta}'")
        return vector_store.similarity_search(pregunta, k=cantidad_resultados)


if __name__ == "__main__":
    gestor = GestorVectorial()
    archivo_a_procesar = "documentos/BBVA 03 26.pdf"
    if os.path.exists(archivo_a_procesar):
        gestor.guardar_archivo_en_db(archivo_a_procesar)
        pregunta_prueba = "Cual es el numero de cuenta o cliente"
        print("\n--------------------------------------------------")
        fragmentos_encontrados = gestor.buscar_similitud(pregunta_prueba)
        print(f"\n🎯 Se encontraron {len(fragmentos_encontrados)} fragmentos relevantes:")
        for i, doc in enumerate(fragmentos_encontrados):
            print(f"\n[Resultado {i+1}] (Fuente: {doc.metadata.get('source')})")
            print(f"Contenido: {doc.page_content[:250]}...")
    else:
        print(f"⚠️ Archivo de prueba no encontrado: {archivo_a_procesar}")