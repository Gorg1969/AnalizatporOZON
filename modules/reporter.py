import pandas as pd
from io import BytesIO
from typing import List, Dict

class ReportGenerator:
    """Генерация отчётов в Excel"""
    
    @staticmethod
    def generate_single_report(data: Dict) -> BytesIO:
        """Создаёт отчёт для одного товара"""
        output = BytesIO()
        
        flat_data = {
            'Название': data.get('name', ''),
            'Бренд': data.get('brand', ''),
            'Цена': data.get('price', ''),
            'Рейтинг': data.get('rating', ''),
            'Платформа': data.get('platform', ''),
            'Описание': data.get('description', '')[:500] + '...' if data.get('description') else ''
        }
        
        df = pd.DataFrame([flat_data])
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Анализ', index=False)
        
        output.seek(0)
        return output
    
    @staticmethod
    def generate_pro_report(data_list: List[Dict]) -> BytesIO:
        """Создаёт отчёт для нескольких товаров"""
        output = BytesIO()
        
        rows = []
        for data in data_list:
            rows.append({
                'Название': data.get('name', ''),
                'Бренд': data.get('brand', ''),
                'Цена': data.get('price', ''),
                'Рейтинг': data.get('rating', ''),
                'Платформа': data.get('platform', ''),
                'Описание': data.get('description', '')[:200] + '...' if data.get('description') else ''
            })
        
        df = pd.DataFrame(rows)
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Анализ конкурентов', index=False)
        
        output.seek(0)
        return output
