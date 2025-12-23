
import pandas as pd
import os
from datetime import datetime

# Ruta de la carpeta con los CSV
ruta_carpeta = r"D:\Supermercados\BD"
dataframes = []

# Leer todos los CSV
for archivo in os.listdir(ruta_carpeta):
    if archivo.endswith(".csv"):
        ruta_archivo = os.path.join(ruta_carpeta, archivo)
        try:
            df = pd.read_csv(ruta_archivo, sep=',', encoding='utf-8-sig', on_bad_lines='skip')
            dataframes.append(df)
        except Exception as e:
            print(f"Error al leer {archivo}: {e}")

if dataframes:
    # Unificar todos los DataFrames
    df_unificado = pd.concat(dataframes, ignore_index=True)

    # Eliminar duplicados considerando TODAS las columnas
    filas_antes = len(df_unificado)
    df_unificado = df_unificado.drop_duplicates(keep='first')
    filas_despues = len(df_unificado)

    # Crear carpeta destino si no existe
    carpeta_destino = r"D:\Supermercados\Basecondolidada"
    os.makedirs(carpeta_destino, exist_ok=True)

    # Nombre con fecha actual
    fecha_actual = datetime.now().strftime("%Y-%m-%d")
    nombre_archivo = f"Base_supermercados_{fecha_actual}.csv"
    ruta_final = os.path.join(carpeta_destino, nombre_archivo)

    # Guardar archivo
    df_unificado.to_csv(ruta_final, index=False, encoding='utf-8-sig')

    print("\n==============================================")
    print(f"¡Archivos unificados con éxito!")
    print(f"Filas antes: {filas_antes} | Filas después (sin duplicados): {filas_despues}")
    print(f"Guardado en: {ruta_final}")
    print("==============================================")
else:
    print("No se encontraron archivos CSV.")