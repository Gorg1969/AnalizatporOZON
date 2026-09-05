import json
import re
import logging
from typing import Dict, Optional
import aiohttp
import asyncio

logger = logging.getLogger(__name__)

class WildberriesParser:
    """Парсер карточек Wildberries через публичное API"""
    
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
            
            # === ИСПОЛЬЗУЕМ ПУБЛИЧНОЕ API (без токена) ===
            # Пробуем несколько эндпоинтов
            
            # 1. Прямой запрос к публичному API Wildberries
            api_urls = [
                f"https://public-api.wildberries.ru/api/v1/product/{product_id}",
                f"https://content-api.wildberries.ru/v1/product/{product_id}",
                f"https://wbx.ru/api/v1/product/{product_id}",
            ]
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json',
                'Accept-Language': 'ru-RU,ru;q=0.9',
            }
            
            data = None
            for api_url in api_urls:
                try:
                    async with self.session.get(api_url, headers=headers, timeout=self.timeout) as response:
                        if response.status == 200:
                            data = await response.json()
                            logger.info(f"Успешный ответ от {api_url}")
                            break
                        else:
                            logger.warning(f"API {api_url} вернул статус {response.status}")
                except Exception as e:
                    logger.warning(f"Ошибка при запросе к {api_url}: {e}")
                    continue
            
            if not data:
                # Если API не работают, пробуем парсить через веб
                return await self._parse_via_web(url, product_id)
            
            # Извлекаем данные из ответа
            return await self._extract_product_data(data, product_id)
                    
        except aiohttp.ClientError as e:
            logger.error(f"Ошибка сети: {e}")
            return {'error': f'Ошибка сети: {str(e)}'}
        except Exception as e:
            logger.error(f"Ошибка: {e}")
            return {'error': f'Ошибка парсинга: {str(e)}'}
    
    async def _extract_product_data(self, data: Dict, product_id: str) -> Dict:
        """Извлекает данные из API-ответа"""
        try:
            # Пробуем разные структуры ответа
            product = data.get('data', {})
            if not product:
                product = data
            
            name = product.get('name', '')
            brand = product.get('brand', '') or product.get('vendor', '')
            price = product.get('price', product.get('priceU', 0))
            
            # Цена может быть в копейках
            if price and isinstance(price, (int, float)) and price > 1000:
                price = price / 100
            
            # Описание
            description = product.get('description', '')
            if not description:
                description = product.get('text', '')
            
            # Характеристики
            characteristics = product.get('characteristics', {})
            if not characteristics:
                characteristics = product.get('params', {})
                if isinstance(characteristics, list):
                    chars_dict = {}
                    for item in characteristics:
                        name_char = item.get('name', '')
                        value_char = item.get('value', '')
                        if name_char and value_char:
                            chars_dict[name_char] = value_char
                    characteristics = chars_dict
            
            # Рейтинг и отзывы
            rating = product.get('rating', 0)
            reviews_count = product.get('reviewsCount', 0)
            
            if rating > 10:
                rating = rating / 10
            
            return {
                'name': name or 'Название не указано',
                'brand': brand or 'Не указан',
                'price': price if price else None,
                'rating': rating if rating > 0 else 0,
                'reviews_count': reviews_count if reviews_count > 0 else 0,
                'description': description[:5000] if description else '',
                'characteristics': characteristics,
                'platform': 'wildberries'
            }
        except Exception as e:
            logger.error(f"Ошибка извлечения данных: {e}")
            return {'error': f'Ошибка извлечения данных: {str(e)}'}
    
    async def _parse_via_web(self, url: str, product_id: str) -> Dict:
        """Запасной способ: парсинг через веб-страницу"""
        try:
            # Используем другой подход — запрос к мобильной версии
            mobile_url = f"https://m.wildberries.ru/product/{product_id}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'ru-RU,ru;q=0.9',
            }
            
            async with self.session.get(mobile_url, headers=headers, timeout=self.timeout) as response:
                if response.status != 200:
                    return {'error': f'Не удалось загрузить страницу (статус: {response.status})'}
                
                html = await response.text()
                
                # Пытаемся найти данные в JSON внутри HTML
                import re
                json_pattern = r'<script type="application/ld\+json">(.*?)</script>'
                matches = re.findall(json_pattern, html, re.DOTALL)
                
                for match in matches:
                    try:
                        data = json.loads(match)
                        if data.get('@type') == 'Product':
                            return {
                                'name': data.get('name', 'Название не указано'),
                                'brand': data.get('brand', {}).get('name', 'Не указан') if isinstance(data.get('brand'), dict) else 'Не указан',
                                'price': data.get('offers', {}).get('price', None),
                                'rating': 0,
                                'reviews_count': 0,
                                'description': data.get('description', '')[:5000],
                                'characteristics': {},
                                'platform': 'wildberries'
                            }
                    except:
                        pass
                
                return {'error': 'Не удалось извлечь данные с мобильной версии'}
                
        except Exception as e:
            return {'error': f'Ошибка веб-парсинга: {str(e)}'}
