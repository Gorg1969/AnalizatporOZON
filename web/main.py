import os
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
import json
from pathlib import Path

logger = logging.getLogger(__name__)

# Создаём папку для статики если её нет
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)

app = FastAPI(title="Market Analyzer", version="1.0.0")

# CORS для безопасности
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Монтируем статику
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


# ============================================
# ВРЕМЕННОЕ ХРАНИЛИЩЕ (в реальном проекте — Redis или БД)
# ============================================

sessions = {}


# ============================================
# МОДЕЛИ ДАННЫХ
# ============================================

class AnalyzeRequest(BaseModel):
    url: str


# ============================================
# ЭНДПОИНТЫ СТРАНИЦ
# ============================================

@app.get("/", response_class=HTMLResponse)
async def index():
    """Главная страница с меню"""
    html_file = static_dir / "index.html"
    if html_file.exists():
        return HTMLResponse(html_file.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Страница в разработке</h1>")


@app.get("/single", response_class=HTMLResponse)
async def single_mode():
    """Страница разового режима"""
    html_file = static_dir / "single.html"
    if html_file.exists():
        return HTMLResponse(html_file.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Страница в разработке</h1>")


@app.get("/pro", response_class=HTMLResponse)
async def pro_mode():
    """Страница профи-режима"""
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
    url = request.url
    
    # Простая валидация
    if not url.startswith(('http://', 'https://')):
        return JSONResponse(
            status_code=400,
            content={"error": "Некорректный URL. Ссылка должна начинаться с http:// или https://"}
        )
    
    # Проверка на опасные ссылки
    dangerous = ['.exe', '.zip', '.rar', 'javascript:', 'data:', 'file:']
    for d in dangerous:
        if d in url.lower():
            return JSONResponse(
                status_code=400,
                content={"error": f"Обнаружен потенциально опасный URL (содержит {d})"}
            )
    
    # Генерируем ID сессии
    session_id = str(uuid.uuid4())
    
    # Здесь будет реальный анализ (пока заглушка)
    # Импортируем парсеры
    try:
        from modules.detector import SiteDetector
        
        site = SiteDetector.detect(url)
        logger.info(f"Определён сайт: {site} для {url}")
        
        # TODO: реальный парсинг
        
        sessions[session_id] = {
            "url": url,
            "site": site,
            "status": "completed",
            "data": {
                "name": "Пример товара",
                "brand": "Пример бренда",
                "price": 1000,
                "rating": 4.5,
                "platform": site,
                "description": "Это пример описания товара. В реальном режиме здесь будут данные с маркетплейса."
            }
        }
    except Exception as e:
        logger.error(f"Ошибка анализа: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Ошибка при анализе: {str(e)}"}
        )
    
    return {
        "success": True,
        "session_id": session_id,
        "message": "Анализ завершён"
    }


@app.get("/api/download/{session_id}")
async def download_report(session_id: str):
    """Скачивание отчёта"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    
    try:
        from modules.reporter import ReportGenerator
        
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
    try:
        from modules.reporter import ReportGenerator
        
        # Заглушка с несколькими товарами
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
