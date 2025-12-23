#==================JUMBO================

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
from webdriver_manager.chrome import ChromeDriverManager

# ===== Rutas de archivos =====
ARCHIVO_SALIDA = "D:/Supermercados/BD/JUMBO.csv" 
ARCHIVO_ESTADO = "D:/Supermercados/estado_progreso/estado_JUMBO.json"

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
    "Supermercado": {
        "url": "https://jumbo.com.do/catalogsearch/result/index/?p=1&q=Supermercado", 
        "max_paginas": 469
    },
    "Belleza Y Salud": {
        "url": "https://jumbo.com.do/catalogsearch/result/index/?p=1&q=Belleza Y Salud", 
        "max_paginas": 171
    },
    "Hogar": {
        "url": "https://jumbo.com.do/catalogsearch/result/index/?p=1&q=Hogar", 
        "max_paginas": 88
    },
    "Electrodomésticos": {
        "url": "https://jumbo.com.do/catalogsearch/result/index/?p=1&q=Electrodomésticos", 
        "max_paginas": 50
    },
    "Ferretería": {
        "url": "https://jumbo.com.do/catalogsearch/result/index/?p=1&q=Ferretería", 
        "max_paginas": 41
    },
    "Deportes": {
        "url": "https://jumbo.com.do/catalogsearch/result/index/?p=1&q=Deportes", 
        "max_paginas": 49
    },
    "Bebés": {
        "url": "https://jumbo.com.do/catalogsearch/result/index/?p=1&q=Bebés", 
        "max_paginas": 56
    },
    "Escolares Y Oficina": {
        "url": "https://jumbo.com.do/catalogsearch/result/index/?p=1&q=Escolares Y Oficina", 
        "max_paginas": 63
    },
    "Juguetería": {
        "url": "https://jumbo.com.do/catalogsearch/result/index/?p=1&q=Juguetería", 
        "max_paginas": 58
    },

    "Ofertas": {
        "url": "https://jumbo.com.do/catalogsearch/result/index/?p=1&q=Ofertas", 
        "max_paginas": 23
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
    Se ha corregido para buscar la clave 'hashes_procesados' o 'processed_hashes'
    para asegurar la compatibilidad con estados guardados anteriormente.
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
    Se han añadido más argumentos para simular un comportamiento humano y
    evitar las advertencias de la GPU.
    """
    options = Options()
    options.add_argument(f"user-agent={random.choice(USER_AGENTS)}")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-extensions")
    options.add_argument("--log-level=3")  # Oculta warnings y errores menores
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    #options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")  # Evita advertencias de GPU
    options.add_argument("--window-size=1280,1024")  # Simula un tamaño de pantalla común
    
    # Usa un directorio de usuario temporal para evitar errores de permisos en entornos limitados
    user_data_path = os.path.expanduser("~/.chrome_temp_data")
    options.add_argument(f"--user-data-dir={user_data_path}")
    
    # Excluye switches para evitar que el sitio web detecte que es un bot
    options.add_experimental_option("excludeSwitches", ["enable-logging", "enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
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
    new_rows = []
    new_hashes = []
    fecha_extraccion = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
    
    intentos = 0
    max_intentos = 3
    
    while intentos < max_intentos:
        try:
            driver.get(url)
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//li[@class='tile-item product-item-tile']|//div[@class='product-item-info']"))
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
        productos = driver.find_elements(By.XPATH, "//li[@class='tile-item product-item-tile']")
        
        if not productos:
            print("No se encontraron productos en la página.")
            return [], []
        
        for producto in productos:
            try:
                nombre = producto.find_element(By.XPATH, ".//div[@class = 'product-item-tile__name']").text.strip()
            except NoSuchElementException:
                nombre = "Nombre no disponible"

            try:
                precio_bruto = producto.find_element(By.XPATH, ".//div[@class='price-box price-final_price']").text.strip()
                precio = limpiar_precio(precio_bruto)
            except NoSuchElementException:
                precio = None
            
            if nombre != "Nombre no disponible" and precio is not None:
                hash_val = crear_hash_producto(nombre, precio, fecha_extraccion)
                if hash_val not in hashes_procesados:
                    new_rows.append({
                        "Supermercado": "JUMBO",
                        "Fecha_extraccion": fecha_extraccion,
                        "Categoria": categoria,
                        "Articulo": nombre,
                        "Precio": precio
                    })
                    new_hashes.append(hash_val)
        
        return new_rows, new_hashes
    
    except Exception as e:
        print(f"Error extrayendo productos de {url}: {e}")
        return [], []


def anadir_a_csv(datos, ruta_archivo):
    """Añade los datos a un archivo CSV."""
    df = pd.DataFrame(datos)
    df.to_csv(ruta_archivo, mode='a', header=not os.path.exists(ruta_archivo), index=False, encoding='utf-8-sig')
    print(f"Se añadieron {len(datos)} productos al CSV.")

from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

def cambiar_pagina(url_base, page_num):
    parsed = urlparse(url_base)
    query = parse_qs(parsed.query)
    query['p'] = [str(page_num)]
    new_query = urlencode(query, doseq=True)
    return urlunparse(parsed._replace(query=new_query))

# ========== PROCESO PRINCIPAL ==========
def jumbo():
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
                page_url = cambiar_pagina(url_base, page_num)
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
                time.sleep(random.uniform(5, 15)) 

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
    jumbo()
