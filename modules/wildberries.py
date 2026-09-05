import json
import re
import logging
from typing import Dict, Optional
from bs4 import BeautifulSoup
import aiohttp

logger = logging.getLogger(__name__)

class WildberriesParser:
    """Парсер карточек Wildberries"""
    
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
            
            # Используем другой API-эндпоинт Wildberries
            # Этот эндпоинт менее защищён и работает без токена
            api_url = f"https://card.wb.ru/cards/v2/detail?appType=1&curr=rub&dest=-1257786&spp=30&nm={product_id}"
            
            # Расширенные заголовки (имитируем браузер)
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
            
            async with self.session.get(api_url, headers=headers, timeout=self.timeout) as response:
                if response.status != 200:
                    return {'error': f'Не удалось получить данные через API (статус: {response.status})'}
                
                data = await response.json()
                
                products = data.get('data', {}).get('products', [])
                if not products:
                    return {'error': 'Товар не найден'}
                
                product = products[0]
                
                # Получаем описание
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
                
                # Отзывы (через другой API)
                reviews_count = 0
                try:
                    reviews_url = f"https://feedbacks.wb.ru/api/v1/feedbacks/summary?nmId={product_id}"
                    async with self.session.get(reviews_url, headers=headers, timeout=self.timeout) as rev_response:
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
                
        except aiohttp.ClientError as e:
            logger.error(f"Ошибка сети при парсинге Wildberries: {e}")
            return {'error': f'Ошибка сети: {str(e)}'}
        except Exception as e:
            logger.error(f"Ошибка при парсинге Wildberries: {e}")
            return {'error': f'Ошибка парсинга: {str(e)}'}
