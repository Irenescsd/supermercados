#Iberia
import os
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from selenium.webdriver.common.action_chains import ActionChains
import time
import random
from datetime import datetime
import json
import re
import hashlib
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from webdriver_manager.chrome import ChromeDriverManager

# ===== Rutas de archivos =====
ARCHIVO_SALIDA = "D:/Supermercados/BD/IBERIA.csv" 
ARCHIVO_ESTADO = "D:/Supermercados/estado_progreso/estado_IBERIA.json"

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
    "Abarrotes": {
        "url": "https://hipermercadosiberia.com/product-category/abarrotes/",
        "max_paginas": 16
    },
    "Limpieza": {
        "url": "https://hipermercadosiberia.com/product-category/uncategorized/",
        "max_paginas": 1
    },
    "Aceites": {
        "url": "https://hipermercadosiberia.com/product-category/aceites/",
        "max_paginas": 1
    },
    "Arroz": {
        "url": "https://hipermercadosiberia.com/product-category/arroz/",
        "max_paginas": 1
    },
    "Bebes": {
        "url": "https://hipermercadosiberia.com/product-category/bebes/",
        "max_paginas": 1
    },
    "Bebidas": {
        "url": "https://hipermercadosiberia.com/product-category/bebidas/",
        "max_paginas": 1
    },
    "Cafeteria y Restaurante": {
        "url": "https://hipermercadosiberia.com/product-category/cafeteria-restaurante/",
        "max_paginas": 1
    },
    "Caldos": {
        "url": "https://hipermercadosiberia.com/product-category/caldos/",
        "max_paginas": 1
    },
    "Carnes": {
        "url": "https://hipermercadosiberia.com/product-category/carnes/",
        "max_paginas": 1
    },
    "Cereales": {
        "url": "https://hipermercadosiberia.com/product-category/cereales/",
        "max_paginas": 1
    },
    "Condimentos": {
        "url": "https://hipermercadosiberia.com/product-category/condimentos/",
        "max_paginas": 1
    },
    "Cosmeticos": {
        "url": "https://hipermercadosiberia.com/product-category/cosmeticos/",
        "max_paginas": 1
    },
    "De Primera": {
        "url": "https://hipermercadosiberia.com/product-category/de-primera/",
        "max_paginas": 1
    },
    "Desechables": {
        "url": "https://hipermercadosiberia.com/product-category/desechables/",
        "max_paginas": 1
    },
    "Electrodomesticos": {
        "url": "https://hipermercadosiberia.com/product-category/electrodomesticos/",
        "max_paginas": 1
    },
    "Enlatados": {
        "url": "https://hipermercadosiberia.com/product-category/enlatados/",
        "max_paginas": 1
    },
    "Farmacia": {
        "url": "https://hipermercadosiberia.com/product-category/farmacia/",
        "max_paginas": 1
    },
    "Frutas": {
        "url": "https://hipermercadosiberia.com/product-category/frutas/",
        "max_paginas": 1
    },
    "Galletas": {
        "url": "https://hipermercadosiberia.com/product-category/galletas/",
        "max_paginas": 1
    },
    "Graneria": {
        "url": "https://hipermercadosiberia.com/product-category/graneria-2/",
        "max_paginas": 1
    },
    "Harinas": {
        "url": "https://hipermercadosiberia.com/product-category/harinas/",
        "max_paginas": 1
    },
    "Higiene y Aseo": {
        "url": "https://hipermercadosiberia.com/product-category/higiene-y-aseo-personal/",
        "max_paginas": 1
    },
    "Vegetales": {
        "url": "https://hipermercadosiberia.com/product-category/vegetales/",
        "max_paginas": 1
    },
    "Hogar": {
        "url": "https://hipermercadosiberia.com/product-category/hogar/",
        "max_paginas": 1
    },
    "Lacteos": {
        "url": "https://hipermercadosiberia.com/product-category/lacteos/",
        "max_paginas": 1
    },
    "Muebleria": {
        "url": "https://hipermercadosiberia.com/product-category/muebleria/",
        "max_paginas": 1
    },
    "Pan": {
        "url": "https://hipermercadosiberia.com/product-category/pan/",
        "max_paginas": 1
    },
    "Panaderia y Reposteria": {
        "url": "https://hipermercadosiberia.com/product-category/panaderia-y-reposteria/",
        "max_paginas": 1
    },
    "Pasta": {
        "url": "https://hipermercadosiberia.com/product-category/pastas/",
        "max_paginas": 1
    },
    "Picadera": {
        "url": "https://hipermercadosiberia.com/product-category/picaderas/",
        "max_paginas": 1
    },
    "Queso y Embutido": {
        "url": "https://hipermercadosiberia.com/product-category/quesos-embutidos/",
        "max_paginas": 1
    },
    "Sazones": {
        "url": "https://hipermercadosiberia.com/product-category/sazones/",
        "max_paginas": 1
    },
    "Untables": {
        "url": "https://hipermercadosiberia.com/product-category/untables/",
        "max_paginas": 1
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
    """Obtiene o inicializa el progreso de una categoría."""
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
    """Configura y retorna el driver de Selenium con opciones para evitar detección."""
    options = Options()
    options.add_argument(f"user-agent={random.choice(USER_AGENTS)}")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-extensions")
    options.add_argument("--log-level=3")  # Oculta warnings y errores menores
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # options.add_argument("--headless")  # Descomentado para poder ver el proceso de hover
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--window-size=1280,1024")
    
    user_data_path = os.path.expanduser("~/.chrome_temp_data")
    options.add_argument(f"--user-data-dir={user_data_path}")
    
    options.add_experimental_option("excludeSwitches", ["enable-logging", "enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', { get: () => undefined })"
    })
    return driver

def limpiar_precio(texto):
    """Limpia la cadena de precio y la convierte a float."""
    if not isinstance(texto, str):
        return None
    # Elimina símbolos de moneda, comas y espacios, luego extrae el primer número
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
    """Crea un hash único para un producto, incluyendo la fecha de extracción."""
    return hashlib.md5(f"{nombre}_{str(precio)}_{fecha_extraccion}".encode('utf-8')).hexdigest()

def extraer_pagina(driver, url, hashes_procesados, categoria):
    """Extrae productos de una página de Hipermercados IBERIA."""
    new_rows = []
    new_hashes = []
    fecha_extraccion = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
    
    intentos = 0
    max_intentos = 2
    
    while intentos < max_intentos:
        try:
            driver.get(url)
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//div[@class='product-inner  clearfix']"))
            )
            break
        except (TimeoutException, WebDriverException) as e:
            intentos += 1
            print(f"Error al cargar la página ({e}). Intento {intentos}/{max_intentos}.")
            time.sleep(random.uniform(1.5, 2.5))
            if intentos == max_intentos:
                print(f"No se pudo cargar la página después de {max_intentos} intentos. Saltando: {url}")
                return [], []

    try:
        # Buscar productos en la página
        productos = driver.find_elements(By.XPATH, "//div[@class='product-inner  clearfix']")
        
        if not productos:
            print("No se encontraron productos en la página.")
            return [], []
        
        print(f"Encontrados {len(productos)} productos en la página")
        
        for i, producto in enumerate(productos):
            try:
                # Hacer hover sobre el producto para activar los detalles
                actions = ActionChains(driver)
                actions.move_to_element(producto).perform()
                time.sleep(random.uniform(0.5, 1.5))  # Esperar a que aparezca el hover
                
                nombre = None
                precio = None
                
                try:
                    # Intentar extraer nombre del hover
                    nombre_element = producto.find_element(By.XPATH, ".//div[@class='mf-product-details-hover']//h2/a")
                    nombre = nombre_element.text.strip() if nombre_element.text else nombre_element.get_attribute("textContent").strip()
                except NoSuchElementException:
                    try:
                        # Fallback: buscar nombre en otro lugar
                        nombre_element = producto.find_element(By.XPATH, ".//h2/a")
                        nombre = nombre_element.text.strip() if nombre_element.text else nombre_element.get_attribute("textContent").strip()
                    except NoSuchElementException:
                        nombre = "Nombre no disponible"

                try:
                    # Intentar extraer precio del hover
                    precio_element = producto.find_element(By.XPATH, ".//div[contains(@class, 'mf-product-details-hover')]//span[@class='woocommerce-Price-amount amount']")
                    precio_bruto = precio_element.text.strip() if precio_element.text else precio_element.get_attribute("textContent").strip()
                    precio = limpiar_precio(precio_bruto)
                except NoSuchElementException:
                    try:
                        # Fallback: buscar precio en otro lugar
                        precio_element = producto.find_element(By.XPATH, ".//span[@class='price']")
                        precio_bruto = precio_element.text.strip() if precio_element.text else precio_element.get_attribute("textContent").strip()
                        precio = limpiar_precio(precio_bruto)
                    except NoSuchElementException:
                        precio = None
                
                if nombre and nombre != "Nombre no disponible" and precio is not None:
                    hash_val = crear_hash_producto(nombre, precio, fecha_extraccion)
                    if hash_val not in hashes_procesados:
                        new_rows.append({
                            "Supermercado": "IBERIA",
                            "Fecha_extraccion": fecha_extraccion,
                            "Categoria": categoria,
                            "Articulo": nombre,
                            "Precio": precio
                        })
                        new_hashes.append(hash_val)
                        print(f"  Producto {i+1}: {nombre} - ${precio}")
                    else:
                        print(f"  Producto {i+1}: Ya procesado anteriormente")
                else:
                    print(f"  Producto {i+1}: Datos incompletos (nombre: {nombre}, precio: {precio})")
                
                # Pausa pequeña entre productos
                #time.sleep(random.uniform(0.1, 0.5))
                
            except Exception as e:
                print(f"Error procesando producto {i+1}: {e}")
                continue
        
        return new_rows, new_hashes
    
    except Exception as e:
        print(f"Error extrayendo productos de {url}: {e}")
        return [], []

