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
    
    # 1. Inicializar una llave única en session_state para el uploader si no existe
    if "uploader_key" not in st.session_state:
        st.session_state.uploader_key = 0

    # 2. Asignar la llave dinámica al file_uploader
    archivos_subidos = st.file_uploader(
        "Arrastra tus archivos aquí",
        type=["pdf", "docx", "xlsx", "csv"],
        accept_multiple_files=True,
        key=f"uploader_{st.session_state.uploader_key}"
    )
    
    if archivos_subidos:
        if st.button("🚀 Procesar e Indexar", use_container_width=True):
            # Asegurar que la carpeta documentos exista
            os.makedirs("./documentos", exist_ok=True)
            
            with st.spinner("Procesando e indexando en ChromaDB..."):
                for archivo in archivos_subidos:
                    ruta_destino = os.path.join("./documentos", archivo.name)
                    
                    # 1. Guardar el archivo físicamente en la carpeta local
                    with open(ruta_destino, "wb") as f:
                        f.write(archivo.getbuffer())
                    
                    # 2. Indexarlo usando tu GestorVectorial
                    st.session_state.gestor.guardar_archivo_en_db(ruta_destino)
                
                # 3. Reiniciar la instancia del asistente para que cargue los nuevos vectores
                st.session_state.asistente = AsistenteRAG()
                
            st.success("¡Archivos indexados con éxito!")
            
            # 4. Cambiamos el identificador del uploader para forzar que se limpie visualmente
            st.session_state.uploader_key += 1
            st.rerun()

    st.divider()
    
    # Listado visual de los archivos almacenados localmente
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

# --- CUERPO PRINCIPAL ---
st.title("🤖 Asistente RAG")
st.caption("Consulta tus documentos de forma segura y privada.")

# Mostrar los mensajes anteriores del historial
for mensaje in st.session_state.mensajes:
    with st.chat_message(mensaje["rol"]):
        st.markdown(mensaje["contenido"])

# Caja de entrada de texto para el usuario
if pregunta_usuario := st.chat_input("Escribe tu pregunta aquí..."):
    
    # 1. Mostrar la pregunta del usuario en la pantalla
    with st.chat_message("user"):
        st.markdown(pregunta_usuario)
    
    # 2. Agregar al historial en memoria
    st.session_state.mensajes.append({"rol": "user", "contenido": pregunta_usuario})
    
    # 3. Generar la respuesta del asistente con animación de carga
    with st.chat_message("assistant"):
        with st.spinner("Consultando documentos en la base de datos..."):
            respuesta = st.session_state.asistente.responder_pregunta(pregunta_usuario)
            st.markdown(respuesta)
            
    # 4. Agregar la respuesta de la IA al historial
    st.session_state.mensajes.append({"rol": "assistant", "contenido": respuesta})