import logging
import os
from obabot import create_bot
from obabot.filters import Command

logger = logging.getLogger(__name__)

async def start_max_bot(token: str):
    """Запускает бота для платформы MAX"""
    
    WEBAPP_URL = os.getenv("WEBAPP_URL", "https://ваш-бот.bothost.tech")
    
    # Создаём бота
    bot, dp, router = create_bot(max_token=token)
    
    @router.message(Command("start"))
    async def start_command(message):
        """Обработчик команды /start"""
        # Простое сообщение со ссылкой (без WebApp)
        await message.answer(
            "👋 Привет! Я помогу проанализировать карточки конкурентов на маркетплейсах.\n\n"
            "📌 Что я умею:\n"
            "• Анализировать карточки Wildberries, Ozon, Яндекс.Маркет\n"
            "• Находить слабые места в описаниях\n"
            "• Сравнивать характеристики\n"
            "• Генерировать отчёты в Excel\n\n"
            f"🔗 Открой сервис по ссылке:\n{WEBAPP_URL}\n\n"
            "Или используй команду /analyze <ссылка> для быстрого анализа."
        )
    
    @router.message(Command("analyze"))
    async def analyze_command(message):
        """Обработчик команды /analyze"""
        # Получаем текст после команды
        text = message.text
        parts = text.split(maxsplit=1)
        
        if len(parts) < 2:
            await message.answer(
                "❌ Укажите ссылку для анализа.\n"
                "Пример: /analyze https://www.wildberries.ru/catalog/12345678/detail.aspx"
            )
            return
        
        url = parts[1].strip()
        
        # Проверяем ссылку
        if not url.startswith(('http://', 'https://')):
            await message.answer("❌ Некорректная ссылка. Убедитесь, что она начинается с http:// или https://")
            return
        
        await message.answer(f"🔍 Анализирую: {url}\n⏳ Пожалуйста, подождите...")
        
        # Здесь будет вызов функции анализа
        # Пока заглушка
        await message.answer(
            "✅ Анализ завершён!\n\n"
            "📄 Отчёт готов. Скачать можно по ссылке:\n"
            f"{WEBAPP_URL}/download/report"
        )
    
    logger.info("🤖 MAX бот запущен и готов к работе")
    await dp.start_polling(bot)
