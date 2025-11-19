#plalama

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
ARCHIVO_SALIDA = "D:/Supermercados/BD/PlazaLama.csv" 
ARCHIVO_ESTADO = "D:/Supermercados/estado_progreso/estado_Plaza_Lama.json"

# ===== Configuración inicial mejorada =====
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/113.0"
]

# ===== Categorías de PlazaLama =====
CATEGORIAS = {
    #"Supermercado": {"url": "https://plazalama.com.do/ca/supermercado/11"}, # Este enlace extrae la categoria de supermercado completa, pero es mejor hacer el scroll por categoria asi es mas facil acceder a todos por las subcategorias de esta categoria de supermercado
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

# ===== Funciones para manejar estado del progreso =====
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

def obtener_progreso_categoria(progreso, nombre_cat):
    """Obtiene o inicializa el progreso de una categoría."""
    fecha_hoy = datetime.now().strftime('%d-%m-%Y')
    
    if nombre_cat not in progreso:
        progreso[nombre_cat] = {
            'fecha_ultima_ejecucion': fecha_hoy,
            'completada': False,
            'hashes_procesados': [],
            'productos_totales': 0
        }
    else:
        if progreso[nombre_cat].get('fecha_ultima_ejecucion') != fecha_hoy:
            print(f"Nuevo día detectado para '{nombre_cat}'. Reiniciando progreso.")
            progreso[nombre_cat] = {
                'fecha_ultima_ejecucion': fecha_hoy,
                'completada': False,
                'hashes_procesados': [],
                'productos_totales': 0
            }
    
    return progreso[nombre_cat]

def configurar_driver():
    """Configura y retorna el driver de Selenium con opciones mejoradas."""
    options = Options()
    
    # Opciones mejoradas para estabilidad
    options.add_argument(f"user-agent={random.choice(USER_AGENTS)}")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Para mayor estabilidad, quitar headless temporalmente
    # options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    
    # Configuración de tiempoouts
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-renderer-backgrounding")
    options.add_argument("--disable-backgrounding-occluded-windows")

    try:
        service = Service()
        driver = webdriver.Chrome(service=service, options=options)
        
        # Script para evitar detección
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": random.choice(USER_AGENTS)
        })
        
        return driver
    except Exception as e:
        print(f"Error configurando el driver: {e}")
        raise

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
    except (ValueError, AttributeError):
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

def obtener_total_productos_esperados(driver):
    """Obtiene el número total de productos esperados según el contador de la página."""
    try:
        # Múltiples selectores posibles para el contador
        selectores = [
            "//span[@class='products-length']",
            "//span[contains(@class, 'products-length')]",
            "//div[contains(text(), 'productos') or contains(text(), 'items')]"
        ]
        
        for selector in selectores:
            try:
                elementos = driver.find_elements(By.XPATH, selector)
                for elemento in elementos:
                    texto = elemento.text.strip()
                    numeros = re.findall(r'\d+', texto)
                    if numeros:
                        total_esperado = int(numeros[0])
                        print(f"Total de productos esperados: {total_esperado}")
                        return total_esperado
            except:
                continue
                
    except Exception as e:
        print(f"No se pudo obtener el contador de productos: {e}")
    
    return None

def extraer_datos_visibles(driver, hashes_procesados, fecha_solo, fecha_extraccion, categoria):
    """Extrae los datos actualmente visibles en el viewport."""
    nuevos_datos = []
    nuevos_hashes = []
    
    # Selectores optimizados (basados en tu código)
    selectores_productos = [
        "//div[contains(@class, 'product-card')]",
        "//div[contains(@class, 'styles__StyledCard')]",
        "//div[contains(@class, 'card')]"
    ]
    
    productos = []
    for selector in selectores_productos:
        elementos = driver.find_elements(By.XPATH, selector)
        if len(elementos) > 0:
            productos = elementos
            break # Usamos el primer selector que funcione
            
    for producto in productos:
        try:
            # Intentamos obtener el texto completo del elemento primero para ver si vale la pena procesarlo
            texto_bloque = producto.text
            if not texto_bloque or ("$" not in texto_bloque and "RD" not in texto_bloque):
                continue

            # --- Extracción de Nombre ---
            nombre = "Nombre no disponible"
            try:
                # Buscamos h3, h4, o clases específicas de nombre
                elem_nombre = producto.find_element(By.XPATH, ".//h3 | .//h4 | .//p[contains(@class, 'name')]")
                nombre = limpiar_nombre(elem_nombre.text)
            except:
                continue # Si no tiene nombre, saltamos

            # --- Extracción de Precio ---
            precio = None
            try:
                # Buscamos el precio
                elem_precio = producto.find_element(By.XPATH, ".//p[contains(@class, 'price')] | .//span[contains(@class, 'price')]")
                precio = limpiar_precio(elem_precio.text)
            except:
                continue # Si no tiene precio, saltamos

            # --- Validación y Hash ---
            if nombre and precio:
                hash_val = crear_hash_producto(nombre, precio, fecha_solo)
                
                # VERIFICACIÓN CRÍTICA: ¿Ya procesamos este producto hoy?
                # Verificamos tanto en el historial global como en los recolectados en esta ejecución
                if hash_val not in hashes_procesados:
                    nuevos_datos.append({
                        "Supermercado": "PlazaLama",
                        "Fecha_extraccion": fecha_extraccion,
                        "Categoria": categoria,
                        "Articulo": nombre,
                        "Precio": precio
                    })
                    nuevos_hashes.append(hash_val)
                    # Agregamos al set temporal para no duplicar si el scroll vuelve a ver el mismo
                    hashes_procesados.append(hash_val) 

        except Exception:
            continue # Si falla un producto individual, seguimos con el siguiente

    return nuevos_datos, nuevos_hashes

