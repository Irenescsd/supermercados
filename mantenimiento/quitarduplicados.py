#Eliminar duplicados tomando en cuenta la fecha y otras variables
import pandas as pd

# Cargar el archivo histórico
archivo = "D:\Supermercados\BD\PlazaLama"
df = pd.read_csv(archivo)

# Convertir la columna de fecha a datetime




#df["Fecha_extraccion"] = pd.to_datetime(df["Fecha_extraccion"], format='%d-%m-%Y %H:%M:%S')

# Crear una columna nueva solo con la fecha (sin hora)
#df["Fecha"] = df["Fecha_extraccion"].dt.date

# Ordenar por fecha completa (más reciente primero)
#df = df.sort_values(by="Fecha_extraccion", ascending=False)

# Eliminar duplicados por combinación de medicamento y fecha
df_limpio = df.drop_duplicates(subset=["Fecha_extraccion","Categoria", "Articulo","Precio"], keep="first")

# Guardar en nuevo CSV limpio
df_limpio.to_csv("plaplazalama.csv", index=False)

print(f"Limpieza completa. Registros únicos por medicamento y fecha: {len(df_limpio)}")
print(f"Registros duplicados eliminados: {len(df) - len(df_limpio)}")
