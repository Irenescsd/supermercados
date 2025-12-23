#=============Supermercado Nacional====================

import os
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import time
import random
from datetime import datetime
import json
import re
import hashlib

# ===== Rutas de archivos =====
ARCHIVO_SALIDA = "D:/Supermercados/BD/Supermercado_Nacional.csv" 
ARCHIVO_ESTADO = "D:/Supermercados/estado_progreso/estado_SuperNacional.json"

# ===== Configuración inicial y para evitar detección =====
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/113.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
]

# ===== Categorías con límites específicos =====
CATEGORIAS = {
    "Carnes, Pescados y Mariscos": {"url": "https://supermercadosnacional.com/carnes-pescados-y-mariscos", "max_paginas": 21},
    "Frutas y Vegetales": {"url": "https://supermercadosnacional.com/frutas-y-vegetales", "max_paginas": 9},
    "Platos Preparados": {"url": "https://supermercadosnacional.com/platos-preparados", "max_paginas": 1},
    "Lácteos y Huevos": {"url": "https://supermercadosnacional.com/lacteos-y-huevos", "max_paginas": 33},
    "Quesos y Embutidos": {"url": "https://supermercadosnacional.com/quesos-y-embutidos", "max_paginas": 39},
    "Panadería y Repostería": {"url": "https://supermercadosnacional.com/panaderia-y-reposteria", "max_paginas": 19},
    "Congelados": {"url": "https://supermercadosnacional.com/congelados", "max_paginas": 16},
    "Despensa": {"url": "https://supermercadosnacional.com/despensa", "max_paginas": 186},
    "Bebidas": {"url": "https://supermercadosnacional.com/bebidas", "max_paginas": 33},
    "Cervezas, Vinos y Licores": {"url": "https://supermercadosnacional.com/cervezas-vinos-y-licores", "max_paginas": 22},
    "Limpieza y Desechables": {"url": "https://supermercadosnacional.com/limpieza-y-desechables", "max_paginas": 56},
    "Salud y Belleza": {"url": "https://supermercadosnacional.com/salud-y-belleza", "max_paginas": 44},
    "Bebé": {"url": "https://supermercadosnacional.com/bebe", "max_paginas": 19},
    "Mascotas": {"url": "https://supermercadosnacional.com/mascotas", "max_paginas": 6},
    "Complementos del Hogar": {"url": "https://supermercadosnacional.com/complementos-del-hogar", "max_paginas": 14}
}

# ===== Funciones para manejar estado del progreso (JSON) =====
def cargar_estado():
    """Lee el estado del progreso desde un archivo JSON."""
    try:
        if os.path.exists(ARCHIVO_ESTADO):
            with open(ARCHIVO_ESTADO, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}
    except (FileNotFoundError, json.JSONDecodeError):
        print("Advertencia: No se pudo cargar el estado del progreso. Iniciando desde el principio.")
        return {}

def guardar_estado(progreso):
    """Guarda el estado del progreso en un archivo JSON."""
    os.makedirs(os.path.dirname(ARCHIVO_ESTADO), exist_ok=True)
    with open(ARCHIVO_ESTADO, "w", encoding="utf-8") as f:
        json.dump(progreso, f, ensure_ascii=False, indent=2)

def obtener_progreso_categoria(progreso, nombre_cat, max_paginas):
    """
    Obtiene o inicializa el progreso de una categoría.
    """
    if nombre_cat not in progreso:
        progreso[nombre_cat] = {
            'pagina_actual': 1,
            'completada': False,
            'hashes_procesados': []
        }
    
    # Manejo de compatibilidad con versiones anteriores
    if 'processed_hashes' in progreso[nombre_cat]:
        progreso[nombre_cat]['hashes_procesados'] = progreso[nombre_cat].pop('processed_hashes')

    return progreso[nombre_cat]

def configurar_driver():
    """
    Configura y retorna el driver de Selenium con opciones para evitar detección.
    Ademas argumentos para simular un comportamiento humano y
    evitar las advertencias de la GPU.
    """
    options = Options()
    options.add_argument(f"user-agent={random.choice(USER_AGENTS)}")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-extensions")
    options.add_argument("--log-level=3")  # Elimina mensajes de registro innecesarios
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    #options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")  # Evita advertencias de GPU
    #options.add_argument("--window-size=1920,1080")  # Simula un tamaño de pantalla común
    
    # Usa un directorio de usuario temporal para evitar errores de permisos en entornos limitados
    user_data_path = os.path.expanduser("~/.chrome_temp_data")
    options.add_argument(f"--user-data-dir={user_data_path}")
    
    # Excluye switches para evitar que el sitio web detecte que es un bot
    options.add_experimental_option("excludeSwitches", ["enable-logging", "enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(options=options)
    # Ejecuta un script para ocultar la propiedad "navigator.webdriver"
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', { get: () => undefined })"
    })
    return driver

def limpiar_precio(texto):
    """Limpia la cadena de precio y la convierte a float."""
    if not isinstance(texto, str):
        return None
    # Elimina símbolos de moneda, comas y espacios, luego extrae el primer nÃºmero
    texto_limpio = re.sub(r'RD|\$|\s', '', texto).replace(',', '')
    try:
        # Busca un patrón de número entero o flotante
        match = re.search(r'\d+(\.\d+)?', texto_limpio)
        if match:
            return float(match.group(0))
        return None
    except (ValueError, AttributeError):
        return None