def extraer_categoria_completa(driver, url, hashes_procesados_previos, categoria):
    """
    Estrategia: Scroll -> Pausa -> Extraer -> Guardar -> Repetir.
    Esto evita la pérdida de datos por virtualización del DOM.
    """
    filas_totales = []
    hashes_nuevos_totales = []
    
    # Convertimos a set para búsqueda rápida (O(1)) en lugar de lista (O(n))
    # Nota: al final convertimos los nuevos a lista para guardar en JSON
    set_hashes_procesados = set(hashes_procesados_previos)
    
    fecha_extraccion = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
    fecha_solo = datetime.now().strftime('%d-%m-%Y')
    
    print(f"Cargando URL: {url}")
    driver.get(url)
    time.sleep(5) # Espera inicial
    
    # Intentar detectar el total esperado (opcional, solo informativo)
    total_esperado = obtener_total_productos_esperados(driver)
    
    last_height = driver.execute_script("return document.body.scrollHeight")
    intentos_sin_nuevos = 0
    max_intentos_sin_nuevos = 4  # Si scrollea 4 veces y no saca nada nuevo, termina.
    
    while True:
        # 1. EXTRAER LO QUE VEMOS AHORA
        datos_ronda, hashes_ronda = extraer_datos_visibles(
            driver, list(set_hashes_procesados), fecha_solo, fecha_extraccion, categoria
        )
        
        if datos_ronda:
            print(f"   -> Extraídos {len(datos_ronda)} productos nuevos en este bloque.")
            filas_totales.extend(datos_ronda)
            hashes_nuevos_totales.extend(hashes_ronda)
            # Actualizamos el set local para no re-capturarlos en el siguiente scroll
            for h in hashes_ronda:
                set_hashes_procesados.add(h)
            intentos_sin_nuevos = 0 # Reiniciamos contador de fallos
        else:
            intentos_sin_nuevos += 1
            # Scroll ligero hacia arriba y abajo para despertar "lazy loading" si está atascado
            if intentos_sin_nuevos == 2:
                driver.execute_script("window.scrollBy(0, -300);")
                time.sleep(1)
                driver.execute_script("window.scrollBy(0, 300);")
        
        # Condición de salida por falta de datos nuevos
        if intentos_sin_nuevos >= max_intentos_sin_nuevos:
            print("Se alcanzó el límite de intentos sin encontrar productos nuevos. Finalizando categoría.")
            break
            
        # 2. SCROLL
        # Hacemos scroll por pasos, no directo al fondo, para dar tiempo a cargar imágenes/datos
        driver.execute_script("window.scrollBy(0, 800);") # Bajar 800 pixeles
        time.sleep(2) # Esperar carga
        
        # Chequeo de altura (si llegamos al fondo físico de la página)
        new_height = driver.execute_script("return document.body.scrollHeight")
        
        # Si la altura no cambia, intentamos esperar un poco más o forzar scroll
        if new_height == last_height:
            # A veces el botón "Ver más" existe aunque haya scroll infinito
            try:
                boton_ver_mas = driver.find_element(By.XPATH, "//button[contains(text(), 'Ver más') or contains(text(), 'Cargar más')]")
                boton_ver_mas.click()
                time.sleep(3)
            except:
                pass # No hay botón, simplemente estamos al final o cargando
            
            # Si ya hemos intentado varias veces sin datos nuevos, el loop de arriba (intentos_sin_nuevos) nos sacará
        
        last_height = new_height
        
        # Reporte de progreso en consola
        print(f"Total acumulado: {len(filas_totales)} | Scroll intento sin éxito: {intentos_sin_nuevos}/{max_intentos_sin_nuevos}")

    print(f"Extracción finalizada. Total recolectado: {len(filas_totales)}")
    return filas_totales, hashes_nuevos_totales

    # Hacer scroll
    print(f"Iniciando proceso de scroll para '{categoria}'...")
    total_productos = scroll_mejorado(driver, categoria)
    
    if total_productos == 0:
        print("No se encontraron productos después del scroll.")
        return [], []
    
    # Extraer productos después del scroll
    try:
        print("Extrayendo productos finales...")
        
        # Selectores actualizados basados en el HTML proporcionado
        selectores_finales = [
            "//div[contains(@class, 'sc-3ccf89ec-3')]//div[contains(@class, 'card')]",
            "//div[contains(@class, 'styles__StyledCard')]",
            "//div[contains(@class, 'product-card')]"
        ]
        
        productos = []
        for selector in selectores_finales:
            try:
                elementos = driver.find_elements(By.XPATH, selector)
                if len(elementos) > len(productos):
                    productos = elementos
            except:
                continue
        
        if not productos:
            print("No se encontraron productos después de la extracción.")
            return [], []
            
        print(f"Procesando {len(productos)} productos encontrados...")
        productos_procesados = 0
        productos_validos = 0
        
        for i, producto in enumerate(productos):
            try:
                productos_procesados += 1
                
                # Extraer nombre - SELECTORES ACTUALIZADOS
                nombre = "Nombre no disponible"
                selectores_nombre = [
                    ".//p[contains(@class, 'prod__name')]",
                    ".//p[contains(@class, 'name')]",
                    ".//h3",
                    ".//h4",
                    ".//div[contains(@class, 'name')]"
                ]
                
                for selector in selectores_nombre:
                    try:
                        elemento = producto.find_element(By.XPATH, selector)
                        nombre_texto = elemento.text.strip()
                        if nombre_texto:
                            nombre = limpiar_nombre(nombre_texto)
                            break
                    except:
                        continue
                
                # Extraer precio - SELECTORES ACTUALIZADOS
                precio = None
                selectores_precio = [
                    ".//p[contains(@class, 'base__price')]",
                    ".//p[contains(@class, 'price')]",
                    ".//span[contains(@class, 'price')]",
                    ".//div[contains(@class, 'price')]"
                ]
                
                for selector in selectores_precio:
                    try:
                        elemento = producto.find_element(By.XPATH, selector)
                        precio_texto = elemento.text.strip()
                        if precio_texto:
                            precio = limpiar_precio(precio_texto)
                            if precio:
                                break
                    except:
                        continue
                
                # Validar y agregar producto
                if nombre != "Nombre no disponible" and precio is not None:
                    productos_validos += 1
                    hash_val = crear_hash_producto(nombre, precio, fecha_solo)
                    
                    if hash_val not in hashes_procesados:
                        new_rows.append({
                            "Supermercado": "PlazaLama",
                            "Fecha_extraccion": fecha_extraccion,
                            "Categoria": categoria,
                            "Articulo": nombre,
                            "Precio": precio
                        })
                        new_hashes.append(hash_val)
                
                # Mostrar progreso
                if productos_procesados % 50 == 0:
                    print(f"Procesados {productos_procesados}/{len(productos)} productos. Válidos: {productos_validos}")
                    
            except Exception as e:
                print(f"Error procesando producto {i + 1}: {e}")
                continue

        print(f"Extracción completada: {productos_validos} válidos, {len(new_rows)} nuevos")
        
        return new_rows, new_hashes

    except Exception as e:
        print(f"Error crítico extrayendo productos: {e}")
        return [], []

