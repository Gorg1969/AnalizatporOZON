import os
import logging
import asyncio
import threading
import uvicorn
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================
# ЗАПУСК ВЕБ-СЕРВЕРА (FastAPI)
# ============================================

def run_web_server():
    """Запускает FastAPI веб-сервер в отдельном потоке"""
    try:
        # Импортируем FastAPI приложение
        from web.main import app
        
        port = int(os.getenv("PORT", 8000))
        
        logger.info(f"🌐 Запуск веб-сервера на порту {port}")
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"❌ Ошибка запуска веб-сервера: {e}")

# ============================================
# ЗАПУСК БОТА
# ============================================

async def run_bot():
    """Запускает бота"""
    try:
        BOT_PLATFORM = os.getenv("BOT_PLATFORM", "max")
        MAX_BOT_TOKEN = os.getenv("MAX_BOT_TOKEN")
        
        if not MAX_BOT_TOKEN:
            logger.error("❌ MAX_BOT_TOKEN не найден!")
            return
            
        if BOT_PLATFORM == "max":
            from bot.max_bot import start_max_bot
            await start_max_bot(MAX_BOT_TOKEN)
        else:
            from bot.telegram_bot import start_telegram_bot
            await start_telegram_bot(MAX_BOT_TOKEN)
            
    except Exception as e:
        logger.error(f"❌ Ошибка запуска бота: {e}")

# ============================================
# ГЛАВНАЯ ТОЧКА ВХОДА
# ============================================

if __name__ == "__main__":
    logger.info("🚀 Запуск приложения...")
    
    # Запускаем веб-сервер в отдельном потоке
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    
    # Запускаем бота в основном потоке
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        logger.info("👋 Приложение остановлено")
