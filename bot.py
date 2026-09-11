import os
import asyncio
import logging
import random
import time
import socket
import sys
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import RPCError
from telethon.tl.functions.payments import GetPaymentFormRequest, SendStarsFormRequest
from telethon.tl.types import InputInvoiceStarGift, InputUser, TextWithEntities
from telethon.tl.functions import PingRequest

# ==================== НАСТРОЙКИ ====================
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID_STR = os.getenv("GROUP_ID")
GROUP_ID = int(GROUP_ID_STR) if GROUP_ID_STR and GROUP_ID_STR.strip() else None
SPAM_LIMIT = int(os.getenv("SPAM_LIMIT", 3))

API_ID = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH")
PHONE = os.getenv("PHONE")
SESSION_STRING = os.getenv("SESSION_STRING", "")

if not BOT_TOKEN:
    print("❌ Токен бота не найден!")
    exit(1)

if not API_ID or not API_HASH:
    print("❌ Не заполнены API_ID или API_HASH!")
    exit(1)

if not SESSION_STRING:
    print("❌ Не заполнен SESSION_STRING!")
    print("   Запусти get_session.py локально чтобы получить его")
    exit(1)

# ===================================================

logging.getLogger("telethon").setLevel(logging.WARNING)
logging.getLogger("aiogram").setLevel(logging.WARNING)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN, request_timeout=60)
dp = Dispatcher()
user_spin_times = {}

# Telethon через StringSession (для хостинга)
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH, connection_retries=10, retry_delay=3)
user_prizes = {}

# ==================== GIFT ID ====================

GIFT_IDS = {
    "❤️": 5170145012310081615,
    "🧸": 5170233102089322756,
    "🎁": 5170250947678437525,
    "🎂": 5170144170496491616,
    "🚀": 5170564780938756245,
}

# ==================== КАРТА ====================

SLOT_MAP = {
    1: ["🤞", "🤞", "🤞"], 2: ["🍒", "🤞", "🤞"], 3: ["🍋", "🤞", "🤞"], 4: ["7️⃣", "🤞", "🤞"],
    5: ["🤞", "🍒", "🤞"], 6: ["🍒", "🍒", "🤞"], 7: ["🍋", "🍒", "🤞"], 8: ["7️⃣", "🍒", "🤞"],
    9: ["🤞", "🍋", "🤞"], 10: ["🍒", "🍋", "🤞"], 11: ["🍋", "🍋", "🤞"], 12: ["7️⃣", "🍋", "🤞"],
    13: ["🤞", "7️⃣", "🤞"], 14: ["🍒", "7️⃣", "🤞"], 15: ["🍋", "7️⃣", "🤞"], 16: ["7️⃣", "7️⃣", "🤞"],
    17: ["🤞", "🤞", "🍒"], 18: ["🍒", "🤞", "🍒"], 19: ["🍋", "🤞", "🍒"], 20: ["7️⃣", "🤞", "🍒"],
    21: ["🤞", "🍒", "🍒"], 22: ["🍒", "🍒", "🍒"], 23: ["🍋", "🍒", "🍒"], 24: ["7️⃣", "🍒", "🍒"],
    25: ["🤞", "🍋", "🍒"], 26: ["🍒", "🍋", "🍒"], 27: ["🍋", "🍋", "🍒"], 28: ["7️⃣", "🍋", "🍒"],
    29: ["🤞", "7️⃣", "🍒"], 30: ["🍒", "7️⃣", "🍒"], 31: ["🍋", "7️⃣", "🍒"], 32: ["7️⃣", "7️⃣", "🍒"],
    33: ["🤞", "🤞", "🍋"], 34: ["🍒", "🤞", "🍋"], 35: ["🍋", "🤞", "🍋"], 36: ["7️⃣", "🤞", "🍋"],
    37: ["🤞", "🍒", "🍋"], 38: ["🍒", "🍒", "🍋"], 39: ["🍋", "🍒", "🍋"], 40: ["7️⃣", "🍒", "🍋"],
    41: ["🤞", "🍋", "🍋"], 42: ["🍒", "🍋", "🍋"], 43: ["🍋", "🍋", "🍋"], 44: ["7️⃣", "🍋", "🍋"],
    45: ["🤞", "7️⃣", "🍋"], 46: ["🍒", "7️⃣", "🍋"], 47: ["🍋", "7️⃣", "🍋"], 48: ["7️⃣", "7️⃣", "🍋"],
    49: ["🤞", "🤞", "7️⃣"], 50: ["🍒", "🤞", "7️⃣"], 51: ["🍋", "🤞", "7️⃣"], 52: ["7️⃣", "🤞", "7️⃣"],
    53: ["🤞", "🍒", "7️⃣"], 54: ["🍒", "🍒", "7️⃣"], 55: ["🍋", "🍒", "7️⃣"], 56: ["7️⃣", "🍒", "7️⃣"],
    57: ["🤞", "🍋", "7️⃣"], 58: ["🍒", "🍋", "7️⃣"], 59: ["🍋", "🍋", "7️⃣"], 60: ["7️⃣", "🍋", "7️⃣"],
    61: ["🤞", "7️⃣", "7️⃣"], 62: ["🍒", "7️⃣", "7️⃣"], 63: ["🍋", "7️⃣", "7️⃣"], 64: ["7️⃣", "7️⃣", "7️⃣"],
}

