import asyncio
import sqlite3
import random
import os
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode

# ========== ВЕБ-СЕРВЕР ДЛЯ RENDER ==========
from flask import Flask
import threading

flask_app = Flask(__name__)

@flask_app.route('/')
def health_check():
    return "✅ MemCase Bot is running!", 200

def run_web_server():
    port = int(os.environ.get('PORT', 10000))
    flask_app.run(host='0.0.0.0', port=port)

# Запускаем веб-сервер в отдельном потоке
threading.Thread(target=run_web_server, daemon=True).start()
# ==========================================

# ========== КОНФИГУРАЦИЯ ==========
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8123456789:AAE_ВАШ_ТОКЕН_ЗДЕСЬ")
WEBAPP_URL = os.environ.get("WEBAPP_URL", "https://memcase.vercel.app")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ========== БАЗА ДАННЫХ ==========
def init_db():
    conn = sqlite3.connect('memcase.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            tg_id INTEGER PRIMARY KEY,
            username TEXT,
            coins INTEGER DEFAULT 100,
            crystals INTEGER DEFAULT 5,
            opened_cases INTEGER DEFAULT 0,
            last_free_case TEXT,
            combo_count INTEGER DEFAULT 0,
            last_open_time TEXT,
            daily_bonus TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_memes (
            user_id INTEGER,
            meme_title TEXT,
            meme_rarity TEXT,
            opened_at TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

init_db()

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========
def get_user(tg_id):
    conn = sqlite3.connect('memcase.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE tg_id = ?", (tg_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def register_user(tg_id, username):
    conn = sqlite3.connect('memcase.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (tg_id, username) VALUES (?, ?)", (tg_id, username))
    conn.commit()
    conn.close()

def update_coins(tg_id, amount):
    conn = sqlite3.connect('memcase.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET coins = coins + ? WHERE tg_id = ?", (amount, tg_id))
    conn.commit()
    conn.close()

# ========== КОМАНДЫ БОТА ==========
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user = message.from_user
    register_user(user.id, user.username)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 ОТКРЫТЬ MEMCASE", web_app=WebAppInfo(url=WEBAPP_URL))],
        [InlineKeyboardButton(text="📊 Профиль", callback_data="profile"),
         InlineKeyboardButton(text="🎁 Бонус", callback_data="daily")]
    ])
    
    await message.answer(
        f"<b>🔥 ДОБРО ПОЖАЛОВАТЬ В MEMCASE, {user.first_name}!</b>\n\n"
        f"🎮 Собирай вирусные мемы\n"
        f"🎁 Открывай кейсы в WebApp\n"
        f"👑 Стань Мем-королём",
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )

@dp.callback_query()
async def handle_callbacks(callback: types.CallbackQuery):
    if callback.data == "profile":
        user = get_user(callback.from_user.id)
        if user:
            await callback.message.answer(f"👤 Профиль:\n🪙 Монет: {user[2]}\n💎 Кристаллов: {user[3]}\n🎁 Открыто кейсов: {user[4]}")
    elif callback.data == "daily":
        update_coins(callback.from_user.id, 50)
        await callback.message.answer("🎁 +50 монет! Заходи завтра снова!")
    await callback.answer()

# ========== ЗАПУСК БОТА ==========
async def main():
    print("🤖 MemCase Бот запущен!")
    print(f"Бот: @{(await bot.get_me()).username}")
    print("Ожидание сообщений...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
