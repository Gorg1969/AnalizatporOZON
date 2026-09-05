import json
import re
import logging
from typing import Dict, Optional
from bs4 import BeautifulSoup
import aiohttp
import random
import time

logger = logging.getLogger(__name__)

class WildberriesParser:
    """Парсер карточек Wildberries с обходом антибота"""
    
    def __init__(self, session: aiohttp.ClientSession):
        self.session = session
        self.timeout = aiohttp.ClientTimeout(total=30)
    
    async def parse(self, url: str) -> Dict:
        """Парсит карточку товара на Wildberries"""
        try:
            # Извлекаем ID товара из URL
            product_id = re.search(r'catalog/(\d+)/', url)
            if not product_id:
                product_id = re.search(r'/product/(\d+)', url)
            if not product_id:
                return {'error': 'Неверный формат ссылки Wildberries'}
            
            product_id = product_id.group(1)
            logger.info(f"Парсинг Wildberries: ID {product_id}")
            
            # === ПЕРВЫЙ СПОСОБ: API карточек (с правильными заголовками) ===
            api_url = f"https://card.wb.ru/cards/v2/detail?appType=1&curr=rub&dest=-1257786&spp=30&nm={product_id}"
            
            # Полный набор заголовков как у реального браузера
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-site',
                'Referer': 'https://www.wildberries.ru/',
                'Origin': 'https://www.wildberries.ru',
            }
            
            # Добавляем небольшую задержку для имитации человека
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            async with self.session.get(api_url, headers=headers, timeout=self.timeout) as response:
                if response.status == 200:
                    data = await response.json()
                    products = data.get('data', {}).get('products', [])
                    
                    if products:
                        product = products[0]
                        return await self._extract_product_data(product, product_id)
                    else:
                        logger.warning(f"Товар {product_id} не найден через API")
                        # Пробуем второй способ
                        return await self._parse_via_web(url, product_id)
                else:
                    logger.warning(f"API вернул статус {response.status}, пробуем веб-парсинг")
                    return await self._parse_via_web(url, product_id)
                    
        except aiohttp.ClientError as e:
            logger.error(f"Ошибка сети: {e}")
            return {'error': f'Ошибка сети: {str(e)}'}
        except Exception as e:
            logger.error(f"Ошибка: {e}")
            return {'error': f'Ошибка парсинга: {str(e)}'}
    
    async def _extract_product_data(self, product: Dict, product_id: str) -> Dict:
        """Извлекает данные из API-ответа"""
        try:
            # Описание
            description_html = product.get('description', '')
            if description_html:
                soup = BeautifulSoup(description_html, 'html.parser')
                description_text = soup.get_text(strip=True)
            else:
                description_text = ''
            
            # Характеристики
            characteristics = {}
            if 'characteristics' in product:
                for char in product.get('characteristics', []):
                    name = char.get('name', '')
                    value = char.get('value', '')
                    if name and value:
                        characteristics[name] = value
            
            # Отзывы
            reviews_count = 0
            try:
                reviews_headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'application/json',
                    'Referer': 'https://www.wildberries.ru/'
                }
                reviews_url = f"https://feedbacks.wb.ru/api/v1/feedbacks/summary?nmId={product_id}"
                async with self.session.get(reviews_url, headers=reviews_headers, timeout=self.timeout) as rev_response:
                    if rev_response.status == 200:
                        rev_data = await rev_response.json()
                        reviews_count = rev_data.get('data', {}).get('count', 0)
            except:
                pass
            
            return {
                'name': product.get('name', 'Название не указано'),
                'brand': product.get('brand', ''),
                'price': product.get('priceU', 0) / 100 if product.get('priceU') else None,
                'rating': product.get('rating', 0),
                'reviews_count': reviews_count,
                'description': description_text[:5000],
                'characteristics': characteristics,
                'platform': 'wildberries'
            }
        except Exception as e:
            logger.error(f"Ошибка извлечения данных: {e}")
            return {'error': f'Ошибка извлечения данных: {str(e)}'}
    
    async def _parse_via_web(self, url: str, product_id: str) -> Dict:
        """
        Запасной способ: парсинг через веб-страницу
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0',
                'Upgrade-Insecure-Requests': '1'
            }
            
            async with self.session.get(url, headers=headers, timeout=self.timeout) as response:
                if response.status != 200:
                    return {'error': f'Не удалось загрузить страницу (статус: {response.status})'}
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Извлекаем данные из JSON-LD
                name = self._extract_name_from_html(soup)
                brand = self._extract_brand_from_html(soup)
                price = self._extract_price_from_html(soup)
                
                return {
                    'name': name or 'Название не указано',
                    'brand': brand or 'Не указан',
                    'price': price,
                    'rating': 0,
                    'reviews_count': 0,
                    'description': self._extract_description_from_html(soup),
                    'characteristics': self._extract_chars_from_html(soup),
                    'platform': 'wildberries'
                }
        except Exception as e:
            return {'error': f'Ошибка веб-парсинга: {str(e)}'}
    
    def _extract_name_from_html(self, soup: BeautifulSoup) -> str:
        """Извлекает название из HTML"""
        # Пробуем JSON-LD
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)
                if data.get('@type') == 'Product':
                    return data.get('name', '')
            except:
                pass
        
        # Пробуем заголовок
        title = soup.find('h1')
        if title:
            return title.get_text(strip=True)
        
        return ''
    
    def _extract_brand_from_html(self, soup: BeautifulSoup) -> str:
        """Извлекает бренд из HTML"""
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)
                if data.get('@type') == 'Product':
                    brand_data = data.get('brand', {})
                    if isinstance(brand_data, dict):
                        return brand_data.get('name', '')
                    return str(brand_data)
            except:
                pass
        
        # Ищем на странице
        brand_selectors = ['[class*="brand"]', '[class*="Brand"]', '[class*="vendor"]']
        for selector in brand_selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        
        return ''
    
    def _extract_price_from_html(self, soup: BeautifulSoup) -> float:
        """Извлекает цену из HTML"""
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)
                if data.get('@type') == 'Product':
                    offers = data.get('offers', {})
                    price = offers.get('price')
                    if price:
                        return float(price)
            except:
                pass
        
        # Ищем на странице
        price_selectors = ['[class*="price"]', '[class*="Price"]', '[itemprop="price"]']
        for selector in price_selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                # Убираем пробелы и знаки валют
                text = re.sub(r'[^\d]', '', text)
                try:
                    return float(text) / 100 if len(text) > 3 else float(text)
                except:
                    pass
        
        return None
    
    def _extract_description_from_html(self, soup: BeautifulSoup) -> str:
        """Извлекает описание из HTML"""
        desc_selectors = ['[class*="description"]', '[class*="Description"]', '[itemprop="description"]']
        for selector in desc_selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        return ''
    
    def _extract_chars_from_html(self, soup: BeautifulSoup) -> Dict:
        """Извлекает характеристики из HTML"""
        chars = {}
        char_selectors = ['[class*="characteristic"]', '[class*="Characteristic"]', '[class*="params"]']
        
        for selector in char_selectors:
            container = soup.select_one(selector)
            if container:
                items = container.find_all(['li', 'div', 'tr'])
                for item in items:
                    text = item.get_text(strip=True)
                    if ':' in text:
                        key, value = text.split(':', 1)
                        chars[key.strip()] = value.strip()
                    elif '—' in text:
                        key, value = text.split('—', 1)
                        chars[key.strip()] = value.strip()
        
        return chars


# Добавляем импорт asyncio
import asyncio
