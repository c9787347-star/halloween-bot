import os
import asyncio
import aiosqlite
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiohttp import web

# === НАСТРОЙКИ (ИЗМЕНИТЕ ЭТО) ===
BOT_TOKEN = "9194764652:AAGiJDm3vf-7LxxIqgt-1som2NoF4uJKBkY"
CHANNELS = ["@starstrawa"] # Ваши каналы
ADMIN_USERNAME = "plsuy"

WEBAPP_URL = "https://c9787347-star.github.io/halloween-bot/index.html"  # <--- ВОТ ЭТА СТРОКА
bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# === БАЗА ДАННЫХ ===
async def init_db():
    async with aiosqlite.connect("giveaways.db") as db:
        await db.execute("CREATE TABLE IF NOT EXISTS participants (id INTEGER PRIMARY KEY, giveaway_id INTEGER, user_id INTEGER, username TEXT, UNIQUE(giveaway_id, user_id))")
        await db.commit()

# === БОТ ===
async def is_admin(user):
    return user.username and user.username.lower() == ADMIN_USERNAME.lower()

async def check_subs(user_id):
    for ch in CHANNELS:
        try:
            m = await bot.get_chat_member(chat_id=ch, user_id=user_id)
            if m.status not in ("member", "administrator", "creator"):
                return False, ch
        except Exception:
            return False, ch
    return True, None

@dp.message(Command("start"))
async def cmd_start(message: Message):
    # Получаем ссылку на наш сайт из переменных окружения Railway
    domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", "your-domain.up.railway.app")
    
    ok, missing = await check_subs(message.from_user.id)
    if not ok:
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=f"📢 Подписаться на {missing}", url=f"https://t.me/{missing.lstrip('@')}")]])
        await message.answer("Сначала подпишитесь 👇", reply_markup=kb)
        return
    
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🎃 Участвовать", web_app=WebAppInfo(url=f"https://{domain}/"))
    ]])
    await message.answer("🎃 <b>Добро пожаловать!</b>\nНажмите кнопку ниже, чтобы участвовать.", reply_markup=kb)

@dp.message(Command("create"))
async def cmd_create(message: Message):
    if not await is_admin(message.from_user):
        await message.answer("⛔ Нет прав.")
        return
    await message.answer("✅ Вы админ! (Тут будет создание розыгрыша)")

# === ВЕБ-СЕРВЕР (ДЛЯ WEB APP) ===
async def handle_index(request):
    return web.FileResponse('./webapp/index.html')

async def handle_css(request):
    return web.FileResponse('./webapp/style.css')

async def handle_js(request):
    return web.FileResponse('./webapp/app.js')

async def handle_check(request):
    # Заглушка для проверки (в будущем можно доработать)
    return web.json_response({"ok": True})

# === ЗАПУСК ВСЕГО ВМЕСТЕ ===
async def main():
    await init_db()
    
    # Запускаем бота в фоне
    asyncio.create_task(dp.start_polling(bot))
    print("Бот запущен!")
    
    # Запускаем веб-сервер
    app = web.Application()
    app.router.add_get('/', handle_index)
    app.router.add_get('/style.css', handle_css)
    app.router.add_get('/app.js', handle_js)
    app.router.add_post('/api/check_subscription', handle_check)
    
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    # Держим сервер включенным
    while True:
        await asyncio.sleep(3600)

if name == "main":
    asyncio.run(main())
