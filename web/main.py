import os
import logging
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
import asyncio

# Импортируем наши модули
from modules.detector import SiteDetector
from modules.reporter import ReportGenerator
from modules.security import SecurityManager

logger = logging.getLogger(__name__)

# Создаём папку для статики
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)

app = FastAPI(title="Market Analyzer", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Монтируем статику
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Хранилище сессий (в реальном проекте — Redis)
sessions = {}
security = SecurityManager()


# ============================================
# МОДЕЛИ
# ============================================

class AnalyzeRequest(BaseModel):
    url: str


# ============================================
# ФУНКЦИЯ АНАЛИЗА
# ============================================

async def analyze_product(url: str):
    """Основная функция анализа товара"""
    # 1. Проверка безопасности
    if not SiteDetector.is_safe(url):
        return {"error": "Ссылка не распознана или является потенциально опасной"}
    
    # 2. Определяем сайт
    site = SiteDetector.detect(url)
    logger.info(f"Определён сайт: {site} для {url}")
    
    if site == 'unknown':
        return {"error": "Не удалось определить маркетплейс. Поддерживаются: Wildberries, Ozon, Яндекс.Маркет"}
    
    # 3. Извлекаем ID товара
    product_id = SiteDetector.extract_product_id(url, site)
    if not product_id:
        return {"error": "Не удалось извлечь ID товара из ссылки"}
    
    # 4. Парсим в зависимости от сайта
    try:
        if site == 'wildberries':
            from modules.wildberries import WildberriesParser
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                parser = WildberriesParser(session)
                result = await parser.parse(url)
                
        elif site == 'ozon':
            from modules.ozon import OzonParser
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                parser = OzonParser(session)
                result = await parser.parse(url)
                
        else:
            return {"error": f"Парсер для {site} пока в разработке"}
        
        if result.get('error'):
            return result
            
        # 5. Добавляем информацию о платформе
        result['platform'] = site
        
        # 6. Генерируем слабые места
        result['weak_spots'] = ReportGenerator.generate_weak_spots_report(result)
        
        return result
        
    except Exception as e:
        logger.error(f"Ошибка парсинга: {e}")
        return {"error": f"Ошибка при парсинге: {str(e)}"}


# ============================================
# ЭНДПОИНТЫ СТРАНИЦ
# ============================================

@app.get("/", response_class=HTMLResponse)
async def index():
    html_file = static_dir / "index.html"
    if html_file.exists():
        return HTMLResponse(html_file.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Страница в разработке</h1>")


@app.get("/single", response_class=HTMLResponse)
async def single_mode():
    html_file = static_dir / "single.html"
    if html_file.exists():
        return HTMLResponse(html_file.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Страница в разработке</h1>")


@app.get("/pro", response_class=HTMLResponse)
async def pro_mode():
    html_file = static_dir / "pro.html"
    if html_file.exists():
        return HTMLResponse(html_file.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Страница в разработке</h1>")


# ============================================
# API ЭНДПОИНТЫ
# ============================================

@app.post("/api/analyze")
async def analyze(request: AnalyzeRequest):
    """Анализ одной ссылки"""
    url = request.url.strip()
    
    # Проверка URL
    if not SiteDetector.is_valid_url(url):
        return JSONResponse(
            status_code=400,
            content={"error": "Некорректный URL. Проверьте ссылку."}
        )
    
    # Проверка на опасность
    if not SiteDetector.is_safe(url):
        return JSONResponse(
            status_code=400,
            content={"error": "Ссылка не распознана или является потенциально опасной"}
        )
    
    # Выполняем анализ
    result = await analyze_product(url)
    
    if result.get('error'):
        return JSONResponse(
            status_code=400,
            content={"error": result['error']}
        )
    
    # Сохраняем результат
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        "url": url,
        "data": result,
        "created_at": str(uuid.uuid4())
    }
    
    return {
        "success": True,
        "session_id": session_id,
        "message": "Анализ завершён",
        "preview": {
            "name": result.get('name', ''),
            "brand": result.get('brand', ''),
            "price": result.get('price', ''),
            "rating": result.get('rating', ''),
            "weak_spots": result.get('weak_spots', '')
        }
    }


@app.get("/api/download/{session_id}")
async def download_report(session_id: str):
    """Скачивание отчёта"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    
    try:
        data = sessions[session_id]["data"]
        output = ReportGenerator.generate_single_report(data)
        
        return FileResponse(
            path=output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=f"report_{session_id[:8]}.xlsx"
        )
    except Exception as e:
        logger.error(f"Ошибка генерации отчёта: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка генерации: {str(e)}")


@app.get("/api/download-pro")
async def download_pro_report():
    """Скачивание отчёта для профи-режима (заглушка)"""
    # В реальном проекте здесь будет генерация отчёта из нескольких товаров
    try:
        # Заглушка
        data_list = [
            {"name": "Товар 1", "brand": "Brand A", "price": 1000, "rating": 4.5, "platform": "wildberries"},
            {"name": "Товар 2", "brand": "Brand B", "price": 2000, "rating": 4.2, "platform": "ozon"},
        ]
        output = ReportGenerator.generate_pro_report(data_list)
        
        return FileResponse(
            path=output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename="pro_report.xlsx"
        )
    except Exception as e:
        logger.error(f"Ошибка генерации отчёта: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка генерации: {str(e)}")


# ============================================
# ЗАПУСК (для локальной разработки)
# ============================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
