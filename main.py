import os
import sys
import logging
import asyncio
import threading
from pathlib import Path

# Добавляем корневую папку в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_web_server():
    """Запускает FastAPI веб-сервер"""
    try:
        from web.main import app
        import uvicorn
        port = int(os.getenv("PORT", 8000))
        logger.info(f"🌐 Запуск веб-сервера на порту {port}")
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
    except Exception as e:
        logger.error(f"❌ Ошибка запуска веб-сервера: {e}")


async def run_bot():
    """Запускает бота"""
    try:
        from bot.max_bot import start_max_bot
        token = os.getenv("MAX_BOT_TOKEN")
        if not token:
            logger.error("❌ MAX_BOT_TOKEN не найден!")
            return
        await start_max_bot(token)
    except Exception as e:
        logger.error(f"❌ Ошибка запуска бота: {e}")


if __name__ == "__main__":
    logger.info("🚀 Запуск приложения...")
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        logger.info("👋 Приложение остановлено")
