import re
import logging
import asyncio
from typing import Dict
from playwright.async_api import async_playwright, Browser, Page

logger = logging.getLogger(__name__)

class WildberriesParser:
    """Парсер карточек Wildberries через Playwright с маскировкой"""
    
    async def parse(self, url: str) -> Dict:
        """Парсит карточку товара используя Playwright"""
        try:
            # Извлекаем ID товара
            product_id = re.search(r'catalog/(\d+)/', url)
            if not product_id:
                product_id = re.search(r'/product/(\d+)', url)
            if not product_id:
                return {'error': 'Неверный формат ссылки Wildberries'}
            
            product_id = product_id.group(1)
            logger.info(f"Парсинг Wildberries через Playwright: ID {product_id}")
            
            async with async_playwright() as p:
                # Запускаем браузер с маскировкой
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-dev-shm-usage',
                        '--no-sandbox',
                        '--disable-setuid-sandbox'
                    ]
                )
                
                # Создаем контекст с реалистичными настройками
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    locale='ru-RU',
                    timezone_id='Europe/Moscow',
                    extra_http_headers={
                        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7'
                    }
                )
                
                # Создаем страницу
                page = await context.new_page()
                
                # Применяем маскировку (stealth-режим)
                await self._apply_stealth(page)
                
                # Переходим на страницу товара
                await page.goto(url, wait_until='networkidle', timeout=30000)
                
                # Имитация человеческого поведения
                await page.mouse.move(100, 100)
                await asyncio.sleep(1.5)
                await page.mouse.move(200, 200)
                await asyncio.sleep(0.5)
                
                # Ждем загрузки основных элементов
                await page.wait_for_selector('[class*="product"], [class*="Product"], .product-page', timeout=10000)
                
                # Извлекаем данные
                result = await self._extract_data(page)
                
                # Закрываем браузер
                await browser.close()
                
                if result:
                    result['platform'] = 'wildberries'
                    return result
                else:
                    return {'error': 'Не удалось извлечь данные со страницы'}
                
        except Exception as e:
            logger.error(f"Ошибка парсинга через Playwright: {e}")
            return {'error': f'Ошибка парсинга: {str(e)}'}
    
    async def _apply_stealth(self, page: Page):
        """Применяет маскировку для обхода антибот-систем"""
        await page.add_init_script("""
            // Удаляем признаки автоматизации
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // Добавляем реалистичные плагины
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            
            // Устанавливаем язык
            Object.defineProperty(navigator, 'languages', {
                get: () => ['ru-RU', 'ru', 'en-US', 'en']
            });
            
            // Маскировка WebGL
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) {
                    return 'Intel Inc.';
                }
                if (parameter === 37446) {
                    return 'Intel Iris OpenGL Engine';
                }
                return getParameter(parameter);
            };
        """)
    
    async def _extract_data(self, page: Page) -> Dict:
        """Извлекает данные с загруженной страницы"""
        try:
            # Извлекаем название
            name = await page.evaluate("""
                () => {
                    const selectors = [
                        'h1[class*="product"]',
                        '[class*="product-name"]',
                        '[class*="ProductName"]',
                        '[itemprop="name"]'
                    ];
                    for (const selector of selectors) {
                        const el = document.querySelector(selector);
                        if (el) return el.textContent.trim();
                    }
                    return '';
                }
            """)
            
            # Извлекаем бренд
            brand = await page.evaluate("""
                () => {
                    const selectors = [
                        '[class*="brand"]',
                        '[class*="Brand"]',
                        '[itemprop="brand"]'
                    ];
                    for (const selector of selectors) {
                        const el = document.querySelector(selector);
                        if (el) return el.textContent.trim();
                    }
                    // Ищем в JSON-LD
                    const scripts = document.querySelectorAll('script[type="application/ld+json"]');
                    for (const script of scripts) {
                        try {
                            const data = JSON.parse(script.textContent);
                            if (data.brand) return data.brand.name || data.brand;
                        } catch(e) {}
                    }
                    return '';
                }
            """)
            
            # Извлекаем цену
            price = await page.evaluate("""
                () => {
                    const selectors = [
                        '[class*="price"]',
                        '[class*="Price"]',
                        '[itemprop="price"]',
                        '[class*="final-price"]'
                    ];
                    for (const selector of selectors) {
                        const el = document.querySelector(selector);
                        if (el) {
                            const text = el.textContent.replace(/[^\\d.]/g, '');
                            const num = parseFloat(text);
                            if (!isNaN(num) && num > 0) return num;
                        }
                    }
                    return null;
                }
            """)
            
            # Извлекаем рейтинг
            rating = await page.evaluate("""
                () => {
                    const selectors = [
                        '[class*="rating"]',
                        '[class*="Rating"]',
                        '[itemprop="ratingValue"]'
                    ];
                    for (const selector of selectors) {
                        const el = document.querySelector(selector);
                        if (el) {
                            const text = el.textContent.replace(',', '.');
                            const num = parseFloat(text);
                            if (!isNaN(num)) return num;
                        }
                    }
                    return 0;
                }
            """)
            
            # Извлекаем описание
            description = await page.evaluate("""
                () => {
                    const selectors = [
                        '[class*="description"]',
                        '[class*="Description"]',
                        '[itemprop="description"]',
                        '.product-description'
                    ];
                    for (const selector of selectors) {
                        const el = document.querySelector(selector);
                        if (el) return el.textContent.trim();
                    }
                    return '';
                }
            """)
            
            # Извлекаем характеристики
            characteristics = await page.evaluate("""
                () => {
                    const chars = {};
                    const containers = document.querySelectorAll('[class*="characteristic"], [class*="Characteristic"], [class*="params"]');
                    for (const container of containers) {
                        const items = container.querySelectorAll('li, div, tr');
                        for (const item of items) {
                            const text = item.textContent.trim();
                            if (text.includes(':')) {
                                const [key, ...valueParts] = text.split(':');
                                chars[key.trim()] = valueParts.join(':').trim();
                            } else if (text.includes('—')) {
                                const [key, ...valueParts] = text.split('—');
                                chars[key.trim()] = valueParts.join('—').trim();
                            }
                        }
                    }
                    return chars;
                }
            """)
            
            return {
                'name': name or 'Название не указано',
                'brand': brand or 'Не указан',
                'price': price,
                'rating': rating,
                'reviews_count': 0,  # Для отзывов нужен отдельный запрос
                'description': description[:5000] if description else '',
                'characteristics': characteristics
            }
            
        except Exception as e:
            logger.error(f"Ошибка извлечения данных: {e}")
            return None
