import os
import re
import json
import time
import random
from datetime import datetime

import requests
import pandas as pd
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

API_URL = "https://www.pricesmart.com/api/br_discovery/getProductsByKeyword"
HISTORICO_FILE = "D:/Supermercados/BD/PriceSmart.csv"
PROGRESO_FILE = "D:/Supermercados/estado_progreso/PriceSmart.json"

# Rotación simple de User-Agents (añade más si quieres)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
]

# ---- CATEGORÍAS (las que compartiste) ----
CATEGORIAS = {
    "Alimentos": {"url": "https://www.pricesmart.com/es-do/categoria/Alimentos-G10D03/G10D03", "max_paginas": 86},
    "Productos de temporada": {"url": "https://www.pricesmart.com/es-do/categoria/Productos-de-temporada-S10D45/S10D45", "max_paginas": 6},
    "Hogar": {"url": "https://www.pricesmart.com/es-do/categoria/Hogar-H30D22/H30D22", "max_paginas": 30},
    "Salud y belleza": {"url": "https://www.pricesmart.com/es-do/categoria/Salud-y-belleza-H20D09/H20D09", "max_paginas": 12},
    "Licor, cerveza y vino": {"url": "https://www.pricesmart.com/es-do/categoria/Licor-cerveza-y-vino-G10D08014/G10D08014", "max_paginas": 9},
    "Mascotas": {"url": "https://www.pricesmart.com/es-do/categoria/Mascotas-P10D51/P10D51", "max_paginas": 3},
    "Ferretería y mejoras al hogar": {"url": "https://www.pricesmart.com/es-do/categoria/Ferreteria-y-mejoras-al-hogar-H10D21/H10D21", "max_paginas": 6},
    "Deportes y fitness": {"url": "https://www.pricesmart.com/es-do/categoria/Deportes-y-fitness-S30D26/S30D26", "max_paginas": 3},
    "Bebés": {"url": "https://www.pricesmart.com/es-do/categoria/Bebe-B10D27/B10D27", "max_paginas": 4},
    "Exteriores": {"url": "https://www.pricesmart.com/es-do/categoria/Exteriores-O20D30/O20D30", "max_paginas": 7},
    "Electrónicos": {"url": "https://www.pricesmart.com/es-do/categoria/Electronicos-E10D24/E10D24", "max_paginas": 9},
    "Electrodomésticos": {"url": "https://www.pricesmart.com/es-do/categoria/Electrodomesticos-S20D23/S20D23", "max_paginas": 6},
    "Computadoras, tablets y accesorios": {"url": "https://www.pricesmart.com/es-do/categoria/Computadoras-tablets-y-accesorios-C10D29/C10D29", "max_paginas": 5},
    "Línea blanca": {"url": "https://www.pricesmart.com/es-do/categoria/Linea-blanca-M10D43/M10D43", "max_paginas": 4},
    "Moda y accesorios": {"url": "https://www.pricesmart.com/es-do/categoria/Moda-y-accesorios-F10D40/F10D40", "max_paginas": 16},
    "Muebles": {"url": "https://www.pricesmart.com/es-do/categoria/Muebles-F20D27/F20D27", "max_paginas": 5},
    "Oficina": {"url": "https://www.pricesmart.com/es-do/categoria/Oficina-O10D25/O10D25", "max_paginas": 2},
    "Suministros para restaurantes": {"url": "https://www.pricesmart.com/es-do/categoria/Suministros-para-restaurantes-R10D22/R10D22", "max_paginas": 3},
    "Automotriz": {"url": "https://www.pricesmart.com/es-do/categoria/Automotriz-A10D20/A10D20", "max_paginas": 10},
    "Juguetes y juegos": {"url": "https://www.pricesmart.com/es-do/categoria/Juguetes-y-juegos-T10D46/T10D46", "max_paginas": 3},
    "Equipaje": {"url": "https://www.pricesmart.com/es-do/categoria/Equipaje-L10D22/L10D22", "max_paginas": 2},
    "Óptica": {"url": "https://www.pricesmart.com/es-do/categoria/Optica-U10D72/U10D72", "max_paginas": 7},
    "Audiología": {"url": "https://www.pricesmart.com/es-do/categoria/Audiologia-U11D13/U11D13", "max_paginas": 1}
}

# ----------------- Utilidades -----------------
def user_headers():
    return {
        "accept": "application/json, text/plain, */*",
        "content-type": "application/json",
        "origin": "https://www.pricesmart.com",
        "referer": "https://www.pricesmart.com/es-do/",
        "user-agent": random.choice(USER_AGENTS),
    }

def build_session():
    """
    Session con reintentos a nivel HTTP (5xx, timeouts, etc.).
    """
    sess = requests.Session()
    retries = Retry(
        total=3,                # reintentos por request
        backoff_factor=1.5,     # backoff exponencial
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["POST", "GET"]
    )
    adapter = HTTPAdapter(max_retries=retries, pool_connections=10, pool_maxsize=10)
    sess.mount("https://", adapter)
    sess.mount("http://", adapter)
    return sess

def extraer_codigo_q(url: str) -> str:
    """
    Toma el último segmento de la URL (p.ej. .../G10D03) como 'q'.
    """
    last = url.rstrip("/").split("/")[-1]
    return last

