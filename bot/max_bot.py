import logging
import os
import aiohttp
import asyncio
from obabot import create_bot
from obabot.filters import Command

logger = logging.getLogger(__name__)

from modules.detector import SiteDetector
from modules.wildberries import WildberriesParser
from modules.ozon import OzonParser


async def start_max_bot(token: str):
    WEBAPP_URL = os.getenv("WEBAPP_URL", "https://bot-1788513478-6189-evgeniy-zn.bothost.tech")
    
    bot, dp, router = create_bot(max_token=token)
    
    @router.message(Command("start"))
    async def start_command(message):
        await message.answer(
            "👋 Привет! Я помогу проанализировать карточки конкурентов.\n\n"
            "📌 Отправь команду:\n"
            "/analyze <ссылка> — анализ карточки\n\n"
            "📌 Поддерживаются:\n"
            "• Wildberries\n"
            "• Ozon\n\n"
            f"🔗 Или открой веб-сервис:\n{WEBAPP_URL}"
        )
    
    @router.message(Command("analyze"))
    async def analyze_command(message):
        text = message.text
        parts = text.split(maxsplit=1)
        
        if len(parts) < 2:
            await message.answer(
                "❌ Укажите ссылку для анализа.\n"
                "Пример: /analyze https://www.wildberries.ru/catalog/12345678/detail.aspx"
            )
            return
        
        url = parts[1].strip()
        
        if not url.startswith(('http://', 'https://')):
            await message.answer("❌ Некорректная ссылка")
            return
        
        site = SiteDetector.detect(url)
        await message.answer(f"🔍 Определён маркетплейс: **{site}**\n⏳ Начинаю анализ...")
        
        try:
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
                
                # Формируем ответ
                response = f"📊 **Результат анализа**\n\n"
                response += f"📌 **Название:** {result.get('name', 'Не указано')}\n"
                response += f"🏷️ **Бренд:** {result.get('brand', 'Не указан')}\n"
                response += f"💰 **Цена:** {result.get('price', 'Не указана')} ₽\n" if result.get('price') else f"💰 **Цена:** Не указана\n"
                response += f"⭐ **Рейтинг:** {result.get('rating', 'Нет')}\n"
                response += f"💬 **Отзывов:** {result.get('reviews_count', 'Нет')}\n\n"
                
                desc = result.get('description', '')[:300] + '...' if result.get('description') else ''
                if desc:
                    response += f"📝 **Описание:**\n{desc}\n\n"
                
                chars = result.get('characteristics', {})
                if chars:
                    response += "📋 **Характеристики:**\n"
                    for key, value in list(chars.items())[:5]:
                        response += f"• {key}: {value}\n"
                
                response += f"\n📥 Полный отчёт: {WEBAPP_URL}/download/report"
                
                await message.answer(response)
                
        except Exception as e:
            logger.error(f"Ошибка: {e}")
            await message.answer(f"❌ Ошибка: {str(e)}")
    
    logger.info("🤖 MAX бот запущен")
    await dp.start_polling(bot)
