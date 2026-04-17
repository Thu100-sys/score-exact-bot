import os
import json
import telebot
from telebot import types
from flask import Flask, request
from threading import Thread
import time

# ================= ENV =================
TOKEN = os.getenv("TOKEN")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "0"))

bot = telebot.TeleBot(TOKEN)

# ================= FLASK (WEBHOOK) =================
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running 24/7"

@app.route('/webhook', methods=['POST'])
def webhook():
    json_data = request.get_json()
    update = telebot.types.Update.de_json(json_data)
    bot.process_new_updates([update])
    return 'OK', 200

# ================= DATA =================
DATA_FILE = "data.json"

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {"users": {}, "steps": {}, "all_users": [], "validated_count": 0}

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

data = load_data()

user_steps = data["steps"]
user_data = data["users"]
all_users = set(data["all_users"])
validated_count = data["validated_count"]

GROUP_LINK = "https://t.me/+qvrpwk_KSJVhMjFk"

# ================= START =================
@bot.message_handler(commands=['start'])
def start(message):
    chat_id = str(message.chat.id)

    all_users.add(chat_id)
    data["all_users"] = list(all_users)
    save_data()

    bot.send_message(chat_id,
        "🔥 BIENVENUE SUR SCORE EXACT FIABLE 🔥\n\n"
        "💰 Accès VIP scores exacts\n"
        "👉 Quel est ton prénom ?"
    )

    user_steps[chat_id] = 1
    save_data()

# ================= NAME =================
@bot.message_handler(func=lambda m: user_steps.get(str(m.chat.id)) == 1)
def name(message):
    chat_id = str(message.chat.id)

    user_data[chat_id] = {"name": message.text}

    bot.send_message(chat_id,
        f"Merci {message.text} 🙌\nAs-tu 18 ans ? (OUI/NON)"
    )

    user_steps[chat_id] = 2
    save_data()

# ================= AGE =================
@bot.message_handler(func=lambda m: user_steps.get(str(m.chat.id)) == 2)
def age(message):
    chat_id = str(message.chat.id)

    if message.text.lower() == "oui":
        bot.send_message(chat_id,
            "✅ Parfait !\nEnvoie ta capture (inscription + dépôt)"
        )
        user_steps[chat_id] = 3
    else:
        bot.send_message(chat_id, "❌ Accès interdit (18+)")
        user_steps[chat_id] = 0

    save_data()

# ================= PHOTO =================
@bot.message_handler(content_types=['photo'])
def photo(message):
    chat_id = str(message.chat.id)

    if user_steps.get(chat_id) != 3:
        return

    file_id = message.photo[-1].file_id

    user_data[chat_id] = user_data.get(chat_id, {})
    user_data[chat_id]["photo"] = file_id

    bot.send_message(chat_id, "📸 Capture reçue, vérification...")

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Valider", callback_data=f"val_{chat_id}"),
        types.InlineKeyboardButton("❌ Refuser", callback_data=f"rej_{chat_id}")
    )

    bot.send_photo(
        ADMIN_CHAT_ID,
        file_id,
        caption=f"User: {user_data[chat_id].get('name','?')} | ID: {chat_id}",
        reply_markup=markup
    )

    save_data()

# ================= VALIDATE =================
@bot.callback_query_handler(func=lambda call: call.data.startswith("val_"))
def validate(call):
    chat_id = call.data.split("_")[1]

    bot.send_message(chat_id,
        f"🎉 VALIDÉ !\n\n👉 Groupe VIP : {GROUP_LINK}"
    )

    user_steps[chat_id] = 4
    save_data()

    bot.answer_callback_query(call.id)

# ================= REJECT =================
@bot.callback_query_handler(func=lambda call: call.data.startswith("rej_"))
def reject(call):
    chat_id = call.data.split("_")[1]

    bot.send_message(chat_id,
        "❌ Refusé : renvoie une capture correcte avec ID visible"
    )

    user_steps[chat_id] = 3
    save_data()

    bot.answer_callback_query(call.id)

# ================= BROADCAST =================
@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if str(message.chat.id) != str(ADMIN_CHAT_ID):
        return

    msg = message.text.replace("/broadcast", "").strip()

    for user in all_users:
        try:
            bot.send_message(user, msg)
        except:
            pass

    bot.send_message(message.chat.id, "✅ Envoyé à tous")

# ================= RUN BOT =================
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    
    # Set webhook
    bot.remove_webhook()
    bot.set_webhook(url=f"https://score-exact-bot.onrender.com/webhook")
    
    app.run(host="0.0.0.0", port=port)