def build_payload(url: str, start: int) -> dict:
    q = extraer_codigo_q(url)
    return {
        "account_id": "7024",
        "auth_key": "ev7libhybjg5h1d1",
        "domain_key": "pricesmart_bloomreach_io_es",
        "fl": "pid,title,currency,price_DO,fractionDigits",
        "fq": [],
        "q": q,
        "ref_url": "https://www.pricesmart.com/es-do/categorias",
        "rows": 12,
        "search_type": "category",
        "start": start,
        "url": url,
        "view_id": "DO",
    }
def leer_progreso() -> dict:
    if os.path.isfile(PROGRESO_FILE):
        try:
            with open(PROGRESO_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def guardar_progreso(progreso: dict):
    tmp = PROGRESO_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(progreso, f, ensure_ascii=False, indent=2)
    os.replace(tmp, PROGRESO_FILE)

def normalizar_precio(p):
    
    price_do = p.get("price_DO")
    fd = p.get("fractionDigits", 2)
    if isinstance(price_do, (int, float)) and isinstance(fd, int) and fd >= 0:
        return float(price_do) / (10 ** fd)
    return None

def limpiar_productos(raw_products, categoria):
    Fecha_extraccion= datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    out = []
    for p in raw_products:
        out.append({
            "Supermercado": "PriceSmart",
            "Fecha_extraccion": Fecha_extraccion,
            "Categoria": categoria,
            "Articulo": p.get("title"),
            "Precio": normalizar_precio(p),
            #"Moneda": p.get("currency"),
        })
    return out
def guardar_csv_incremental(filas: list):
    if not filas:
        return
    df = pd.DataFrame(filas, columns=["Supermercado", "Fecha_extraccion", "Categoria", "Articulo", "Precio", "Moneda"])
    # Si no existe, escribe con header; si existe, agrega sin header
    if not os.path.isfile(HISTORICO_FILE):
        df.to_csv(HISTORICO_FILE, index=False, encoding="utf-8-sig")
    else:
        df.to_csv(HISTORICO_FILE, mode="a", index=False, header=False, encoding="utf-8-sig")

def sleep_suave(pagina):
    # Pausas aleatorias para ser menos ruidoso
    time.sleep(random.uniform(1.2, 3.2))
    # Cada cierto número de páginas, pausa más larga
    if pagina % 10 == 0:
        time.sleep(random.uniform(6, 12))

def parse_docs(data: dict):
    """
    La API a veces cambia el envoltorio. Buscamos 'docs' en rutas probables.
    """
    if not isinstance(data, dict):
        return []
    # Ruta habitual
    docs = data.get("response", {}).get("docs")
    if docs: 
        return docs
    # Otras variantes defensivas
    if "products" in data and isinstance(data["products"], dict):
        if "docs" in data["products"]:
            return data["products"]["docs"]
    if "docs" in data:
        return data["docs"]
    return []
# ----------------- Main -----------------
def pricesmart():
    progreso = leer_progreso()
    ses = build_session()

    total_insertadas = 0

    for categoria, meta in CATEGORIAS.items():
        url = meta["url"]
        q_code = extraer_codigo_q(url)
        max_paginas = int(meta.get("max_paginas", 1))

        # Reanudar desde progreso
        pagina_inicio = int(progreso.get(categoria, 1))
        if pagina_inicio > 1:
            print(f"Reanudando '{categoria}' desde página {pagina_inicio}/{max_paginas}")
        else:
            print(f"Procesando categoría: {categoria} ({q_code}) | páginas: 1..{max_paginas}")

        for pagina in range(pagina_inicio, max_paginas + 1):
            start = (pagina - 1) * 12
            payload = build_payload(url, start)

            try:
                r = ses.post(API_URL, json=payload, headers=user_headers(), timeout=20)
            except requests.RequestException as ex:
                print(f"[{categoria}] Error de red en página {pagina}: {ex}")
                # Guardar progreso antes de pausar
                progreso[categoria] = pagina
                guardar_progreso(progreso)
                time.sleep(random.uniform(8, 15))
                continue

            if r.status_code != 200:
                print(f"[{categoria}] HTTP {r.status_code} en página {pagina}")
                # Guardar progreso y continuar (backoff suave)
                progreso[categoria] = pagina
                guardar_progreso(progreso)
                time.sleep(random.uniform(5, 10))
                continue
            try:
                data = r.json()
            except ValueError:
                print(f"[{categoria}] Respuesta no-JSON en página {pagina}")
                progreso[categoria] = pagina
                guardar_progreso(progreso)
                time.sleep(random.uniform(5, 10))
                continue

            docs = parse_docs(data)
            print(f"{categoria} | Página {pagina}/{max_paginas}: {len(docs)} productos")

            if not docs:
                # Si no hay docs, asumimos final prematuro de la categoría
                progreso[categoria] = pagina + 1
                guardar_progreso(progreso)
                sleep_suave(pagina)
                continue

            filas = limpiar_productos(docs, categoria)
            guardar_csv_incremental(filas)
            total_insertadas += len(filas)

            # Actualizamos progreso después de guardar
            progreso[categoria] = pagina + 1
            guardar_progreso(progreso)

            sleep_suave(pagina)

        print(f"Categoría finalizada: {categoria}")

    print(f"Terminado. Filas nuevas insertadas: {total_insertadas}")
    print(f"CSV histórico: {HISTORICO_FILE}")
    print(f"Progreso guardado en: {PROGRESO_FILE} (para reanudar si algo falla)")

if __name__ == "__main__":
    pricesmart()