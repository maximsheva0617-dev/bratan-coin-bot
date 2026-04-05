import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json
import os
import time
from datetime import datetime, timedelta
import threading

# =============== ТВОЙ ТОКЕН ===============
TOKEN = "8785871682:AAFvU2KFojj1dvcklj_cCTNht7wqHvcJ8_M"
bot = telebot.TeleBot(TOKEN)

# =============== ДАННЫЕ ПОЛЬЗОВАТЕЛЕЙ ===============
DATA_FILE = "bratan_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

user_data = load_data()

# =============== КОНФИГ ===============
ENERGY_LIMIT = 100
ENERGY_REGEN_RATE = 5  # 5 энергии в минуту
TAP_REWARD = 1

# Бусты
BOOSTS = {
    "semki": {"name": "🫘 Семечки", "price": 500, "effect": "x2 тапа на 1 час", "multiplier": 2, "duration": 3600},
    "pivo": {"name": "🍺 Пиво 'Жигуль'", "price": 1500, "effect": "+50 энергии", "energy": 50},
    "pitbike": {"name": "🛵 Питбайк", "price": 5000, "effect": "Авто-тап 30 мин", "autotap": True, "duration": 1800},
    "kostum": {"name": "👕 Спортивный костюм", "price": 25000, "effect": "x3 тапа навсегда", "multiplier": 3, "forever": True},
    "zhigul": {"name": "🚗 Жигуль", "price": 100000, "effect": "Авто-ферма навсегда", "autotap_forever": True}
}

# =============== ФУНКЦИИ ===============
def init_user(user_id, username):
    if str(user_id) not in user_data:
        user_data[str(user_id)] = {
            "username": username,
            "coins": 0,
            "energy": ENERGY_LIMIT,
            "last_tap": time.time(),
            "last_energy_regen": time.time(),
            "boosts": [],
            "referrals": [],
            "referral_code": str(user_id)[-6:],
            "referred_by": None,
            "autotap_end": 0,
            "multiplier": 1
        }
        save_data(user_data)

def update_energy(user_id):
    user = user_data[str(user_id)]
    now = time.time()
    elapsed = now - user["last_energy_regen"]
    regen = int(elapsed * ENERGY_REGEN_RATE / 60)
    if regen > 0:
        user["energy"] = min(ENERGY_LIMIT, user["energy"] + regen)
        user["last_energy_regen"] = now
        save_data(user_data)

def get_multiplier(user_id):
    user = user_data[str(user_id)]
    mult = 1
    for boost in user.get("boosts", []):
        if boost.get("type") == "kostum" and boost.get("forever"):
            mult = 3
    return mult

# =============== КЛАВИАТУРЫ ===============
def main_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🖱️ ТАПАТЬ", callback_data="tap"),
        InlineKeyboardButton("👤 Мой профиль", callback_data="profile"),
        InlineKeyboardButton("🏪 Магазин", callback_data="shop"),
        InlineKeyboardButton("👥 Рефералы", callback_data="referrals"),
        InlineKeyboardButton("🏆 Топ братанов", callback_data="top")
    )
    return keyboard

