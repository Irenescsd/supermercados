  #=============SIRENA====================

import os
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from selenium.webdriver.remote.remote_connection import LOGGER
import time
import random
from datetime import datetime
import json
import re
import hashlib
import logging

# ===== Rutas de archivos =====
ARCHIVO_SALIDA = "D:/Supermercados/BD/Lasirena.csv" 
ARCHIVO_ESTADO = "D:/Supermercados/estado_progreso/estado_sirena.json"

# ===== Configuración inicial y para evitar detección =====
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/113.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
]


# ===== Categorías =====
CATEGORIAS = {
    "Escolares": {
        "url": "https://www.sirena.do/products/category/escolares-?page=1&limit=15&sort=1", 
        "max_paginas": 119
    },
    "Nuestras Marcas": {
        "url": "https://www.sirena.do/products/category/nuestras-marcas?page=1&limit=15&sort=1", 
        "max_paginas": 36
    },
    "Alimentación": {
        "url": "https://www.sirena.do/products/category/alimentacion?page=1&limit=15&sort=1", 
        "max_paginas": 322
    },
    "Frutas y Vegetales": {
        "url": "https://www.sirena.do/products/category/frutas-y-vegetales?page=1&limit=15&sort=1", 
        "max_paginas": 22
    },
    "Bebidas": {
        "url": "https://www.sirena.do/products/category/bebidas?page=1&limit=15&sort=1", 
        "max_paginas": 72
    },
    "Salud y Bienestar": {
        "url": "https://www.sirena.do/products/category/salud-bienestar?page=1&limit=15&sort=1", 
        "max_paginas": 10
    },
    "Cuidado Personal y Belleza": {
        "url": "https://www.sirena.do/products/category/cuidado-personal-y-belleza?page=1&limit=15&sort=1", 
        "max_paginas": 501
    },
    "Limpieza": {
        "url": "https://www.sirena.do/products/category/limpieza?page=1&limit=15&sort=1", 
        "max_paginas": 76
    },
    "Bebé": {
        "url": "https://www.sirena.do/products/category/bebes?page=1&limit=15&sort=1", 
        "max_paginas": 68
    },
    "Hogar y Electrodomésticos": {
        "url": "https://www.sirena.do/products/category/hogar-y-electrodomesticos?page=1&limit=15&sort=1", 
        "max_paginas": 160
    },
    "Ropa": {
        "url": "https://www.sirena.do/products/category/ropa?page=1&limit=15&sort=1", 
        "max_paginas": 4
    }
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
    
    """Configura y retorna el driver de Selenium con opciones para evitar detección.
    """
    options = Options()

    # Opciones de comportamiento
    options.add_argument(f"user-agent={random.choice(USER_AGENTS)}")
    options.add_argument("--window-size=1920,1080")
    
    # Opciones para modo headless (sin interfaz gráfica)
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    
    # Opciones específicas para eliminar errores de GPU/WebGL
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--disable-webgl")
    options.add_argument("--disable-3d-apis")
    options.add_argument("--disable-gpu-compositing")
    options.add_argument("--disable-gl-extensions")
    
    # Opciones para evitar detección como bot
    options.add_experimental_option("excludeSwitches", ["enable-logging", "enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
 
    options.add_argument("--log-level=0")  # Nivel 0 para mínimo logging

    # Configurar servicio con logging mínimo
    service = ChromeService(ChromeDriverManager().install())
    service.service_args = ["--silent", "--log-level=0"]
    # Creamos el driver usando webdriver-manager para gestionar la versión
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    
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

fecha = datetime.now().strftime('%d-%m-%Y')
def control_duplicados(nombre, precio, fecha):
    """
    Crea un hash único para un producto, incluyendo la fecha de extracción.
    Esto permite guardar registros históricos del mismo producto.
    """
    # Se convierte el precio a cadena para asegurar consistencia
    return hashlib.md5(f"{nombre}_{str(precio)}_{fecha}".encode('utf-8')).hexdigest()

def extraer_pagina(driver, url, hashes_procesados, categoria):
    """
    Extrae productos de la página Sirena.do
    """
    new_rows = []
    new_hashes = []
    fecha_extraccion = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
    
    intentos = 0
    max_intentos = 3
    
    while intentos < max_intentos:
        try:
            driver.get(url)
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//div[@data-test='grid-product']"))
            )
            break
        except (TimeoutException, WebDriverException) as e:
            intentos += 1
            print(f"Error al cargar la página ({e}). Intento {intentos}/{max_intentos}.")
            time.sleep(random.uniform(5, 10))
            if intentos == max_intentos:
                print(f"No se pudo cargar la página después de {max_intentos} intentos. Saltando: {url}")
                return [], []

    try:
        productos = driver.find_elements(By.XPATH, "//div[@data-test='grid-product']")
        
        if not productos:
            print("No se encontraron productos en la página.")
            return [], []
        
        for producto in productos:
            try:
                nombre = producto.find_element(By.CLASS_NAME, "item-product-title").text.strip()
            except NoSuchElementException:
                nombre = "Nombre no disponible"

            try:
                precio_bruto = producto.find_element(By.CSS_SELECTOR, ".item-product-price strong").text.strip()
                precio = limpiar_precio(precio_bruto)
            except NoSuchElementException:
                precio = None
            
            if nombre != "Nombre no disponible" and precio is not None:
                sin_duplicado = control_duplicados(nombre, precio, fecha_extraccion)
                if sin_duplicado not in hashes_procesados:
                    new_rows.append({
                        "Supermercado": "Sirena",
                        "Fecha_extraccion": fecha_extraccion,
                        "Categoria": categoria,
                        "Articulo": nombre,
                        "Precio": precio
                    })
                    new_hashes.append(sin_duplicado)
        
        return new_rows, new_hashes
    
    except Exception as e:
        print(f"Error extrayendo productos de {url}: {e}")
        return [], []


def anadir_a_csv(datos, ruta_archivo):
    """Añade los datos a un archivo CSV."""
    df = pd.DataFrame(datos)
    df.to_csv(ruta_archivo, mode='a', header=not os.path.exists(ruta_archivo), index=False, encoding='utf-8-sig')
    print(f"Se añadieron {len(datos)} productos al CSV.")

# ========== PROCESO PRINCIPAL ==========
def sirena():
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
                if page_num == 1:
                    page_url = url_base
                else:
                    page_url = re.sub(r'page=\d+', f'page={page_num}', url_base)

                print(f"Procesando página {page_num} de {max_paginas}")

                filas, hashes = extraer_pagina(driver, page_url, progreso_cat['hashes_procesados'], categoria)

                if not filas:
                    print("Página vacía o error. No se añaden productos. Terminando la categoría.")
                    progreso_cat['completada'] = True
                    break
                
                anadir_a_csv(filas, ARCHIVO_SALIDA)
                
                progreso_cat['pagina_actual'] = page_num + 1
                progreso_cat['hashes_procesados'].extend(hashes)
                guardar_estado(progreso)
                print(f"Estado guardado (categoría: {categoria}, página: {page_num + 1})")
                time.sleep(random.uniform(5, 15))

            progreso_cat['completada'] = True
            guardar_estado(progreso)
            print(f"Categoría '{categoria}' completada.")

    except KeyboardInterrupt:
        print("\nProceso interrumpido por el usuario")
        guardar_estado(progreso)
        print("Estado guardado correctamente.")

    except Exception as e:
        print(f"\nError crítico: {e}")
        guardar_estado(progreso)
        print("Estado guardado antes del fallo.")
        
    finally:
        driver.quit()
        print("\nExtracción completada. Limpiando duplicados del día...")

        try:
            if os.path.exists(ARCHIVO_SALIDA):
                df = pd.read_csv(ARCHIVO_SALIDA)

                # Extraer la fecha de extracción sin hora
                df["Fecha_dia"] = pd.to_datetime(df["Fecha_extraccion"], errors="coerce").dt.date

                # Eliminar duplicados del mismo día según Artículo + Precio
                antes = len(df)
                df = df.drop_duplicates(subset=["Articulo", "Precio", "Fecha_dia"], keep="first")
                despues = len(df)

                # Reescribir el archivo limpio
                df.drop(columns=["Fecha_dia"], inplace=True)
                df.to_csv(ARCHIVO_SALIDA, index=False, encoding="utf-8-sig")

                print(f"Duplicados del día eliminados: {antes - despues} filas borradas.")
                print(f"Total final: {despues} registros únicos del día.")
            else:
                print("No se encontró el archivo CSV para limpiar duplicados.")
        except Exception as e:
            print(f"Error limpiando duplicados: {e}")

        print("\nProceso finalizado correctamente ")


if __name__ == "__main__":
    sirena()