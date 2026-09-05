import re
from urllib.parse import urlparse

class SiteDetector:
    """Автоопределение маркетплейса по ссылке"""
    
    # Паттерны для разных маркетплейсов
    PATTERNS = {
        'wildberries': [
            r'wildberries\.ru',
            r'wb\.ru',
            r'wildberries\.kz',
            r'wildberries\.by'
        ],
        'ozon': [
            r'ozon\.ru',
            r'ozon\.kz',
            r'ozon\.by'
        ],
        'yandex_market': [
            r'market\.yandex\.ru'
        ],
        'aliexpress': [
            r'aliexpress\.ru',
            r'aliexpress\.com'
        ],
        'sbermegamarket': [
            r'megamarket\.ru'
        ]
    }
    
    @classmethod
    def detect(cls, url: str) -> str:
        """
        Определяет сайт по URL.
        Возвращает: 'wildberries', 'ozon', 'yandex_market', 'aliexpress', 'sbermegamarket' или 'unknown'
        """
        if not url:
            return 'unknown'
            
        # Приводим к нижнему регистру и парсим
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        for site, patterns in cls.PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, domain):
                    return site
                    
        return 'unknown'
    
    @classmethod
    def is_valid_url(cls, url: str) -> bool:
        """Проверяет, является ли ссылка валидной"""
        if not url:
            return False
        try:
            parsed = urlparse(url)
            return all([parsed.scheme, parsed.netloc])
        except:
            return False
    
    @classmethod
    def is_safe(cls, url: str) -> bool:
        """Проверяет ссылку на потенциальную опасность (базовая защита)"""
        if not url:
            return False
            
        # Опасные паттерны
        dangerous_patterns = [
            r'\.exe$', r'\.zip$', r'\.rar$', r'\.7z$',
            r'javascript:',
            r'data:',
            r'file:',
            r'\.git',
            r'\.svn'
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, url.lower()):
                return False
                
        # Проверяем, что ссылка ведёт на известный маркетплейс
        site = cls.detect(url)
        return site != 'unknown'
    
    @classmethod
    def extract_product_id(cls, url: str, site: str) -> str:
        """Извлекает ID товара из URL в зависимости от маркетплейса"""
        if site == 'wildberries':
            # Пример: https://www.wildberries.ru/catalog/12345678/detail.aspx
            match = re.search(r'/catalog/(\d+)/', url)
            if match:
                return match.group(1)
            # Альтернативный формат: https://www.wildberries.ru/product/12345678
            match = re.search(r'/product/(\d+)', url)
            if match:
                return match.group(1)
                
        elif site == 'ozon':
            # Пример: https://www.ozon.ru/product/123456789/
            match = re.search(r'/product/(\d+)/?', url)
            if match:
                return match.group(1)
                
        elif site == 'yandex_market':
            # Пример: https://market.yandex.ru/product/1234567890
            match = re.search(r'/product/(\d+)', url)
            if match:
                return match.group(1)
                
        return None
