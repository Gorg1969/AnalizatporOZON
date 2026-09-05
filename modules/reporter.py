import pandas as pd
from io import BytesIO
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

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
            'Количество отзывов': data.get('reviews_count', ''),
            'Платформа': data.get('platform', ''),
            'Описание': data.get('description', '')[:500] + '...' if data.get('description') else ''
        }
        
        df = pd.DataFrame([flat_data])
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Анализ', index=False)
            
            worksheet = writer.sheets['Анализ']
            for col in worksheet.columns:
                max_length = 0
                column = col[0].column_letter
                for cell in col:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column].width = adjusted_width
        
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
                'Количество отзывов': data.get('reviews_count', ''),
                'Платформа': data.get('platform', ''),
                'Описание': data.get('description', '')[:200] + '...' if data.get('description') else ''
            })
        
        df = pd.DataFrame(rows)
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Анализ конкурентов', index=False)
            
            if len(rows) > 0:
                avg_rating = df['Рейтинг'].mean() if not df['Рейтинг'].isna().all() else 0
                avg_price = df['Цена'].mean() if not df['Цена'].isna().all() else 0
                
                summary = pd.DataFrame([{
                    'Всего товаров': len(data_list),
                    'Средний рейтинг': round(avg_rating, 2) if avg_rating else 0,
                    'Средняя цена': round(avg_price, 2) if avg_price else 0,
                    'Платформ': df['Платформа'].nunique()
                }])
                summary.to_excel(writer, sheet_name='Сводка', index=False)
            
            for sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]
                for col in worksheet.columns:
                    max_length = 0
                    column = col[0].column_letter
                    for cell in col:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column].width = adjusted_width
        
        output.seek(0)
        return output
