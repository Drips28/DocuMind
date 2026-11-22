import os
from base_datos import GestorVectorial

if __name__ == "__main__":
    gestor = GestorVectorial()
    carpeta_documentos = "./documentos"
    
    print("🚀 Iniciando indexación masiva de documentos...")
    
    # Escaneamos la carpeta documentos
    for archivo in os.listdir(carpeta_documentos):
        ruta_completa = os.path.join(carpeta_documentos, archivo)
        
        # Validamos que sea un archivo soportado por tu LectorDocumentos
        if os.path.isfile(ruta_completa) and archivo.endswith(('.pdf', '.docx', '.xlsx', '.csv')):
            print(f"\n📦 Procesando: {archivo}")
            gestor.guardar_archivo_en_db(ruta_completa)
            
    print("\n🔥 ¡Todo listo! Tu base de datos local está completamente poblada y lista.")