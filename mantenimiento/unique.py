def extraer_unicos_txt():
    archivo_entrada = "D:\Supermercados\BD\PlazaLama"  
    archivo_salida = "splazalama.csv"      
    
    try:
        with open(archivo_entrada, "r", encoding="utf-8") as f:
            lineas = [linea.strip() for linea in f.readlines() if linea.strip()]
        
        encabezado = lineas[0]
        datos = lineas[1:]

        # Elimina duplicados sin ordenar
        unicos = list(dict.fromkeys(datos))

        with open(archivo_salida, "w", encoding="utf-8") as f:
            f.write(encabezado + "\n")
            f.write("\n".join(unicos))

        print(f"✓ Se extrajeron {len(unicos)} líneas únicas (sin contar encabezado)")
        print(f"✓ Guardados en: {archivo_salida}")
        print("\nMuestra de resultados:")
        print(encabezado)
        print("\n".join(unicos[:5]) + ("\n..." if len(unicos)>5 else ""))

    except Exception as e:
        print(f"Error: {str(e)}")

extraer_unicos_txt()