# =============== КОМАНДЫ ===============
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    username = message.from_user.first_name or message.from_user.username or "Братан"
    
    init_user(user_id, username)
    
    # Рефералка
    if len(message.text.split()) > 1:
        ref_code = message.text.split()[1]
        for uid, data in user_data.items():
            if data["referral_code"] == ref_code and str(user_id) != uid:
                if not user_data[str(user_id)].get("referred_by"):
                    user_data[str(user_id)]["referred_by"] = uid
                    user_data[uid]["coins"] += 1000
                    user_data[uid]["referrals"].append(str(user_id))
                    save_data(user_data)
                    bot.send_message(uid, f"🎉 Братан! По твоей ссылке зашел новый братан! +1000 монет!")
                break
    
    welcome_text = f"""💎 ДОБРО ПОЖАЛОВАТЬ В БРАТАН КОИН 💎

👊 Здарова, {username}!

Ты зашел в самую пацанскую тапалку тут.
Тут все по понятиям: тапаешь → получаешь монеты.

🖱️ Жми на кнопку ТАПАТЬ
⚡️ У тебя 100 энергии (восстанавливается)
🫘 Покупай бусты в магазине
🚗 Копи на Жигуль!

Погнали, братан! 👊
"""
    bot.send_message(message.chat.id, welcome_text, reply_markup=main_keyboard())

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    username = call.from_user.first_name or "Братан"
    
    init_user(user_id, username)
    update_energy(user_id)
    
    if call.data == "tap":
        user = user_data[str(user_id)]
        if user["energy"] <= 0:
            bot.answer_callback_query(call.id, "⚡️ Нет энергии! Подожди немного, братан!", show_alert=True)
            return
        
        multiplier = get_multiplier(user_id)
        reward = TAP_REWARD * multiplier
        
        user["coins"] += reward
        user["energy"] -= 1
        user["last_tap"] = time.time()
        save_data(user_data)
        
        bot.answer_callback_query(call.id, f"+{reward} BRAT! Осталось {user['energy']} энергии", show_alert=False)
        
        # Обновляем сообщение
        bot.edit_message_text(
            f"🖱️ ТАПАЙ, БРАТАН!\n\n💰 Монет: {user['coins']}\n⚡️ Энергия: {user['energy']}/{ENERGY_LIMIT}\n📈 Множитель: x{multiplier}",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=main_keyboard()
        )
        
    elif call.data == "profile":
        user = user_data[str(user_id)]
        boost_text = "\n".join([b.get("name", b.get("type")) for b in user.get("boosts", [])]) or "Нет"
        
        text = f"""👤 ПРОФИЛЬ БРАТАНА

📛 Имя: {user['username']}
💰 Монет: {user['coins']}
⚡️ Энергия: {user['energy']}/{ENERGY_LIMIT}
📈 Множитель: x{get_multiplier(user_id)}
👥 Привел братанов: {len(user.get('referrals', []))}
🔗 Твоя ссылка: t.me/{bot.get_me().username}?start={user['referral_code']}

🛒 Активные бусты:
{boost_text}
"""
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=main_keyboard())
        
    elif call.data == "shop":
        text = "🏪 МАГАЗИН БРАТАНА\n\n"
        keyboard = InlineKeyboardMarkup(row_width=1)
        
        for boost_id, boost in BOOSTS.items():
            text += f"{boost['name']} - {boost['price']} BRAT\n   💪 {boost['effect']}\n\n"
            keyboard.add(InlineKeyboardButton(f"Купить {boost['name']}", callback_data=f"buy_{boost_id}"))
        
        keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="back"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=keyboard)
        
    elif call.data.startswith("buy_"):
        boost_id = call.data.replace("buy_", "")
        boost = BOOSTS.get(boost_id)
        user = user_data[str(user_id)]
        
        if user["coins"] < boost["price"]:
            bot.answer_callback_query(call.id, f"❌ Не хватает! Нужно {boost['price']} BRAT", show_alert=True)
            return
        
        user["coins"] -= boost["price"]
        
        if boost_id == "semki":
            user["multiplier"] = 2
            duration_text = "1 час"
            # Тут можно добавить таймер на отключение множителя
        elif boost_id == "pivo":
            user["energy"] = min(ENERGY_LIMIT, user["energy"] + 50)
        elif boost_id == "pitbike":
            user["autotap_end"] = time.time() + 1800
        elif boost_id == "kostum":
            user["boosts"].append({"type": "kostum", "name": "Спортивный костюм", "forever": True})
            user["multiplier"] = 3
        elif boost_id == "zhigul":
            user["boosts"].append({"type": "zhigul", "name": "Жигуль", "autotap_forever": True})
        
        save_data(user_data)
        bot.answer_callback_query(call.id, f"✅ Куплено {boost['name']}!", show_alert=True)
        
    elif call.data == "referrals":
        user = user_data[str(user_id)]
        ref_list = []
        for ref_id in user.get("referrals", []):
            if ref_id in user_data:
                ref_list.append(user_data[ref_id].get("username", "Братан"))
        
        ref_text = "\n".join(ref_list) if ref_list else "Пока никого"
        
        text = f"""👥 РЕФЕРАЛКА

🔗 Твоя ссылка:
t.me/{bot.get_me().username}?start={user['referral_code']}

👥 Привел братанов: {len(ref_list)}
💰 За каждого братана получаешь 1000 BRAT

Твои братаны:
{ref_text}
"""
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=main_keyboard())
        
    elif call.data == "top":
        sorted_users = sorted(user_data.items(), key=lambda x: x[1]['coins'], reverse=True)[:10]
        text = "🏆 ТОП БРАТАНОВ 🏆\n\n"
        for i, (uid, data) in enumerate(sorted_users, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            text += f"{medal} {data['username']} - {data['coins']} BRAT\n"
        
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=main_keyboard())
        
    elif call.data == "back":
        user = user_data[str(user_id)]
        bot.edit_message_text(
            f"💎 БРАТАН КОИН 💎\n\n💰 Монет: {user['coins']}\n⚡️ Энергия: {user['energy']}/{ENERGY_LIMIT}",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=main_keyboard()
        )

# =============== ЗАПУСК ===============
print("🔥 Братан Коин запущен! Жми тапать, братан!")
bot.infinity_polling()