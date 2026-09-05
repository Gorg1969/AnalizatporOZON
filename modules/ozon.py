import re
import logging
from typing import Dict
from bs4 import BeautifulSoup
import aiohttp

logger = logging.getLogger(__name__)

class OzonParser:
    """Парсер карточек Ozon"""
    
    def __init__(self, session: aiohttp.ClientSession):
        self.session = session
        self.timeout = aiohttp.ClientTimeout(total=30)
    
    async def parse(self, url: str) -> Dict:
        """Парсит карточку товара на Ozon"""
        try:
            # Извлекаем ID товара из URL
            product_id = re.search(r'/product/(\d+)/?', url)
            if not product_id:
                return {'error': 'Неверный формат ссылки Ozon'}
            
            product_id = product_id.group(1)
            logger.info(f"Парсинг Ozon: ID {product_id}")
            
            # Используем API Ozon (публичный)
            api_url = f"https://www.ozon.ru/api/composer-api.bx/page/json/v2?url=/product/{product_id}/"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json'
            }
            
            async with self.session.get(api_url, headers=headers, timeout=self.timeout) as response:
                if response.status != 200:
                    return {'error': f'Не удалось получить данные (статус: {response.status})'}
                
                data = await response.json()
                
                # Извлекаем данные из сложной структуры Ozon
                product_data = self._extract_product_data(data)
                
                if not product_data:
                    return {'error': 'Не удалось извлечь данные о товаре'}
                
                return product_data
                
        except aiohttp.ClientError as e:
            logger.error(f"Ошибка сети при парсинге Ozon: {e}")
            return {'error': f'Ошибка сети: {str(e)}'}
        except Exception as e:
            logger.error(f"Ошибка при парсинге Ozon: {e}")
            return {'error': f'Ошибка парсинга: {str(e)}'}
    
    def _extract_product_data(self, data: Dict) -> Dict:
        """Извлекает данные о товаре из ответа API Ozon"""
        try:
            # Поиск в layout-компонентах
            layout = data.get('layout', [])
            
            name = ''
            description = ''
            price = None
            rating = 0
            reviews_count = 0
            characteristics = {}
            
            for component in layout:
                # Название
                if component.get('component') == 'productHeader':
                    name = component.get('state', {}).get('title', '')
                
                # Описание
                if component.get('component') == 'productDescription':
                    html = component.get('state', {}).get('html', '')
                    if html:
                        soup = BeautifulSoup(html, 'html.parser')
                        description = soup.get_text(strip=True)
                
                # Цена
                if component.get('component') == 'priceBlock':
                    price_data = component.get('state', {}).get('price', {})
                    if price_data:
                        price = price_data.get('price', '').replace('₽', '').replace(' ', '').strip()
                        try:
                            price = float(price)
                        except:
                            price = None
                
                # Характеристики
                if component.get('component') == 'characteristics':
                    items = component.get('state', {}).get('items', [])
                    for item in items:
                        key = item.get('name', '')
                        value = item.get('value', '')
                        if key and value:
                            characteristics[key] = value
                
                # Рейтинг и отзывы
                if component.get('component') == 'productRating':
                    rating_data = component.get('state', {})
                    rating = rating_data.get('rating', 0)
                    reviews_count = rating_data.get('reviewsCount', 0)
            
            return {
                'name': name or 'Название не указано',
                'brand': '',  # Ozon не всегда отдаёт бренд через API
                'price': price,
                'rating': rating,
                'reviews_count': reviews_count,
                'description': description[:5000],
                'characteristics': characteristics,
                'platform': 'ozon'
            }
            
        except Exception as e:
            logger.error(f"Ошибка извлечения данных Ozon: {e}")
            return None
