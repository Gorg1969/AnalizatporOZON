import os
import re
import time
import hashlib
from collections import defaultdict
from typing import Tuple, Optional

class SecurityManager:
    """Управление безопасностью и защитой от атак"""
    
    def __init__(self):
        self.rate_limits = defaultdict(list)
        self.blocked_ips = set()
        self.max_requests_per_minute = int(os.getenv("RATE_LIMIT_PER_MINUTE", 10))
        self.block_duration = 5  # минут
    
    def check_rate_limit(self, ip: str) -> bool:
        """Проверяет, не превысил ли пользователь лимит запросов"""
        if ip in self.blocked_ips:
            return False
            
        now = time.time()
        # Очищаем старые записи (старше 60 секунд)
        self.rate_limits[ip] = [
            t for t in self.rate_limits[ip] 
            if now - t < 60
        ]
        
        if len(self.rate_limits[ip]) >= self.max_requests_per_minute:
            self.blocked_ips.add(ip)
            return False
            
        self.rate_limits[ip].append(now)
        return True
    
    @staticmethod
    def get_client_ip(request) -> str:
        """Получает реальный IP клиента"""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host
    
    @staticmethod
    def sanitize_url(url: str) -> Tuple[bool, str]:
        """Очищает URL и проверяет на опасность"""
        if not url:
            return False, "URL не может быть пустым"
            
        if len(url) > 2048:
            return False, "Слишком длинный URL"
            
        dangerous_patterns = [
            r'(?:\.\./|\.\.\\)',
            r'(?i)(?:<script|javascript:|onerror=)',
            r'(?i)(?:\.exe|\.dll|\.bat|\.cmd)$',
            r'(?i)(?:file://|ftp://|gopher://)'
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, url):
                return False, "Обнаружен потенциально опасный URL"
                
        if not re.match(r'^https?://', url):
            return False, "Поддерживаются только HTTP и HTTPS ссылки"
            
        return True, url
    
    @staticmethod
    def get_fingerprint(ip: str, user_agent: str) -> str:
        """Создаёт отпечаток для идентификации пользователя"""
        data = f"{ip}:{user_agent}"
        return hashlib.sha256(data.encode()).hexdigest()
