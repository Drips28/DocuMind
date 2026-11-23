import os
import streamlit as st
from asistente import AsistenteRAG
from base_datos import GestorVectorial

# 1. Configuración de la página (Debe ser el primer comando de Streamlit)
st.set_page_config(page_title="DocuMind", page_icon="🤖", layout="centered")

# 2. Inicializar el asistente y el gestor en la sesión para no recargarlos en cada click
if "asistente" not in st.session_state:
    st.session_state.asistente = AsistenteRAG()
if "gestor" not in st.session_state:
    st.session_state.gestor = GestorVectorial()

# 3. Inicializar el historial de chat si no existe
if "mensajes" not in st.session_state:
    st.session_state.mensajes = []

# --- BARRA LATERAL (Sidebar) ---
with st.sidebar:
    st.subheader("📁 Control de Documentos")
    st.caption("Conectado a ChromaDB Local")
    
    # Botón para limpiar el historial de la pantalla
    if st.button("🗑️ Limpiar Conversación", use_container_width=True):
        st.session_state.mensajes = []
        st.rerun()
        
    st.divider()
    
    # --- GESTIÓN DINÁMICA DE ARCHIVOS ---
    st.subheader("📤 Subir Nuevos Archivos")
    
    if "uploader_key" not in st.session_state:
        st.session_state.uploader_key = 0

    archivos_subidos = st.file_uploader(
        "Arrastra tus archivos aquí",
        type=["pdf", "docx", "xlsx", "csv", "png", "jpg", "jpeg"],
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
    
    # Listado visual de los archivos almacenados localmente con eliminación sincronizada (CRUD - Delete)
    st.subheader("📚 Biblioteca Local")
    carpeta_docs = "./documentos"
    if os.path.exists(carpeta_docs):
        archivos_locales = sorted(
            f for f in os.listdir(carpeta_docs)
            if os.path.isfile(os.path.join(carpeta_docs, f)) and not f.startswith(".")
        )
        if archivos_locales:
            for arch in archivos_locales:
                col_nombre, col_borrar = st.columns([4, 1])
                with col_nombre:
                    st.text(f"• {arch}")
                with col_borrar:
                    if st.button("🗑️", key=f"del_{arch}", help=f"Eliminar {arch}"):
                        ruta_eliminar = os.path.join(carpeta_docs, arch)
                        with st.spinner(f"Eliminando {arch}..."):
                            if os.path.exists(ruta_eliminar):
                                os.remove(ruta_eliminar)
                            st.session_state.gestor.eliminar_archivo_de_db(ruta_eliminar)
                            st.session_state.asistente = AsistenteRAG()
                        st.toast(f"Archivo '{arch}' eliminado del disco y de ChromaDB.")
                        st.rerun()
        else:
            st.caption("No hay archivos en ./documentos")
    else:
        st.caption("Carpeta ./documentos no encontrada")

# --- CUERPO PRINCIPAL ---
st.title("🤖 Asistente RAG")
st.caption("Consulta tus documentos de forma segura y privada.")

# Mostrar los mensajes anteriores del historial
for mensaje in st.session_state.mensajes:
    with st.chat_message(mensaje["rol"]):
        if mensaje["rol"] == "assistant" and mensaje["contenido"].startswith("⚠️"):
            st.warning(mensaje["contenido"])
        else:
            st.markdown(mensaje["contenido"])

# Caja de entrada de texto para el usuario
if pregunta_usuario := st.chat_input("Escribe tu pregunta aquí..."):
    with st.chat_message("user"):
        st.markdown(pregunta_usuario)
    
    st.session_state.mensajes.append({"rol": "user", "contenido": pregunta_usuario})
    
    with st.chat_message("assistant"):
        with st.spinner("Consultando documentos en la base de datos..."):
            respuesta = st.session_state.asistente.responder_pregunta(pregunta_usuario)
            if isinstance(respuesta, str) and respuesta.startswith("⚠️"):
                st.warning(respuesta)
            else:
                st.markdown(respuesta)
            
    st.session_state.mensajes.append({"rol": "assistant", "contenido": respuesta})