def anadir_a_csv(datos, ruta_archivo):
    """Añade los datos a un archivo CSV."""
    if not datos:
        print("No hay datos para añadir al CSV.")
        return
        
    df = pd.DataFrame(datos)
    df.to_csv(ruta_archivo, mode='a', header=not os.path.exists(ruta_archivo), index=False, encoding='utf-8-sig')
    print(f"Se añadieron {len(datos)} productos al CSV.")

# ========== PROCESO PRINCIPAL ==========
def plazalama():
    print("=== Iniciando scraper de PlazaLama ===")
    progreso = cargar_estado()
    
    try:
        driver = configurar_driver()
        
        for i, (categoria, info) in enumerate(CATEGORIAS.items()):
            url = info["url"]
            
            print(f"\n{'='*60}")
            print(f"Categoría {i+1}/{len(CATEGORIAS)}: {categoria}")
            print(f"{'='*60}")
            
            progreso_cat = obtener_progreso_categoria(progreso, categoria)

            if progreso_cat['completada']:
                print(f"Categoría '{categoria}' ya procesada HOY. Saltando...")
                continue

            # Extraer categoría
            filas, hashes = extraer_categoria_completa(driver, url, progreso_cat['hashes_procesados'], categoria)

            if filas:
                anadir_a_csv(filas, ARCHIVO_SALIDA)
                progreso_cat['hashes_procesados'].extend(hashes)
                progreso_cat['productos_totales'] = len(progreso_cat['hashes_procesados'])

            progreso_cat['completada'] = True
            guardar_estado(progreso)
            print(f"Categoría '{categoria}' completada. Total: {progreso_cat['productos_totales']} productos.")
            
            # Pausa entre categorías
            time.sleep(random.uniform(10, 15))

    except Exception as e:
        print(f"Error crítico: {e}")
        guardar_estado(progreso)
        
    finally:
        try:
            driver.quit()
        except:
            pass
        
        total_productos = sum(cat.get('productos_totales', 0) for cat in progreso.values() if isinstance(cat, dict))
        print(f"\nResumen final: {total_productos} productos extraídos.")

if __name__ == "__main__":
    plazalama()



    #No extrae todos los productos por categorias
    