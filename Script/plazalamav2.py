# plazalama_scraper_2025_CORREGIDO.py
# Funciona al 100% - Noviembre 2025

import os
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import random
from datetime import datetime
import json
import re
import hashlib

# ===== Rutas de archivos =====
ARCHIVO_SALIDA = "D:/Supermercados/BD/PlazaLama.csv"
ARCHIVO_ESTADO = "D:/Supermercados/estado_progreso/estado_Plaza_Lama.json"

# ===== User Agents =====
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
]

# ===== Categorías actualizadas =====
CATEGORIAS = {
    "Bebes y primera infancia": {"url": "https://plazalama.com.do/ca/supermercado/bebes-y-primera-infancia/11/11-40"},
    "Bebidas": {"url": "https://plazalama.com.do/ca/supermercado/bebidas/11/11-41"},
    "Belleza y Bienestar": {"url": "https://plazalama.com.do/ca/supermercado/belleza-y-bienestar/11/11-42"},
    "Carnes, Pescados y Mariscos": {"url": "https://plazalama.com.do/ca/supermercado/carnes-pescados-y-mariscos/11/11-43"},
    "Congelados": {"url": "https://plazalama.com.do/ca/supermercado/congelados/11/11-44"},
    "Cuidado del Hogar": {"url": "https://plazalama.com.do/ca/supermercado/cuidado-del-hogar/11/11-45"},
    "Despensa": {"url": "https://plazalama.com.do/ca/supermercado/despensa/11/11-46"},
    "Farmacia": {"url": "https://plazalama.com.do/ca/supermercado/farmacia/11/11-47"},
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

# ===== Funciones de estado =====
def cargar_estado():
    try:
        if os.path.exists(ARCHIVO_ESTADO):
            with open(ARCHIVO_ESTADO, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}
    except:
        return {}

def guardar_estado(progreso):
    os.makedirs(os.path.dirname(ARCHIVO_ESTADO), exist_ok=True)
    with open(ARCHIVO_ESTADO, "w", encoding="utf-8") as f:
        json.dump(progreso, f, ensure_ascii=False, indent=2)

def obtener_progreso_categoria(progreso, nombre_cat):
    fecha_hoy = datetime.now().strftime('%d-%m-%Y')
    if nombre_cat not in progreso or progreso[nombre_cat].get('fecha_ultima_ejecucion') != fecha_hoy:
        progreso[nombre_cat] = {
            'fecha_ultima_ejecucion': fecha_hoy,
            'completada': False,
            'hashes_procesados': [],
            'productos_totales': 0
        }
    return progreso[nombre_cat]

# ===== Configuración driver =====
def configurar_driver():
    options = Options()
    options.add_argument(f"user-agent={random.choice(USER_AGENTS)}")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    # options.add_argument("--headless")  # QUITAR headless mientras pruebas
    # === Quitar el 99% del ruido de Chrome ===
    options.add_argument("--disable-features=PushMessaging")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-background-networking")
    options.add_argument("--disable-sync")
    options.add_argument("--disable-translate")
    options.add_argument("--disable-logging")
    options.add_argument("--disable-web-security")  # opcional
    options.add_argument("--log-level=3")  # solo errores graves
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    options.add_argument("--disable-gpu")  # quita el error de WebGL
    
    service = Service()
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

# ===== Limpieza y hash =====
def limpiar_precio(texto):
    if not texto: return None
    texto = re.sub(r'[^0-9.,]', '', texto.replace(',', ''))
    try:
        return float(texto)
    except:
        return None

def limpiar_nombre(texto):
    if not texto: return "Nombre no disponible"
    return re.sub(r'\s+', ' ', texto.strip()).replace('...', '')

def crear_hash_producto(nombre, fecha_solo):
    nombre_norm = re.sub(r'\s+', ' ', nombre.lower().strip())
    return hashlib.md5(f"plazalama_{nombre_norm}_{fecha_solo}".encode()).hexdigest()

# ===== Extracción de productos visibles =====
def extraer_datos_visibles(driver, hashes_existentes_set, fecha_solo, fecha_extraccion, categoria):
    nuevos_datos = []
    nuevos_hashes = []

    selectores_productos = [
        "//div[contains(@class, 'product-card') or contains(@class, 'ProductCard')]",
        "//div[contains(@class, 'styles__Card') or contains(@class, 'StyledCard')]",
        "//article[contains(@class, 'product')]",
        "//div[@data-testid='product-card']"
    ]

    productos = []
    for sel in selectores_productos:
        try:
            elems = driver.find_elements(By.XPATH, sel)
            if elems:
                productos = elems
                break
        except:
            continue

    for prod in productos:
        try:
            # Nombre
            nombre = "Nombre no disponible"
            for s in [".//h3", ".//h2", ".//p[contains(@class,'title') or contains(@class,'name')]", ".//a[contains(@class,'product-name')]"]:
                try:
                    nombre = limpiar_nombre(prod.find_element(By.XPATH, s).text)
                    if nombre and nombre != "Nombre no disponible":
                        break
                except:
                    continue

            # Precio
            precio = None
            for s in [".//span[contains(@class,'price')]", ".//p[contains(@class,'price')]", ".//div[contains(text(),'RD$')]"]:
                try:
                    precio_texto = prod.find_element(By.XPATH, s).text
                    precio = limpiar_precio(precio_texto)
                    if precio:
                        break
                except:
                    continue

            if nombre != "Nombre no disponible" and precio:
                hash_val = crear_hash_producto(nombre, fecha_solo)
                if hash_val not in hashes_existentes_set:
                    nuevos_datos.append({
                        "Supermercado": "PlazaLama",
                        "Fecha_extraccion": fecha_extraccion,
                        "Categoria": categoria,
                        "Articulo": nombre,
                        "Precio": precio
                    })
                    nuevos_hashes.append(hash_val)
                    hashes_existentes_set.add(hash_val)

        except:
            continue

    return nuevos_datos, nuevos_hashes

# ===== FUNCIÓN PRINCIPAL CORREGIDA (click en "Ver más" + fallback scroll) =====
def extraer_categoria_completa(driver, url, hashes_previos, categoria):
    filas = []
    set_hashes = set(hashes_previos)
    fecha_extraccion = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
    fecha_solo = datetime.now().strftime('%d-%m-%Y')

    print(f"\n>>> Iniciando categoría: {categoria}")
    driver.get(url)
    time.sleep(random.uniform(2.5,4.5))

    sin_nuevos = 0
    max_sin_nuevos = 7

    while True:
        datos, hashes_nuevos = extraer_datos_visibles(driver, set_hashes, fecha_solo, fecha_extraccion, categoria)
        if datos:
            print(f"   + {len(datos)} productos nuevos")
            filas.extend(datos)
            sin_nuevos = 0
        else:
            sin_nuevos += 1

        # === INTENTAR CARGAR MÁS PRODUCTOS ===
        cargado = False

        # Botón "Ver más productos" (todos los selectores posibles 2025)
        botones = [
            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'ver más')]",
            "//button//span[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'ver más')]",
            "//button[contains(@class, 'load-more') or contains(@class, 'LoadMore')]",
            "//button[contains(text(), 'Cargar más')]"
        ]

        for btn_xpath in botones:
            try:
                boton = WebDriverWait(driver, 8).until(EC.element_to_be_clickable((By.XPATH, btn_xpath)))
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", boton)
                time.sleep(1)
                boton.click()
                print("   → Click en 'Ver más productos'")
                time.sleep(random.uniform(2.5, 5.5))
                cargado = True
                sin_nuevos = 0
                break
            except:
                continue

        # Si no hay botón → fallback scroll (algunas categorías aún lo usan)
        if not cargado:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(3.5, 5.50))

        if sin_nuevos >= max_sin_nuevos:
            print(f"   Fin de categoría → Total extraídos: {len(filas)} productos")
            break

    nuevos_hashes_lista = [h for h in set_hashes if h not in hashes_previos]
    return filas, nuevos_hashes_lista

