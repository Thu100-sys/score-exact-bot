
import telebot
from telebot import types
import json
import os
import time
from threading import Thread
from keep_alive import keep_alive

# ================= CONFIG =================
TOKEN = "8198100748:AAFaRtHzSyQltiKVlWZ-KSKURaXK5eagTic"
GROUP_LINK = "https://t.me/+qvrpwk_KSJVhMjFk"
ADMIN_CHAT_ID = 1435944368

bot = telebot.TeleBot(TOKEN)

# ================= DATA =================
DATA_FILE = "data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"users": {}, "steps": {}, "all_users": [], "validated_count": 0}

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

data = load_data()

user_steps = data["steps"]
user_data = data["users"]
all_users = set(data["all_users"])
validated_count = data["validated_count"]

# ================= RELANCE AUTO =================
def reminder_loop():
    while True:
        time.sleep(1800)
        for chat_id, step in user_steps.items():
            if step == 3:
                if 'photo_id' not in user_data.get(chat_id, {}):
                    try:
                        bot.send_message(chat_id,
                            "⏳ Tu n’as pas encore envoyé ta preuve.\n\n"
                            "⚠️ Sans validation, pas d’accès aux scores VIP.\n\n"
                            "👉 Envoie ta capture maintenant 💰"
                        )
                    except:
                        pass

Thread(target=reminder_loop, daemon=True).start()

# ================= START =================
@bot.message_handler(commands=['start'])
def start(message):
    chat_id = str(message.chat.id)

    all_users.add(chat_id)
    data["all_users"] = list(all_users)

    bot.send_message(chat_id,
        "🔥 *BIENVENUE SUR SCORE EXACT FIABLE* 🔥\n\n"
        "💰 Accède à des scores exacts ultra fiables.\n"
        "📊 Réservé aux membres sérieux.\n\n"
        "👉 Quel est ton prénom ?",
        parse_mode="Markdown"
    )

    user_steps[chat_id] = 1
    save_data()

# ================= NOM =================
@bot.message_handler(func=lambda m: user_steps.get(str(m.chat.id)) == 1)
def get_name(message):
    chat_id = str(message.chat.id)

    user_data[chat_id] = {"name": message.text}

    bot.send_message(chat_id,
        f"🙌 Merci {message.text}\n\nAs-tu 18 ans ? (OUI/NON)"
    )

    user_steps[chat_id] = 2
    save_data()

# ================= AGE =================
@bot.message_handler(func=lambda m: user_steps.get(str(m.chat.id)) == 2)
def age(message):
    chat_id = str(message.chat.id)

    if message.text.lower() == "oui":
        bot.send_message(chat_id,
            "✅ Parfait !\n\n"
            "👉 Pour accéder aux scores VIP :\n\n"
            "1. Crée un compte (code THU50)\n"
            "2. Dépose 3000 FCFA minimum\n"
            "3. Envoie capture inscription + dépôt\n\n"
            "⚠️ ID visible obligatoire"
        )
        user_steps[chat_id] = 3
    else:
        bot.send_message(chat_id, "❌ Accès refusé (18+ uniquement)")

    save_data()

# ================= PHOTO =================
@bot.message_handler(content_types=['photo'], func=lambda m: user_steps.get(str(m.chat.id)) == 3)
def photo(message):
    chat_id = str(message.chat.id)

    if chat_id not in user_data:
        user_data[chat_id] = {}

    file_id = message.photo[-1].file_id
    user_data[chat_id]['photo_id'] = file_id

    bot.send_message(chat_id, "📸 Capture reçue. Vérification en cours...")

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Valider", callback_data=f"validate_{chat_id}"),
        types.InlineKeyboardButton("❌ Refuser", callback_data=f"reject_{chat_id}")
    )

    bot.send_photo(
        ADMIN_CHAT_ID,
        file_id,
        caption=f"👤 {user_data[chat_id].get('name','Inconnu')}\n🆔 {chat_id}",
        reply_markup=markup
    )

    save_data()

# ================= VALIDATION =================
@bot.callback_query_handler(func=lambda call: call.data.startswith("validate_"))
def validate(call):
    global validated_count

    chat_id = call.data.split("_")[1]

    bot.send_message(chat_id,
        f"🎉 VALIDÉ !\n\n"
        f"🔥 Accède au groupe VIP :\n{GROUP_LINK}\n\n"
        f"⚠️ Reste actif pour les gains"
    )

    validated_count += 1
    data["validated_count"] = validated_count

    user_steps[chat_id] = 4
    save_data()

    bot.answer_callback_query(call.id, "Validé ✅")

# ================= REFUS =================
@bot.callback_query_handler(func=lambda call: call.data.startswith("reject_"))
def reject(call):
    chat_id = call.data.split("_")[1]

    bot.send_message(chat_id,
        "❌ Capture refusée\n\n"
        "👉 ID non visible ou dépôt incorrect\n\n"
        "📸 Renvoie une bonne capture"
    )

    if chat_id in user_data:
        user_data[chat_id].pop('photo_id', None)

    user_steps[chat_id] = 3
    save_data()

    bot.answer_callback_query(call.id, "Refusé ❌")

# ================= BROADCAST =================
@bot.message_handler(commands=['broadcast_all'])
def broadcast(message):
    if message.chat.id != ADMIN_CHAT_ID:
        return

    bot.reply_to(message, "Envoie le message à tous")
    user_steps[str(message.chat.id)] = "broadcast"

@bot.message_handler(func=lambda m: user_steps.get(str(m.chat.id)) == "broadcast")
def send_all(message):
    for user_id in all_users:
        try:
            bot.send_message(user_id, message.text)
        except:
            pass

    bot.reply_to(message, "✅ Envoyé à tous")
    user_steps[str(message.chat.id)] = None

# ================= KEEP ALIVE =================
keep_alive()

# ================= RUN =================
bot.infinity_polling()

