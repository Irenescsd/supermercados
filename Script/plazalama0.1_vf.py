# =====Plaza Lama =====

import os
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import time
import random
from datetime import datetime
import json
import re
import hashlib

# ===== Rutas de archivos =====
# NOTA: Se cambiaron a rutas locales para prueba. El usuario puede cambiarlas de nuevo.
ARCHIVO_SALIDA = "D:\Supermercados\BD\PlazaLama.csv"
ARCHIVO_ESTADO = "estado_Plaza_Lama.json"

# ===== Configuración inicial  =====
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/113.0"
]

# ===== Categorías=====
CATEGORIAS = {
    "Bebes y primera infancia": {"url": "https://plazalama.com.do/ca/supermercado/bebes-y-primera-infancia/11/11-40"},
    "Bebidas": {"url": "https://plazalama.com.do/ca/supermercado/bebidas/11/11-41"},
    "Carnes, Pescados y Mariscos": {"url": "https://plazalama.com.do/ca/supermercado/carnes-pescados-y-mariscos/11/11-43"},
    "Congelados": {"url": "https://plazalama.com.do/ca/supermercado/congelados/11/11-44"},
    "Cuidado del Hogar": {"url": "https://plazalama.com.do/ca/supermercado/cuidado-del-hogar/11/11-45"},
    "Despensa": {"url": "https://plazalama.com.do/ca/supermercado/despensa/11/11-46"},
    "Farmacia": {"url": "https://plazalama.com.do/ca/supermercado/farmacia/11/11-47"},
    "Belleza y Bienestar": {"url": "https://plazalama.com.do/ca/supermercado/belleza-y-bienestar/11/11-42"},
    "Frutas y Vegetales": {"url": "https://plazalama.com.do/ca/supermercado/frutas-y-vegetales/11/11-48"},
    "Lácteos y Huevos": {"url": "https://plazalama.com.do/ca/supermercado/lacteos-y-huevos/11/11-49"},
    "Mascotas": {"url": "https://plazalama.com.do/ca/supermercado/mascotas/11/11-50"},
    "Panaderia y Reposteria": {"url": "https://plazalama.com.do/ca/supermercado/panaderia-y-reposteria/11/11-51"},
    "Papeles y Desechables": {"url": "https://plazalama.com.do/ca/supermercado/papeles-y-desechables/11/11-52"},
    "Quesos y Embutidos": {"url": "https://plazalama.com.do/ca/supermercado/quesos-y-embutidos/11/11-53"},
    "Electrodomesticos": {"url": "https://plazalama.com.do/ca/electrodomesticos/4"},
    "Hogar": {"url": "https://plazalama.com.do/ca/hogar/6"},
    "Ferreteria y Automotores": {"url": "https://plazalama.com.do/ca/ferreteria-y-automotores/5"},
    "Deportes": {"url": "https://plazalama.com.do/ca/deportes/3"},
    "Juguetes": {"url": "https://plazalama.com.do/ca/juguetes/7"},
    "Libreria": {"url": "https://plazalama.com.do/ca/libreria/8"},
    "Moda": {"url": "https://plazalama.com.do/ca/moda/9"}
}

# ===== FUNCIONES AUXILIARES =====

def configurar_driver():
    """Configura y retorna el driver de Selenium con opciones mejoradas."""
    options = Options()
    options.add_argument(f"user-agent={random.choice(USER_AGENTS)}")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    # options.add_argument("--headless") # Descomentar para modo headless

    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        # Anti-detección básica
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    except Exception as e:
        print(f"Error configurando el driver: {e}")
        raise

