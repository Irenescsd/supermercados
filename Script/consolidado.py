import pandas as pd
import os

# Ruta de la carpeta donde están los archivos CSV
ruta_carpeta = "D:\Supermercados\BD" 
# Lista para almacenar los DataFrames
dataframes = []

# Iterar sobre todos los archivos en la carpeta
for archivo in os.listdir(ruta_carpeta):
    if archivo.endswith(".csv"):
        ruta_archivo = os.path.join(ruta_carpeta, archivo)
        df = pd.read_csv(ruta_archivo)
        dataframes.append(df)

# Unir todos los DataFrames
df_unificado = pd.concat(dataframes, ignore_index=True)

# Guardar en un nuevo archivo CSV
df_unificado.to_csv("Base_supermercados.csv", index=False)

print("Archivos unificados en 'Base_supermercados.csv'")
