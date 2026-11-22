import os
from base_datos import GestorVectorial

EXTENSIONES_SOPORTADAS = ('.pdf', '.docx', '.xlsx', '.csv', '.png', '.jpg', '.jpeg')

if __name__ == "__main__":
    gestor = GestorVectorial()
    carpeta_documentos = "./documentos"
    
    if not os.path.exists(carpeta_documentos):
        print(f"⚠️ La carpeta '{carpeta_documentos}' no existe.")
        raise SystemExit(1)

    print("🚀 Iniciando indexación masiva de documentos...")
    
    for archivo in os.listdir(carpeta_documentos):
        ruta_completa = os.path.join(carpeta_documentos, archivo)
        
        if os.path.isfile(ruta_completa) and archivo.lower().endswith(EXTENSIONES_SOPORTADAS):
            print(f"\n📦 Procesando: {archivo}")
            gestor.guardar_archivo_en_db(ruta_completa)
            
    print("\n🔥 ¡Todo listo! Tu base de datos local está completamente poblada y lista.")