# ==================== ФУНКЦИИ ====================

def get_combination(value: int) -> list:
    return SLOT_MAP.get(value, ["❓", "❓", "❓"])

def count_sevens(combo: list) -> int:
    return combo.count("7️⃣")

def count_bars(combo: list) -> int:
    return combo.count("🤞")

def get_result_message(sevens: int, bars: int) -> dict:
    if sevens == 3:
        return {"title": "🎉 ДЖЕКПОТ! 🎉", "message": "7️⃣7️⃣7️⃣! ТЫ ВЫИГРАЛ ГЛАВНЫЙ ПРИЗ! 🏆", "is_jackpot": True}
    if bars == 3:
        return {"title": "🔥 ТРИ BAR!", "message": "🤞🤞🤞! КРУТАЯ КОМБИНАЦИЯ! 🎯", "is_jackpot": False}
    if sevens == 2:
        return {"title": "😱 ПОЧТИ ДЖЕКПОТ!", "message": "2 семерки из 3! Еще одна и был бы джекпот! 🍀", "is_jackpot": False}
    if bars == 2:
        return {"title": "💪 ДВА BAR!", "message": "2 BAR из 3! Отличная комбинация! 🎯", "is_jackpot": False}
    if sevens == 1:
        return {"title": "🍀 ОДНА СЕМЕРКА!", "message": "1 семерка из 3! Ты почти выиграл! 💪", "is_jackpot": False}
    if bars == 1:
        return {"title": "🎯 ОДИН BAR!", "message": "1 BAR из 3! Неплохо, но нужно больше! 💪", "is_jackpot": False}
    if sevens > 0 and bars > 0:
        return {"title": "🔥 СЕМЕРКА + BAR!", "message": f"{sevens} семерки и {bars} BAR! Круто! 🎯", "is_jackpot": False}
    lose_phrases = [
        "😅 0 семерок и 0 BAR... Попробуй еще раз!",
        "🍀 Удача любит настойчивых! Продолжай!",
        "😉 Попробуй еще! Удача ждет!",
        "🌟 Фортуна отворачивается, но она вернется!",
        "💪 Не сдавайся! Следующий раз будет твоим!",
        "🎯 Тренируй удачу! Крути еще!",
        "🔥 Разогрев окончен! Теперь точно будет джекпот!",
        "🎰 Продолжай крутить!",
    ]
    return {"title": "😅 НЕ ПОВЕЗЛО", "message": random.choice(lose_phrases), "is_jackpot": False}

