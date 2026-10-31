import os
import streamlit as st
from src.core.asistente import AsistenteRAG
from src.storage.base_datos import GestorVectorial

st.set_page_config(page_title="DocuMind RAG", page_icon="🤖", layout="centered")

if "asistente" not in st.session_state:
    st.session_state.asistente = AsistenteRAG()
if "gestor" not in st.session_state:
    st.session_state.gestor = GestorVectorial()
if "mensajes" not in st.session_state:
    st.session_state.mensajes = []

with st.sidebar:
    st.subheader("📁 Control de Documentos")
    st.caption("Conectado a ChromaDB Local")
    
    if st.button("🗑️ Limpiar Conversación", use_container_width=True):
        st.session_state.mensajes = []
        st.rerun()
        
    st.divider()
    st.subheader("📤 Subir Nuevos Archivos")
    
    if "uploader_key" not in st.session_state:
        st.session_state.uploader_key = 0

    archivos_subidos = st.file_uploader(
        "Arrastra tus archivos aquí",
        type=["pdf", "docx", "xlsx", "csv"],
        accept_multiple_files=True,
        key=f"uploader_{st.session_state.uploader_key}"
    )
    
    if archivos_subidos:
        if st.button("🚀 Procesar e Indexar", use_container_width=True):
            os.makedirs("./documentos", exist_ok=True)
            with st.spinner("Procesando e indexando en ChromaDB..."):
                for archivo in archivos_subidos:
                    ruta_destino = os.path.join("./documentos", archivo.name)
                    with open(ruta_destino, "wb") as f:
                        f.write(archivo.getbuffer())
                    st.session_state.gestor.guardar_archivo_en_db(ruta_destino)
                
                st.session_state.asistente = AsistenteRAG()
                
            st.success("¡Archivos indexados con éxito!")
            st.session_state.uploader_key += 1
            st.rerun()
            
    st.divider()
    st.subheader("📚 Biblioteca Local")
    carpeta_docs = "./documentos"
    if os.path.exists(carpeta_docs):
        archivos_locales = [f for f in os.listdir(carpeta_docs) if os.path.isfile(os.path.join(carpeta_docs, f))]
        if archivos_locales:
            for arch in archivos_locales:
                st.text(f"• {arch}")
        else:
            st.caption("No hay archivos en ./documentos")
    else:
        st.caption("Carpeta ./documentos no encontrada")

st.title("🤖 DocuMind RAG")
st.caption("Consulta tus documentos de forma segura y privada.")

for mensaje in st.session_state.mensajes:
    with st.chat_message(mensaje["rol"]):
        st.markdown(mensaje["contenido"])

if pregunta_usuario := st.chat_input("Escribe tu pregunta aquí..."):
    with st.chat_message("user"):
        st.markdown(pregunta_usuario)
    st.session_state.mensajes.append({"rol": "user", "contenido": pregunta_usuario})
    
    with st.chat_message("assistant"):
        with st.spinner("Consultando documentos en la base de datos..."):
            respuesta = st.session_state.asistente.responder_pregunta(pregunta_usuario)
            st.markdown(respuesta)
            
    st.session_state.mensajes.append({"rol": "assistant", "contenido": respuesta})