def crear_hash_producto(nombre, precio, fecha_extraccion):
    """
    Crea un hash único para un producto, incluyendo la fecha de extracción.
    Esto permite guardar registros históricos del mismo producto.
    """
    # Se convierte el precio a cadena para asegurar consistencia
    return hashlib.md5(f"{nombre}_{str(precio)}_{fecha_extraccion}".encode('utf-8')).hexdigest()

def extraer_pagina(driver, url, hashes_procesados, categoria):
    """
    Extrae productos de una página específica con un mecanismo de reintento.
    Se ha añadido un bucle para intentar cargar la página hasta 3 veces.
    """
    new_rows = []
    new_hashes = []
    fecha_extraccion = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
    
    intentos = 0
    max_intentos = 3
    
    while intentos < max_intentos:
        try:
            driver.get(url)
            # Espera a que los productos estén presentes, con un tiempo de espera más largo
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CLASS_NAME, "product-item-info"))
            )
            
            # Si el elemento está presente, salimos del bucle de reintento
            break
            
        except (TimeoutException, WebDriverException) as e:
            intentos += 1
            print(f"Error al cargar la página ({e}). Intento {intentos}/{max_intentos}.")
            time.sleep(random.uniform(5, 10))
            if intentos == max_intentos:
                print(f"No se pudo cargar la página después de {max_intentos} intentos. Saltando: {url}")
                return [], []
            
    # Se procede con el scraping una vez que la página ha cargado
    try:
        productos = driver.find_elements(By.CLASS_NAME, "product-item-info")
        
        if not productos:
            print("No se encontraron productos en la página.")
            return [], []
            
        for producto in productos:
            try:
                nombre = producto.find_element(By.CLASS_NAME, 'product-item-name').text.strip()
            except NoSuchElementException:
                nombre = "Nombre no disponible"
            
            try:
                precio_bruto = producto.find_element(By.CLASS_NAME, 'price').text.strip()
                precio = limpiar_precio(precio_bruto)
            except NoSuchElementException:
                precio = None


            if nombre != "Nombre no disponible" and precio is not None:
                hash_val = crear_hash_producto(nombre, precio, fecha_extraccion)
                if hash_val not in hashes_procesados:
                    new_rows.append({
                        "Supermercado": "Nacional",
                        "Fecha_extraccion": fecha_extraccion,
                        "Categoria": categoria, #para que la categoria tenga solo el nombre de supermercado se escribe "supermercado", asi entre comillas.
                        "Articulo": nombre,
                        "Precio": precio
                    })
                    new_hashes.append(hash_val)

        return new_rows, new_hashes

    except Exception as e:
        print(f"Error extrayendo productos de {url}: {e}")
        return [], []

def anadir_a_csv(datos, ruta_archivo):
    df = pd.DataFrame(datos)
    df.to_csv(ruta_archivo, mode='a', header=not os.path.exists(ruta_archivo), index=False, encoding='utf-8-sig')
    print(f"Se añadieron {len(datos)} productos al CSV.")

# ========== PROCESO PRINCIPAL ==========
def nacional():
    progreso = cargar_estado()
    driver = configurar_driver()
    
    try:
        for categoria, info in CATEGORIAS.items():
            url_base = info["url"]
            max_paginas = info["max_paginas"]
            
            progreso_cat = obtener_progreso_categoria(progreso, categoria, max_paginas)

            if progreso_cat['completada']:
                print(f"\nCategoría '{categoria}' ya procesada. Saltando...")
                continue
                
            print(f"\n=== Procesando categoría: {categoria} ===")
            print(f"Continuando desde la página {progreso_cat['pagina_actual']} de {max_paginas}...")

            for page_num in range(progreso_cat['pagina_actual'], max_paginas + 1): 
                # Si la categoría no tiene paginación o si es la primera página, usar la URL base

                if categoria == "Platos Preparados":
                    page_url = url_base
                elif max_paginas == 1 or page_num == 1:
                    page_url = url_base
                else:
                    page_url = f"{url_base}?p={page_num}"

                #if max_paginas == 1 or page_num ==1:
                   # page_url =url_base
                #else:
                   # page_url = f"{url_base}?p={page_num}"
                print(f"Procesando página {page_num} de {max_paginas}")

                filas, hashes = extraer_pagina(driver, page_url, progreso_cat['hashes_procesados'], categoria)

                if not filas:
                    print("Página vacía o error. No se añaden productos. Terminando la categoría.")
                    progreso_cat['completada'] = True
                    break
                
                anadir_a_csv(filas, ARCHIVO_SALIDA)
                
                # Actualizar el estado del progreso
                progreso_cat['pagina_actual'] = page_num + 1
                progreso_cat['hashes_procesados'].extend(hashes)
                guardar_estado(progreso)
                print(f"Estado guardado (categoría: {categoria}, página: {page_num + 1})")
                time.sleep(random.uniform(5, 15)) # Tiempo de espera moderado para ser menos detectable

            # Al completar, marcar como completada y guardar el estado
            progreso_cat['completada'] = True
            guardar_estado(progreso)
            print(f"Categoría '{categoria}' completada.")

    except KeyboardInterrupt:
        print("\nProceso interrumpido por el usuario")
        guardar_estado(progreso)
        print("Estado guardado correctamente.")

    except Exception as e:
        print(f"\nError crítico: {e}")
        # Guardar el estado antes de la falla
        guardar_estado(progreso)
        print("Estado guardado antes del fallo.")
        
    finally:
        driver.quit()
        print("\nProceso finalizado.")

if __name__ == "__main__":
    nacional()