def anadir_a_csv(datos, ruta_archivo):
    """Añade los datos a un archivo CSV."""
    if datos:
        df = pd.DataFrame(datos)
        df.to_csv(ruta_archivo, mode='a', header=not os.path.exists(ruta_archivo), index=False, encoding='utf-8-sig')
        print(f"Se añadieron {len(datos)} productos al CSV.")
    else:
        print("No hay datos para añadir al CSV.")

def cambiar_pagina(url_base, page_num):
    """Construye la URL para una página específica."""
    if page_num == 1:
        return url_base
    else:
        if url_base.endswith('/'):
            return f"{url_base}page/{page_num}/"
        else:
            return f"{url_base}/page/{page_num}/"

# ========== PROCESO PRINCIPAL ==========
def iberia():
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
                print(f"Procesando página {page_num} de {max_paginas}: {page_url}")

                filas, hashes = extraer_pagina(driver, page_url, progreso_cat['hashes_procesados'], categoria)

                if not filas:
                    print("Página vacía o error. No se añaden productos.")
                    if max_paginas == 1:  # Si solo hay una página, marcar como completada
                        progreso_cat['completada'] = True
                        break
                else:
                    anadir_a_csv(filas, ARCHIVO_SALIDA)
                
                # Actualizar el estado del progreso
                progreso_cat['pagina_actual'] = page_num + 1
                progreso_cat['hashes_procesados'].extend(hashes)
                guardar_estado(progreso)
                print(f"Estado guardado (categoría: {categoria}, página: {page_num + 1})")
                
                # Pausa entre páginas
                #time.sleep(random.uniform(1.5, 2.5))

            # Al completar todas las páginas, marcar como completada
            progreso_cat['completada'] = True
            guardar_estado(progreso)
            print(f"Categoría '{categoria}' completada.")
            
            # Pausa entre categorías
            time.sleep(random.uniform(1, 2))

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
        print("\nProceso finalizado.")

if __name__ == "__main__":
    iberia()