# ===== Guardar en CSV =====
def anadir_a_csv(datos, ruta):
    if not datos:
        return
    df = pd.DataFrame(datos)
    header = not os.path.exists(ruta)
    df.to_csv(ruta, mode='a', header=header, index=False, encoding='utf-8-sig')
    print(f"   Guardados {len(datos)} registros en CSV\n")

# ===== MAIN =====
def plazalama():
    print("=== PLAZA LAMA SCRAPER 2025 - INICIANDO ===")
    progreso = cargar_estado()
    driver = configurar_driver()

    try:
        for idx, (cat, info) in enumerate(CATEGORIAS.items()):
            print(f"\n{'='*70}")
            print(f"CATEGORÍA {idx+1}/{len(CATEGORIAS)}: {cat}")
            print(f"{'='*70}")

            prog_cat = obtener_progreso_categoria(progreso, cat)
            if prog_cat['completada']:
                print(f"Ya procesada hoy → Saltando")
                continue

            filas, hashes_nuevos = extraer_categoria_completa(driver, info["url"], prog_cat['hashes_procesados'], cat)

            if filas:
                anadir_a_csv(filas, ARCHIVO_SALIDA)
                prog_cat['hashes_procesados'].extend(hashes_nuevos)
                prog_cat['productos_totales'] = len(prog_cat['hashes_procesados'])

            prog_cat['completada'] = True
            guardar_estado(progreso)

            time.sleep(random.uniform(8, 14))  # Ser amable con el servidor

    except Exception as e:
        print(f"ERROR CRÍTICO: {e}")
        guardar_estado(progreso)
    finally:
        driver.quit()
        total = sum(p.get('productos_totales', 0) for p in progreso.values())
        print(f"\nFIN DEL SCRAPER → {total} productos únicos extraídos hoy.")

if __name__ == "__main__":
    plazalama()