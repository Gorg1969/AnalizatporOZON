import logging
import os
from obabot import create_bot
from obabot.filters import Command
from obabot.types import WebAppInfo, ReplyKeyboardMarkup, KeyboardButton

logger = logging.getLogger(__name__)

async def start_max_bot(token: str):
    """Запускает бота для платформы MAX"""
    
    WEBAPP_URL = os.getenv("WEBAPP_URL", "https://ваш-бот.bothost.tech")
    
    # Создаём бота
    bot, dp, router = create_bot(max_token=token)
    
    @router.message(Command("start"))
    async def start_command(message):
        """Обработчик команды /start"""
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(
                    text="🔍 АНАЛИЗ",
                    web_app=WebAppInfo(url=WEBAPP_URL)
                )]
            ],
            resize_keyboard=True
        )
        
        await message.answer(
            "👋 Привет! Я помогу проанализировать карточки конкурентов на маркетплейсах.\n\n"
            "📌 Что я умею:\n"
            "• Анализировать карточки Wildberries, Ozon, Яндекс.Маркет\n"
            "• Находить слабые места в описаниях\n"
            "• Сравнивать характеристики\n"
            "• Генерировать отчёты в Excel\n\n"
            "Нажми кнопку **АНАЛИЗ**, чтобы открыть сервис.",
            reply_markup=keyboard
        )
    
    logger.info("🤖 MAX бот запущен и готов к работе")
    await dp.start_polling(bot)
