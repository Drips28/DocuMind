import os
import json
import pandas as pd
import time  # 👈 1. Asegúrate de importar esto al inicio del archivo
from pypdf import PdfReader
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

# Cargar variables de entorno (.env)
load_dotenv()

def procesar_estado_cuenta_por_paginas(ruta_pdf):
    print(f"📖 Leyendo PDF: {ruta_pdf}...")
    lector = PdfReader(ruta_pdf)
    total_paginas = len(lector.pages)
    print(f"📄 Total de páginas detectadas: {total_paginas}")
    
    llm = ChatGoogleGenerativeAI(
        model="gemini-3.8-flash",
        temperature=0.1,
        response_mime_type="application/json"
    )
    
    todas_las_transacciones = []
    
    for index, pagina in enumerate(lector.pages):
        num_pagina = index + 1
        print(f"🧠 Analizando página {num_pagina}/{total_paginas}...")
        
        texto_pagina = pagina.extract_text()
        if not texto_pagina.strip():
            print(f"⚠️ Página {num_pagina} vacía. Saltando...")
            continue
            
        prompt = f"""
        Eres un analista financiero experto. Tu tarea es extraer TODAS las transacciones y movimientos bancarios del siguiente texto extraído de la página {num_pagina} de un estado de cuenta.
        
        Texto de la página:
        {texto_pagina}
        
        INSTRUCCIONES DE SALIDA:
        Devuelve un arreglo en formato JSON válido (e.g. [{{...}}, {{...}}]). Si en esta página no hay transacciones, devuelve un arreglo vacío [].
        
        Cada objeto dentro del arreglo debe tener exactamente estas llaves (keys):
        - "fecha_operacion": La fecha en que se hizo (ej: "25/FEB").
        - "fecha_liquidacion": La fecha de liquidación (ej: "24/FEB").
        - "descripcion": El concepto completo del movimiento (ej: "STRIPE *AMAZON").
        - "monto": El valor numérico del movimiento. Si es un cargo/retiro debe ser NEGATIVO. Si es un abono/depósito/pago recibido debe ser POSITIVO. No incluyas signos de pesos '$' ni comas ','.
        - "saldo": El saldo resultante si aparece en la línea (si no aparece, pon null).
        """
        
        # 👈 2. Bloque de Reintentos para mitigar el Error 429
        max_intentos = 3
        exito_pagina = False
        
        for intento in range(max_intentos):
            try:
                respuesta = llm.invoke(prompt)
                texto_json = respuesta.content.strip()
                datos_pagina = json.loads(texto_json)
                
                if isinstance(datos_pagina, list):
                    todas_las_transacciones.extend(datos_pagina)
                    print(f"✅ Se extrajeron {len(datos_pagina)} transacciones de la página {num_pagina}.")
                    exito_pagina = True
                    break  # Éxito, salimos del bucle de reintentos
                
            except Exception as e:
                # Si el error es por cuota/límite de velocidad
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    segundos_espera = 10 if intento == 0 else 20
                    print(f"⏳ Límite de velocidad alcanzado (429) en pág {num_pagina}. Esperando {segundos_espera}s para reintentar (Intento {intento+1}/{max_intentos})...")
                    time.sleep(segundos_espera)
                else:
                    print(f"❌ Error inesperado en página {num_pagina}: {e}")
                    break  # Si es otro tipo de error (JSON corrupto, etc.), no reintentamos
                    
        if not exito_pagina:
            print(f"💥 No se pudieron recuperar los datos de la página {num_pagina} tras {max_intentos} intentos.")
            
        # 👈 3. Pausa preventiva obligatoria entre páginas para no saturar el API Free
        time.sleep(4)
            
    return todas_las_transacciones

def guardar_en_excel(transacciones, ruta_salida):
    if not transacciones:
        print("❌ No se encontraron transacciones para guardar.")
        return
        
    print(f"💾 Generando archivo de Excel con {len(transacciones)} registros totales...")
    try:
        df = pd.DataFrame(transacciones)
        columnas_ordenadas = ["fecha_operacion", "fecha_liquidacion", "descripcion", "monto", "saldo"]
        df = df.reindex(columns=columnas_ordenadas)
        
        # Guardar a Excel real
        df.to_excel(ruta_salida, index=False, sheet_name="Movimientos Bancarios")
        print(f"🎉 ¡Éxito rotundo! Archivo de Excel guardado en: {ruta_salida}")
    except Exception as e:
        print(f"❌ Error al guardar el Excel: {e}")

if __name__ == "__main__":
    archivo_pdf = "BBVA 03 26.pdf" 
    archivo_excel_salida = "Reporte_Movimientos_BBVA.xlsx"
    
    if os.path.exists(archivo_pdf):
        movimientos = procesar_estado_cuenta_por_paginas(archivo_pdf)
        guardar_en_excel(movimientos, archivo_excel_salida)
    else:
        print(f"❌ No encontré el archivo '{archivo_pdf}' en la carpeta raíz.")