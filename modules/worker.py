import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Callable, Any
import logging

logger = logging.getLogger(__name__)

class TaskManager:
    """Менеджер для параллельной обработки задач"""
    
    def __init__(self, max_workers: int = 10):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.tasks = {}
        self.running = True
    
    async def process_urls(self, urls: List[str], processor: Callable) -> List[Dict]:
        """Обрабатывает список URL параллельно"""
        loop = asyncio.get_event_loop()
        tasks = []
        
        for url in urls:
            task = loop.run_in_executor(self.executor, processor, url)
            tasks.append(task)
        
        # Запускаем все задачи параллельно
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Обрабатываем результаты
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                processed_results.append({'error': str(result)})
            else:
                processed_results.append(result)
        
        return processed_results
    
    def shutdown(self):
        """Корректно завершает работу пула"""
        self.running = False
        self.executor.shutdown(wait=True)
