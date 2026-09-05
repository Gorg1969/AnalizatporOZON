import os
import logging
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path

from modules.detector import SiteDetector
from modules.reporter import ReportGenerator

logger = logging.getLogger(__name__)

static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)

app = FastAPI(title="Market Analyzer", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

sessions = {}


class AnalyzeRequest(BaseModel):
    url: str


# ============================================
# СТРАНИЦЫ
# ============================================

@app.get("/", response_class=HTMLResponse)
async def index():
    html_file = static_dir / "index.html"
    if html_file.exists():
        return HTMLResponse(html_file.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Анализатор карточек</h1><p>Страница в разработке</p>")


@app.get("/single", response_class=HTMLResponse)
async def single_mode():
    html_file = static_dir / "single.html"
    if html_file.exists():
        return HTMLResponse(html_file.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Разовый режим</h1><p>Страница в разработке</p>")


@app.get("/pro", response_class=HTMLResponse)
async def pro_mode():
    html_file = static_dir / "pro.html"
    if html_file.exists():
        return HTMLResponse(html_file.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Профи-режим</h1><p>Страница в разработке</p>")


# ============================================
# API
# ============================================

@app.post("/api/analyze")
async def analyze(request: AnalyzeRequest):
    url = request.url.strip()
    if not SiteDetector.is_valid_url(url):
        return JSONResponse(status_code=400, content={"error": "Некорректный URL"})
    if not SiteDetector.is_safe(url):
        return JSONResponse(status_code=400, content={"error": "Ссылка не распознана"})
    
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        "url": url,
        "data": {
            "name": "Пример товара",
            "brand": "Пример бренда",
            "price": 1000,
            "rating": 4.5,
            "platform": "wildberries",
            "description": "Это пример описания товара"
        }
    }
    
    return {"success": True, "session_id": session_id, "message": "Анализ завершён"}


@app.get("/api/download/{session_id}")
async def download_report(session_id: str):
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
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")


# ============================================
# ПРОСТОЙ МАРШРУТ ДЛЯ СКАЧИВАНИЯ ОТЧЁТА
# ============================================

@app.get("/download/report")
async def download_report_simple():
    """
    Простой маршрут для скачивания отчёта
    """
    try:
        test_data = {
            'name': 'Тестовый товар',
            'brand': 'ТестБренд',
            'price': 1499,
            'rating': 4.7,
            'reviews_count': 125,
            'platform': 'wildberries',
            'description': 'Тестовое описание товара для проверки.'
        }
        output = ReportGenerator.generate_single_report(test_data)
        return FileResponse(
            path=output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename="report.xlsx"
        )
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


# ============================================
# ЗАПУСК
# ============================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
