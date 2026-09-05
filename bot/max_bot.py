import logging
import os
import aiohttp
from obabot import create_bot
from obabot.filters import Command

logger = logging.getLogger(__name__)

# Импортируем детектор и парсеры
from modules.detector import SiteDetector
from modules.wildberries import WildberriesParser
from modules.ozon import OzonParser


async def start_max_bot(token: str):
    WEBAPP_URL = os.getenv("WEBAPP_URL", "https://ваш-бот.bothost.tech")
    
    bot, dp, router = create_bot(max_token=token)
    
    @router.message(Command("start"))
    async def start_command(message):
        await message.answer(
            "👋 Привет! Я помогу проанализировать карточки конкурентов.\n\n"
            "📌 Отправь команду:\n"
            "/analyze <ссылка> — анализ карточки\n\n"
            "📌 Поддерживаются:\n"
            "• Wildberries\n"
            "• Ozon\n"
            "• Яндекс.Маркет (скоро)\n\n"
            f"🔗 Или открой веб-сервис:\n{WEBAPP_URL}"
        )
    
    @router.message(Command("analyze"))
    async def analyze_command(message):
        # Получаем ссылку из команды
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
        
        # Проверяем безопасность
        if not SiteDetector.is_safe(url):
            await message.answer("❌ Ссылка не распознана или является потенциально опасной")
            return
        
        # Определяем сайт
        site = SiteDetector.detect(url)
        await message.answer(f"🔍 Определён маркетплейс: **{site}**\n⏳ Начинаю анализ...")
        
        try:
            # Выполняем парсинг в зависимости от сайта
            async with aiohttp.ClientSession() as session:
                if site == 'wildberries':
                    parser = WildberriesParser(session)
                    result = await parser.parse(url)
                elif site == 'ozon':
                    parser = OzonParser(session)
                    result = await parser.parse(url)
                else:
                    await message.answer(f"❌ Маркетплейс '{site}' пока не поддерживается")
                    return
                
                if result.get('error'):
                    await message.answer(f"❌ Ошибка: {result['error']}")
                    return
                
                # Формируем красивый ответ
                response = f"📊 **Результат анализа**\n\n"
                response += f"📌 **Название:** {result.get('name', 'Не указано')}\n"
                response += f"🏷️ **Бренд:** {result.get('brand', 'Не указан')}\n"
                response += f"💰 **Цена:** {result.get('price', 'Не указана')} ₽\n"
                response += f"⭐ **Рейтинг:** {result.get('rating', 'Нет')}\n"
                response += f"💬 **Отзывов:** {result.get('reviews_count', 'Нет')}\n"
                response += f"📱 **Платформа:** {result.get('platform', 'Неизвестно')}\n\n"
                
                # Добавляем описание (сокращённо)
                desc = result.get('description', '')
                if desc:
                    if len(desc) > 300:
                        desc = desc[:300] + '...'
                    response += f"📝 **Описание:** {desc}\n\n"
                
                # Добавляем характеристики
                chars = result.get('characteristics', {})
                if chars:
                    response += "📋 **Характеристики:**\n"
                    for key, value in list(chars.items())[:5]:
                        response += f"• {key}: {value}\n"
                
                # Добавляем ссылку на полный отчёт
                response += f"\n🔗 Полный отчёт в Excel будет доступен в веб-версии"
                
                await message.answer(response)
                
        except Exception as e:
            logger.error(f"Ошибка при анализе: {e}")
            await message.answer(f"❌ Произошла ошибка при анализе: {str(e)}")
    
    logger.info("🤖 MAX бот запущен и готов к работе")
    await dp.start_polling(bot)
