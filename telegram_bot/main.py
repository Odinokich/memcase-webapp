import asyncio
import sqlite3
import random
import json
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode

# ========== КОНФИГУРАЦИЯ ==========
# ВСТАВЬ СВОЙ ТОКЕН ОТ @BotFather
BOT_TOKEN = "8704536277:AAGgBpa3r-qTFJIDme9gWef1oNXcZQjyJD0"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Временная ссылка на WebApp (пока localhost, потом заменишь)
WEBAPP_URL = "https://memcase.vercel.app"  # Замени после деплоя

# ========== БАЗА ДАННЫХ ==========
def init_db():
    conn = sqlite3.connect('memcase.db')
    cursor = conn.cursor()
    
    # Таблица пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            tg_id INTEGER UNIQUE,
            username TEXT,
            coins INTEGER DEFAULT 100,
            crystals INTEGER DEFAULT 5,
            opened_cases INTEGER DEFAULT 0,
            last_free_case TEXT,
            combo_count INTEGER DEFAULT 0,
            last_open_time TEXT
        )
    ''')
    
    # Таблица мемов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS memes (
            id INTEGER PRIMARY KEY,
            title TEXT,
            rarity TEXT,
            preview_url TEXT,
            source_link TEXT,
            category TEXT
        )
    ''')
    
    # Таблица коллекции
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_memes (
            user_id INTEGER,
            meme_id INTEGER,
            opened_at TEXT,
            UNIQUE(user_id, meme_id)
        )
    ''')
    
    # Добавляем мемы если пусто
    cursor.execute("SELECT COUNT(*) FROM memes")
    if cursor.fetchone()[0] == 0:
        memes = [
            ("POV: ты забыл выключить микрофон", "обычный", "https://media.tenor.com/5iWwZrXqWl0AAAAi/cat-meme.gif", "https://tiktok.com/@memes/1", "жиза"),
            ("Как я сдавал экзамен", "обычный", "https://media.tenor.com/3oR7wX7K5VkAAAAi/meme-funny.gif", "https://youtube.com/shorts/1", "жиза"),
            ("TikTok Болливуд", "редкий", "https://media.tenor.com/8qXwR7VvX9kAAAAi/bollywood.gif", "https://tiktok.com/@memes/2", "bollywood"),
            ("Подслушано у психолога", "редкий", "https://media.tenor.com/6yWwZrXqWl0AAAAi/therapist.gif", "https://tiktok.com/@memes/3", "психолог"),
            ("ВИРУС 2024", "легендарный", "https://media.tenor.com/2pYqLvXq6YgAAAAi/viral.gif", "https://youtube.com/shorts/viral", "тренд"),
            ("Жиза на 3 секунды", "обычный", "https://media.tenor.com/4sXxWrVqY7kAAAAi/funny-cat.gif", "https://tiktok.com/@memes/4", "жиза"),
            ("Бабушка узнала про мемы", "редкий", "https://media.tenor.com/7tYyWsXqZ8lAAAAi/grandma.gif", "https://tiktok.com/@memes/5", "психолог"),
            ("Мем года", "легендарный", "https://media.tenor.com/1pXqLvWq7YgAAAAi/meme-year.gif", "https://youtube.com/shorts/meme", "тренд"),
        ]
        for meme in memes:
            cursor.execute("INSERT INTO memes (title, rarity, preview_url, source_link, category) VALUES (?, ?, ?, ?, ?)", meme)
    
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

def update_user_coins(tg_id, coins_delta):
    conn = sqlite3.connect('memcase.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET coins = coins + ? WHERE tg_id = ?", (coins_delta, tg_id))
    conn.commit()
    conn.close()

# ========== КОМАНДЫ БОТА ==========
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user = message.from_user
    register_user(user.id, user.username)
    
    # Проверка реферальной ссылки
    args = message.text.split()
    if len(args) > 1 and args[1].startswith("ref_"):
        ref_id = int(args[1].split("_")[1])
        if ref_id != user.id:
            update_user_coins(ref_id, 50)  # Бонус пригласившему
            update_user_coins(user.id, 100)  # Бонус новому
    
    welcome_text = """
<b>🔥 ДОБРО ПОЖАЛОВАТЬ В MEMCASE!</b>

🎮 Собирай вирусные мемы
🎁 Открывай кейсы каждые 30 минут
👑 Стань Мем-королём

📊 <b>Твоя статистика:</b>
🪙 Монет: 100
💎 Кристаллов: 5
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 ОТКРЫТЬ MEMCASE", web_app=WebAppInfo(url=WEBAPP_URL))],
        [InlineKeyboardButton(text="📢 Канал новостей", url="https://t.me/memecase_news"),
         InlineKeyboardButton(text="👥 Поддержка", url="https://t.me/memcase_manager")],
        [InlineKeyboardButton(text="📊 Мой профиль", callback_data="profile"),
         InlineKeyboardButton(text="🎁 Ежедневный бонус", callback_data="daily")]
    ])
    
    await message.answer(welcome_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

@dp.message(Command("profile"))
async def cmd_profile(message: types.Message):
    user = get_user(message.from_user.id)
    if user:
        profile_text = f"""
<b>👤 ВАШ ПРОФИЛЬ</b>

🪙 Монеты: {user[3]}
💎 Кристаллы: {user[4]}
🎁 Открыто кейсов: {user[5]}
🏆 Комбо: {user[7]}

<i>Приглашай друзей и получай бонусы!</i>
"""
        await message.answer(profile_text, parse_mode=ParseMode.HTML)

@dp.callback_query()
async def handle_callback(callback: types.CallbackQuery):
    if callback.data == "profile":
        user = get_user(callback.from_user.id)
        text = f"🪙 Монеты: {user[3]}\n💎 Кристаллы: {user[4]}\n🎁 Кейсов открыто: {user[5]}"
        await callback.message.answer(text)
    elif callback.data == "daily":
        update_user_coins(callback.from_user.id, 50)
        await callback.message.answer("🎁 Ты получил 50 монет! Заходи завтра снова!")
    await callback.answer()

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    help_text = """
<b>📖 КАК ИГРАТЬ:</b>

🎁 <b>Кейсы:</b>
• Обычный - бесплатно (30 мин)
• Редкий - 100 монет
• Эпический - 10 кристаллов

🎯 <b>Задания:</b>
• Пригласи друга → +50 монет
• Открой 5 кейсов → редкий кейс
• Собери 10 мемов → +100 монет

👑 <b>Редкости мемов:</b>
🟢 Обычные
🔵 Редкие
🟡 Легендарные

<i>Больше мемов - выше рейтинг!</i>
"""
    await message.answer(help_text, parse_mode=ParseMode.HTML)

# ========== ЗАПУСК БОТА ==========
async def main():
    print("🤖 MemCase Бот запущен!")
    print(f"Бот: @{(await bot.get_me()).username}")
    print("Ожидание сообщений...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