def format_combo(combo: list) -> str:
    return f"🎰 {' '.join(combo)} 🎰"

# ==================== ИГРОВОЕ ПОЛЕ ====================

PRIZE_CATEGORIES = {
    "❤️": {"name": "Сердечко", "emoji": "❤️", "price": 15},
    "🧸": {"name": "Мишка", "emoji": "🧸", "price": 15},
    "🎁": {"name": "Подарок", "emoji": "🎁", "price": 25},
    "🎂": {"name": "Тортик", "emoji": "🎂", "price": 50},
    "🚀": {"name": "Ракета", "emoji": "🚀", "price": 50},
}

def generate_prize_field() -> dict:
    field = {}
    prize_pool = []
    prize_pool.extend(["❤️"] * 35)
    prize_pool.extend(["🧸"] * 35)
    prize_pool.extend(["🎁"] * 20)
    prize_pool.extend(["🎂"] * 5)
    prize_pool.extend(["🚀"] * 5)
    random.shuffle(prize_pool)
    for i in range(7):
        for j in range(7):
            cell_id = f"{i}_{j}"
            category = random.choice(prize_pool)
            field[cell_id] = {
                "category": category,
                "price": PRIZE_CATEGORIES[category]["price"],
                "emoji": PRIZE_CATEGORIES[category]["emoji"],
                "name": PRIZE_CATEGORIES[category]["name"],
                "row": i,
                "col": j
            }
    return field

def create_hidden_keyboard(field: dict) -> InlineKeyboardMarkup:
    keyboard = []
    for i in range(7):
        row = []
        for j in range(7):
            cell_id = f"{i}_{j}"
            row.append(InlineKeyboardButton(text="❓", callback_data=f"prize_{cell_id}"))
        keyboard.append(row)
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def create_revealed_keyboard(field: dict) -> InlineKeyboardMarkup:
    keyboard = []
    for i in range(7):
        row = []
        for j in range(7):
            cell_id = f"{i}_{j}"
            data = field[cell_id]
            row.append(InlineKeyboardButton(text=f"{data['emoji']}", callback_data=f"revealed_{cell_id}"))
        keyboard.append(row)
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# ==================== ОТПРАВКА ПОДАРКА ====================

async def send_star_gift(user_id: int, gift_id: int, stars_amount: int) -> bool:
    try:
        if not client.is_connected():
            await client.connect()
        recipient = await client.get_entity(user_id)
        input_peer = await client.get_input_entity(recipient)
        msg = TextWithEntities(text="🎁 Поздравляю с выигрышем в казино! 🎰", entities=[])
        invoice = InputInvoiceStarGift(peer=input_peer, gift_id=gift_id, message=msg)
        form = await client(GetPaymentFormRequest(invoice=invoice))
        await client(SendStarsFormRequest(form_id=form.form_id, invoice=invoice))
        logger.info(f"✅ Подарок (ID: {gift_id}) отправлен пользователю {user_id}")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка отправки: {e}")
        return False

# ==================== ОБРАБОТЧИКИ ====================

@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer(
        "🎰 **Добро пожаловать в казино!**\n\n"
        "🎯 Отправь **🎰** с клавиатуры в чат\n"
        "🏆 Если выпадет **7️⃣7️⃣7️⃣** — откроется поле с призами!\n"
        "🎁 Выбери клетку и получи РЕАЛЬНЫЙ подарок!\n\n"
        "💰 **Цены призов:**\n"
        "❤️ Сердечко — 15 Stars\n"
        "🧸 Мишка — 15 Stars\n"
        "🎁 Подарок — 25 Stars\n"
        "🎂 Тортик — 50 Stars\n"
        "🚀 Ракета — 50 Stars\n\n"
        "📊 **Шансы выпадения:**\n"
        "❤️ Сердечко — 35%\n"
        "🧸 Мишка — 35%\n"
        "🎁 Подарок — 20%\n"
        "🎂 Тортик — 5%\n"
        "🚀 Ракета — 5%\n\n"
        "🍀 Удачи!"
    )