def extraer_categoria_completa(driver, url, hashes_procesados, categoria):
    """Extrae todos los productos de una categoría iterando por paginación."""
    new_rows = []
    new_hashes = []
    fecha_extraccion = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
    fecha_solo = datetime.now().strftime('%d-%m-%Y')

    try:
        print(f"Cargando URL: {url}")
        driver.get(url)
        
        # Esperar a que cargue el contenedor principal o la paginación
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a.containerCard"))
            )
        except TimeoutException:
            print("Timeout esperando productos. Puede que la categoría esté vacía.")
            return [], []

        pagina_actual = 1
        while True:
            print(f"--- Procesando Página {pagina_actual} ---")
            
            # 1. Extraer productos de la página actual
            productos_pagina, hashes_pagina = extraer_productos_pagina(driver, hashes_procesados, categoria, fecha_extraccion, fecha_solo)
            new_rows.extend(productos_pagina)
            new_hashes.extend(hashes_pagina)
            
            # 2. Intentar ir a la siguiente página
            if not ir_a_siguiente_pagina(driver):
                print("No hay más páginas o se alcanzó el final.")
                break
            
            pagina_actual += 1
            # Pequeña pausa para asegurar carga
            time.sleep(3)

        print(f"Extracción completada para '{categoria}': {len(new_rows)} productos totales en {pagina_actual} páginas")
        return new_rows, new_hashes

    except Exception as e:
        print(f"Error procesando categoría: {e}")
        return [], []

def ir_a_siguiente_pagina(driver):
    """
    Busca el botón 'Next' de la paginación Ant Design y lo clickea.
    Retorna True si pudo avanzar, False si no.
    """
    try:
        # Selector basado en la imagen del usuario: li.ant-pagination-next
        # Verificamos si está deshabilitado (aria-disabled="true" o clase ant-pagination-disabled)
        
        # Opción A: Buscar el li next
        next_li = driver.find_element(By.CSS_SELECTOR, "li.ant-pagination-next")
        
        # Verificar si está deshabilitado
        aria_disabled = next_li.get_attribute("aria-disabled")
        clases = next_li.get_attribute("class")
        
        if aria_disabled == "true" or "ant-pagination-disabled" in clases:
            print("Botón 'Siguiente' deshabilitado. Fin de la paginación.")
            return False
            
        # Buscar el botón/enlace dentro del li (a veces es el li mismo el que recibe el click, o un button dentro)
        # En Ant Design suele ser el li o un button/a dentro. Intentaremos clickear el li o su hijo.
        try:
            boton_click = next_li.find_element(By.TAG_NAME, "button")
        except:
            boton_click = next_li # Si no hay button, clickeamos el li
            
        # Scroll y Click
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", boton_click)
        time.sleep(1)
        
        # Click JS es más robusto para estos elementos
        driver.execute_script("arguments[0].click();", boton_click)
        
        return True

    except NoSuchElementException:
        print("No se encontró barra de paginación (puede ser página única).")
        return False
    except Exception as e:
        print(f"Error al cambiar de página: {e}")
        return False

def extraer_productos_pagina(driver, hashes_procesados, categoria, fecha_extraccion, fecha_solo):
    """Extrae productos del DOM actual."""
    productos_data = []
    nuevos_hashes = []

    try:
        # SELECTOR CORREGIDO: a.containerCard
        productos = driver.find_elements(By.CSS_SELECTOR, "a.containerCard")

        if not productos:
            print("No se encontraron productos en el DOM.")
            return [], []

        print(f"Procesando {len(productos)} productos encontrados en el DOM...")
        productos_validos = 0

        for i, producto in enumerate(productos):
            try:
                # Extraer nombre - SELECTOR CORREGIDO
                # Estructura observada: a.containerCard > div > p:nth-of-type(2) (Descripción/Nombre)
                nombre = "Nombre no disponible"
                try:
                    # Usamos CSS Selector relativo
                    elemento_nombre = producto.find_element(By.CSS_SELECTOR, "div > p:nth-of-type(2)")
                    nombre_texto = elemento_nombre.text.strip()
                    if nombre_texto:
                        nombre = limpiar_nombre(nombre_texto)
                except NoSuchElementException:
                    pass

                # Extraer precio - SELECTOR CORREGIDO
                # Estructura observada: a.containerCard > div > p:nth-of-type(1) (Precio)
                precio = None
                try:
                    elemento_precio = producto.find_element(By.CSS_SELECTOR, "div > p:nth-of-type(1)")
                    precio_texto = elemento_precio.text.strip()
                    if precio_texto:
                        # Mantenemos el texto original o limpiamos según preferencia.
                        # El script original limpiaba a float.
                        precio = limpiar_precio(precio_texto) 
                except NoSuchElementException:
                    pass

                # Validar y agregar producto
                if nombre != "Nombre no disponible" and precio is not None:
                    productos_validos += 1
                    hash_val = crear_hash_producto(nombre, precio, fecha_solo)

                    if hash_val not in hashes_procesados:
                        productos_data.append({
                            "Supermercado": "PlazaLama",
                            "Fecha_extraccion": fecha_extraccion,
                            "Categoria": categoria,
                            "Articulo": nombre,
                            "Precio": precio
                        })
                        nuevos_hashes.append(hash_val)

            except Exception as e:
                continue

        print(f"Página procesada: {productos_validos} productos válidos, {len(productos_data)} nuevos")

    except Exception as e:
        print(f"Error extrayendo productos: {e}")

    return productos_data, nuevos_hashes

