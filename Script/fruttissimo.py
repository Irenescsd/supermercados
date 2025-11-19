#Fruttissimo
import requests
import pandas as pd
from bs4 import BeautifulSoup
import time
import random
import os
import csv
from datetime import datetime
from urllib.parse import urljoin, urlparse
import logging
from fake_useragent import UserAgent
import json

class FruttissimoScraper:
    def __init__(self):
        self.base_url = "https://fruttissimo.com.do/tienda/"
        self.output_file = "D:/Supermercados/BD/fruttissimo.csv"
        self.progress_file = "D:/Supermercados/estado_progreso/scraping_progress.json"
        self.session = requests.Session()
        self.setup_logging()
        self.setup_user_agents()
        self.load_progress()
        
    def setup_logging(self):
        """Configurar sistema de logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('D:/Supermercados/estado_progreso/scraping.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_user_agents(self):
        """Configurar rotación de User-Agents"""
        self.ua = UserAgent()
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15'
        ]
    
    def get_random_headers(self):
        """Generar headers aleatorios para cada request"""
        return {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Referer': self.base_url,
            'DNT': '1'
        }
    
    def load_progress(self):
        """Cargar progreso de scraping anterior"""
        self.progress = {
            'last_page': 1,
            'scraped_pages': [],
            'last_run': None
        }
        
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r') as f:
                    self.progress = json.load(f)
                self.logger.info(f"Progreso cargado: Página {self.progress['last_page']}")
            except Exception as e:
                self.logger.error(f"Error cargando progreso: {e}")
    
    def save_progress(self, page_number):
        """Guardar progreso actual"""
        self.progress['last_page'] = page_number
        self.progress['last_run'] = datetime.now().isoformat()
        
        if page_number not in self.progress['scraped_pages']:
            self.progress['scraped_pages'].append(page_number)
        
        try:
            with open(self.progress_file, 'w') as f:
                json.dump(self.progress, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error guardando progreso: {e}")
    
    def make_request(self, url, max_retries=3):
        """Realizar request con manejo de errores"""
        for attempt in range(max_retries):
            try:
                headers = self.get_random_headers()
                response = self.session.get(
                    url, 
                    headers=headers, 
                    timeout=30,
                    allow_redirects=True
                )
                
                if response.status_code == 200:
                    return response
                elif response.status_code == 403:
                    self.logger.warning("Acceso denegado (403). Esperando...")
                    time.sleep(random.uniform(10, 20))
                else:
                    self.logger.warning(f"Status code {response.status_code}. Reintentando...")
                
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Error en request (intento {attempt + 1}): {e}")
            
            # Espera exponencial con jitter
            #wait_time = (2 ** attempt) + random.uniform(0, 1)
            #time.sleep(wait_time)
            time.sleep(random.uniform(3, 7))
        return None
    
    def extract_product_data(self, product_card):
        """Extraer datos de un producto individual"""
        try:
            # Nombre del producto
            name_element = product_card.find('h2', class_='product-title')
            name = name_element.get_text(strip=True) if name_element else "No disponible"
            
            # Precio
            price_element = product_card.find('span', class_='price')
            price = "No disponible"
            
            
            if price_element:
                # Buscar precio regular o en oferta
                bdi = price_element.find('bdi')
                ins = price_element.find('ins')
                
                if ins:
                    price = ins.get_text(strip=True)
                elif bdi:
                    price = bdi.get_text(strip=True)
                else:
                    price = price_element.get_text(strip=True)
            
            # Limpiar precio
            if price != "No disponible":
                price = price.replace('RD$', '').replace(',', '').strip()
            
            return {
                'Supermercado': 'Fruttissimo Market',
                'Fecha_extraccion': datetime.now().strftime('%d-%m-%Y %H:%M:%S'),
                'Categoria': self.current_category,
                'Articulo': name,
                'Precio': price
            }
            
        except Exception as e:
            self.logger.error(f"Error extrayendo datos del producto: {e}")
            return None
    
    def scrape_page(self, page_url):
        """Scrapear una página individual"""
        #self.logger.info(f"Scrapeando página: {page_url}")
        
        response = self.make_request(page_url)
        if not response:
            return None, False
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Encontrar productos
        product_cards = soup.find_all('div', class_='product-inner')
        products_data = []
        
        for card in product_cards:
            product_data = self.extract_product_data(card)
            if product_data:
                products_data.append(product_data)
        
        # Verificar si hay más páginas
        next_page = soup.find('a', class_='next page-numbers')
        has_next = next_page is not None
        
        return products_data, has_next
    
    def get_category_name(self, url):
        """Obtener nombre de categoría desde la URL"""
        parsed_url = urlparse(url)
        path_parts = parsed_url.path.split('/')
        
        # Buscar parte significativa de la URL para la categoría
        for part in reversed(path_parts):
            if part and part not in ['tienda', 'product-category', 'page']:
                return part.replace('-', ' ').title()
        
        return "General"
    
    def scrape_category(self, category_url):
        """Scrapear una categoría completa"""
        self.current_category = self.get_category_name(category_url)
        #self.logger.info(f"Iniciando scraping de categoría: {self.current_category}")
        
        page_number = self.progress['last_page']
        all_products = []
        
        while True:
            page_url = f"{category_url}page/{page_number}/" if page_number > 1 else category_url
            
            products, has_next = self.scrape_page(page_url)
            
            if products:
                all_products.extend(products)
                
                # Guardar datos incrementalmente
                self.save_to_csv(products)
                self.logger.info(f"Página {page_number}: {len(products)} productos encontrados")
            
            # Guardar progreso después de cada página
            self.save_progress(page_number)
            
            if not has_next:
                break
            
            page_number += 1
            
            # Delay aleatorio entre páginas
            time.sleep(random.uniform(2, 5))
        
        return all_products
    
    def save_to_csv(self, data):
        """Guardar datos en CSV de forma incremental"""
        file_exists = os.path.exists(self.output_file)
        
        with open(self.output_file, 'a', newline='', encoding='utf-8') as f:
            fieldnames = ['Supermercado', 'Fecha_extraccion', 'Categoria', 'Articulo', 'Precio']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            if not file_exists:
                writer.writeheader()
            
            for row in data:
                writer.writerow(row)
                # Mostrar datos en tiempo real
                print(f"Guardado: {row['Articulo']} - {row['Precio']}")
    
    def get_category_urls(self):
        """Obtener URLs de todas las categorías"""
        response = self.make_request(self.base_url)
        if not response:
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Buscar enlaces de categorías
        category_links = []
        nav_menu = soup.find('nav', class_='woocommerce-breadcrumb')
        if nav_menu:
            category_links = nav_menu.find_all('a', href=True)
        
        # Si no encuentra en el breadcrumb, buscar en otros lugares
        if not category_links:
            category_menu = soup.find('ul', class_='product-categories')
            if category_menu:
                category_links = category_menu.find_all('a', href=True)
        
        # Filtrar y normalizar URLs
        unique_urls = set()
        for link in category_links:
            href = link['href']
            if '/product-category/' in href:
                unique_urls.add(href)
        
        return list(unique_urls)
    
    def run(self):
        """Ejecutar el scraping completo"""
        self.logger.info("Iniciando scraping de Fruttissimo Market")
        
        try:
            # Obtener categorías
            category_urls = self.get_category_urls()
            if not category_urls:
                category_urls = [self.base_url]  # Fallback a página principal
            
            self.logger.info(f"Encontradas {len(category_urls)} categorías")
            
            all_products = []
            
            for category_url in category_urls:
                # Resetear progreso de página para nueva categoría
                self.progress['last_page'] = 1
                
                category_products = self.scrape_category(category_url)
                all_products.extend(category_products)
                
                # Delay entre categorías
                time.sleep(random.uniform(3, 7))
            
            self.logger.info(f"Scraping completado. Total: {len(all_products)} productos")
            
        except KeyboardInterrupt:
            self.logger.info("Scraping interrumpido por el usuario")
        except Exception as e:
            self.logger.error(f"Error durante el scraping: {e}")
        finally:
            # Limpiar archivo de progreso al finalizar
            if os.path.exists(self.progress_file):
                os.remove(self.progress_file)

def fruttissimo():
    """Función principal"""
    scraper = FruttissimoScraper()
    
    try:
        scraper.run()
    except Exception as e:
        scraper.logger.error(f"Error fatal: {e}")
    finally:
        scraper.logger.info("Scraping finalizado")

if __name__ == "__main__":
    fruttissimo()