@dp.message(Command("spin"))
async def spin_command(message: types.Message):
    if GROUP_ID and message.chat.id != GROUP_ID:
        await message.answer("❌ Бот работает только в группе!")
        return
    await process_spin(message.from_user.id, message.chat.id, message)

@dp.callback_query(lambda c: c.data and c.data.startswith("prize_"))
async def prize_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    username = callback.from_user.username
    if user_id not in user_prizes:
        await callback.answer("❌ У тебя нет активного приза!")
        return
    prize_data = user_prizes[user_id]
    field = prize_data["field"]
    cell_id = callback.data.replace("prize_", "")
    if cell_id in prize_data["opened"]:
        await callback.answer("❌ Эта клетка уже открыта!")
        return
    cell_data = field[cell_id]
    prize_data["opened"].append(cell_id)
    prize_amount = cell_data["price"]
    prize_emoji = cell_data["emoji"]
    prize_name = cell_data["name"]
    gift_id = GIFT_IDS.get(prize_emoji)
    if not gift_id:
        await callback.answer("❌ Ошибка: неизвестный подарок!")
        return
    revealed_keyboard = create_revealed_keyboard(field)
    user_mention = f"@{username}" if username else callback.from_user.first_name
    await callback.message.edit_text(
        f"🎉 ДЖЕКПОТ!\n"
        f"7️⃣7️⃣7️⃣! ТЫ ВЫИГРАЛ ГЛАВНЫЙ ПРИЗ!\n\n"
        f"{user_mention}, ты выбрал клетку!\n"
        f"{prize_emoji} {prize_name} — {prize_amount} Stars\n\n"
        f"⏳ Отправляем подарок...",
        reply_markup=revealed_keyboard
    )
    await callback.answer(f"{prize_emoji} {prize_name}! +{prize_amount} Stars!", show_alert=True)
    success = await send_star_gift(user_id, gift_id, prize_amount)
    if success:
        await bot.send_message(
            callback.message.chat.id,
            f"🎉 {user_mention}, подарок отправлен!\n\n"
            f"{prize_emoji} {prize_name}\n"
            f"💰 {prize_amount} Stars\n\n"
            f"Проверь свои подарки в профиле Telegram!\n"
            f"[🎁 DGK Gamba](https://t.me/dgkgamba)",
            parse_mode="Markdown",
            disable_web_page_preview=True
        )
    else:
        await bot.send_message(
            callback.message.chat.id,
            f"❌ **Ошибка отправки подарка!**\n\n"
            f"{user_mention}, попробуй позже.\n"
            f"[🎁 DGK Gamba](https://t.me/dgkgamba)",
            parse_mode="Markdown",
            disable_web_page_preview=True
        )
    del user_prizes[user_id]

@dp.message()
async def handle_all(message: types.Message):
    if GROUP_ID and message.chat.id != GROUP_ID:
        return
    if message.text and message.text.startswith('/'):
        return
    if message.dice and message.dice.emoji == "🎰":
        dice_value = message.dice.value
        logger.info(f"🎰 Значение: {dice_value}")
        combo = get_combination(dice_value)
        sevens = count_sevens(combo)
        bars = count_bars(combo)
        result = get_result_message(sevens, bars)
        if result["is_jackpot"]:
            field = generate_prize_field()
            user_prizes[message.from_user.id] = {"field": field, "opened": []}
            keyboard = create_hidden_keyboard(field)
            combo_display = format_combo(combo)
            await message.reply(
                f"🎉 ДЖЕКПОТ!\n"
                f"{combo_display}\n"
                f"{result['title']}\n"
                f"{result['message']}\n\n"
                f"Выбери клетку на поле 7x7!\n"
                f"Нажми на любую клетку и получи РЕАЛЬНЫЙ подарок!\n\n"
                f"🧸 Мишка — 15 Stars\n"
                f"❤️ Сердечко — 15 Stars\n"
                f"🎁 Подарок — 25 Stars\n"
                f"🎂 Тортик — 50 Stars\n"
                f"🚀 Ракета — 50 Stars",
                reply_markup=keyboard
            )
        else:
            await message.reply(f"{result['title']}\n{result['message']}")
        return
    if message.text and '🎰' in message.text:
        await process_spin(message.from_user.id, message.chat.id, message)

