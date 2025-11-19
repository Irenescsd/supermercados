
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

def scroll_mejorado(driver, categoria):
    """
    Hace scroll hasta el final con verificación mejorada.
    """
    print(f"Iniciando scroll para la categoría: {categoria}")
    
    total_esperado = obtener_total_productos_esperados(driver)
    
    productos_anteriores = 0
    intentos_sin_cambios = 0
    max_intentos_sin_cambios = 5  # Aumentado
    scroll_attempts = 0
    max_scroll_attempts = 50
    
    start_time = time.time()
    max_tiempo_total = 600  # 10 minutos máximo
    
    last_height = driver.execute_script("return document.body.scrollHeight")
    
    while scroll_attempts < max_scroll_attempts:
        if time.time() - start_time > max_tiempo_total:
            print(f"TIMEOUT: Límite de tiempo alcanzado")
            break
            
        scroll_attempts += 1
        
        try:
            # Scroll suave
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            
            # Esperar a que carguen nuevos elementos
            WebDriverWait(driver, 10).until(
                lambda driver: driver.execute_script("return document.body.scrollHeight") > last_height
            )
            
            # Actualizar altura
            new_height = driver.execute_script("return document.body.scrollHeight")
            last_height = new_height
            
            # Contar productos actuales - SELECTORES ACTUALIZADOS
            selectores_productos = [
                "//div[contains(@class, 'styles__StyledCard')]",
                "//div[contains(@class, 'product-card')]",
                "//div[contains(@class, 'card')]",
                "//div[@class='sc-3ccf89ec-3 hSxl21']//div[contains(@class, 'card')]"  # Basado en tu HTML
            ]
            
            productos_actuales = 0
            for selector in selectores_productos:
                try:
                    productos = driver.find_elements(By.XPATH, selector)
                    if len(productos) > productos_actuales:
                        productos_actuales = len(productos)
                except:
                    continue
            
            # Mostrar progreso
            if total_esperado:
                porcentaje = (productos_actuales / total_esperado) * 100
                print(f"Scroll {scroll_attempts}: {productos_actuales}/{total_esperado} productos ({porcentaje:.1f}%)")
            else:
                print(f"Scroll {scroll_attempts}: {productos_actuales} productos")
            
            # Verificar si alcanzamos el total
            if total_esperado and productos_actuales >= total_esperado:
                print(f"¡Alcanzado el total esperado! {productos_actuales}/{total_esperado}")
                break
            
            # Verificar progreso
            if productos_actuales > productos_anteriores:
                diferencia = productos_actuales - productos_anteriores
                print(f"+{diferencia} productos nuevos")
                intentos_sin_cambios = 0
                productos_anteriores = productos_actuales
            else:
                intentos_sin_cambios += 1
                print(f"Sin cambios. Intento {intentos_sin_cambios}/{max_intentos_sin_cambios}")
                
                if intentos_sin_cambios >= max_intentos_sin_cambios:
                    print("Máximo de intentos sin cambios alcanzado")
                    break
                
                # Scroll intermedio para forzar carga
                if intentos_sin_cambios % 2 == 0:
                    driver.execute_script("window.scrollBy(0, -500);")
                    time.sleep(1)
                    driver.execute_script("window.scrollBy(0, 500);")
        
        except Exception as e:
            print(f"Error en scroll: {e}")
            break
            
        time.sleep(2)
    
    productos_final = 0
    for selector in selectores_productos:
        try:
            productos = driver.find_elements(By.XPATH, selector)
            if len(productos) > productos_final:
                productos_final = len(productos)
        except:
            continue
    
    tiempo_total = time.time() - start_time
    print(f"Scroll terminado: {productos_final} productos en {tiempo_total:.1f}s")
    
    return productos_final

def extraer_categoria_completa(driver, url, hashes_procesados, categoria):
    """Extrae todos los productos de una categoría usando scroll infinito."""
    new_rows = []
    new_hashes = []
    fecha_extraccion = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
    fecha_solo = datetime.now().strftime('%d-%m-%Y')
    
    intentos = 0
    max_intentos = 3
    
    while intentos < max_intentos:
        try:
            print(f"Cargando URL: {url}")
            driver.get(url)
            
            # Esperar a que la página cargue completamente
            time.sleep(5)
            
            # Verificar que estamos en la página correcta
            if "plazalama" not in driver.current_url:
                raise Exception("No se cargó la página correctamente")
            
            # Esperar a que aparezcan productos
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'card') or contains(@class, 'product')]"))
            )
            
            initial_products = driver.find_elements(By.XPATH, "//div[contains(@class, 'card') or contains(@class, 'product')]")
            if len(initial_products) > 0:
                print(f"Página cargada. Productos iniciales: {len(initial_products)}")
                break
            else:
                raise Exception("No se detectaron productos iniciales")
            
        except Exception as e:
            intentos += 1
            print(f"Error al cargar página ({e}). Intento {intentos}/{max_intentos}.")
            if intentos < max_intentos:
                time.sleep(10)
            else:
                print(f"No se pudo cargar la página después de {max_intentos} intentos")
                return [], []

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
    