def cargar_estado():
    """Lee el estado del progreso desde un archivo JSON."""
    try:
        if os.path.exists(ARCHIVO_ESTADO):
            with open(ARCHIVO_ESTADO, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}
    except:
        return {}

def guardar_estado(progreso):
    """Guarda el estado del progreso en un archivo JSON."""
    try:
        with open(ARCHIVO_ESTADO, "w", encoding="utf-8") as f:
            json.dump(progreso, f, ensure_ascii=False, indent=2)
    except:
        pass

def obtener_progreso_categoria(progreso, nombre_cat):
    """Obtiene o inicializa el progreso de una categoría."""
    fecha_hoy = datetime.now().strftime('%d-%m-%Y')
    if nombre_cat not in progreso or progreso[nombre_cat].get('fecha_ultima_ejecucion') != fecha_hoy:
        progreso[nombre_cat] = {
            'fecha_ultima_ejecucion': fecha_hoy,
            'completada': False,
            'hashes_procesados': [],
            'productos_totales': 0
        }
    return progreso[nombre_cat]

def limpiar_precio(texto):
    """Limpia la cadena de precio y la convierte a float."""
    if not isinstance(texto, str):
        return None
    texto_limpio = re.sub(r'RD|\$|\s', '', texto).replace(',', '')
    try:
        match = re.search(r'\d+(\.\d+)?', texto_limpio)
        if match:
            return float(match.group(0))
        return None
    except:
        return None

def limpiar_nombre(texto):
    """Limpia el nombre del producto."""
    if not isinstance(texto, str):
        return None
    texto = re.sub(r'\.{3,}$', '', texto)
    texto = re.sub(r'\s+', ' ', texto)
    return texto.strip()

def crear_hash_producto(nombre, precio, fecha_solo):
    """Crea un hash único para un producto."""
    return hashlib.md5(f"{nombre}_{str(precio)}_{fecha_solo}".encode('utf-8')).hexdigest()

def anadir_a_csv(datos, ruta_archivo):
    """Añade los datos a un archivo CSV."""
    if not datos:
        return
    df = pd.DataFrame(datos)
    df.to_csv(ruta_archivo, mode='a', header=not os.path.exists(ruta_archivo), index=False, encoding='utf-8-sig')
    print(f"Se añadieron {len(datos)} productos al CSV.")

# ========== PROCESO PRINCIPAL ==========
def plazalama():
    print("=== Iniciando scraper de PlazaLama (Corregido) ===")
    progreso = cargar_estado()

    driver = None
    try:
        driver = configurar_driver()

        # TEST: Solo 1 categoría para verificar
        for i, (categoria, info) in enumerate(CATEGORIAS.items()): 
            url = info["url"]

            print(f"\n{'='*60}")
            print(f"Categoría {i+1}: {categoria}")
            print(f"{'='*60}")

            progreso_cat = obtener_progreso_categoria(progreso, categoria)

            # Extraer categoría
            filas, hashes = extraer_categoria_completa(driver, url, progreso_cat['hashes_procesados'], categoria)

            if filas:
                anadir_a_csv(filas, ARCHIVO_SALIDA)
                progreso_cat['hashes_procesados'].extend(hashes)
                progreso_cat['productos_totales'] = len(progreso_cat['hashes_procesados'])

            progreso_cat['completada'] = True
            guardar_estado(progreso)
            print(f"Categoría '{categoria}' completada. Total: {progreso_cat['productos_totales']} productos.")

    except Exception as e:
        print(f"Error crítico en el proceso principal: {e}")
        guardar_estado(progreso)

    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass
        print(f"\nProceso finalizado.")

if __name__ == "__main__":
    plazalama()