async def process_spin(user_id: int, chat_id: int, source_message):
    current_time = time.time()
    if user_id in user_spin_times:
        if current_time - user_spin_times[user_id] < SPAM_LIMIT:
            wait_time = int(SPAM_LIMIT - (current_time - user_spin_times[user_id]))
            await bot.send_message(chat_id, f"⏳ Подожди {wait_time} сек!")
            return
    user_spin_times[user_id] = current_time
    try:
        sent = await bot.send_dice(chat_id=chat_id, emoji="🎰")
        dice_value = sent.dice.value
        logger.info(f"🎰 Значение: {dice_value}")
        combo = get_combination(dice_value)
        sevens = count_sevens(combo)
        bars = count_bars(combo)
        result = get_result_message(sevens, bars)
        if result["is_jackpot"]:
            field = generate_prize_field()
            user_prizes[user_id] = {"field": field, "opened": []}
            keyboard = create_hidden_keyboard(field)
            combo_display = format_combo(combo)
            await bot.send_message(
                chat_id,
                f"🎉 ДЖЕКПОТ!\n"
                f"{combo_display}\n"
                f"{result['title']}\n"
                f"{result['message']}\n\n"
                f"Выбери клетку на поле 7x7!\n"
                f"Нажми на любую клетку и получи РЕАЛЬНЫЙ подарок!\n\n"
                f"🧸 Мишка — 15 Stars\n"
                f"❤️ Сердечко — 15 Stars\n"
                f"🎁 Подарок — 25 Stars\n"
                f"🎂 Тортик — 50 Stars\n"
                f"🚀 Ракета — 50 Stars",
                reply_markup=keyboard
            )
        else:
            await bot.send_message(chat_id, f"{result['title']}\n{result['message']}")
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await bot.send_message(chat_id, "❌ Ошибка!")

# ==================== ЗАПУСК ====================

async def main():
    print("\n" + "="*50)
    print("🎰 БОТ-КАЗИНО (HOSTING MODE)")
    print("="*50)
    print("✅ ТОЛЬКО 7️⃣7️⃣7️⃣ = ДЖЕКПОТ!")
    print("✅ StringSession (для хостинга)")
    print("✅ Работает на Linux и Windows")
    print("="*50)
    print("💰 Цены призов:")
    print("   ❤️ Сердечко — 15 Stars (35%)")
    print("   🧸 Мишка — 15 Stars (35%)")
    print("   🎁 Подарок — 25 Stars (20%)")
    print("   🎂 Тортик — 50 Stars (5%)")
    print("   🚀 Ракета — 50 Stars (5%)")
    print("="*50)
    print("🔗 ССЫЛКА: DGK Gamba → https://t.me/dgkgamba")
    print("="*50 + "\n")
    
    print("📱 Подключение к Telegram...")
    await client.connect()
    me = await client.get_me()
    print(f"✅ Аккаунт: @{me.username} (ID: {me.id})")
    print("="*50 + "\n")
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    while True:
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            print("\n👋 Бот остановлен")
            break
        except Exception as e:
            logger.error(f"❌ Ошибка: {e}")
            logger.info("🔄 Перезапуск через 5 секунд...")
            time.sleep(5)
            continue
        break