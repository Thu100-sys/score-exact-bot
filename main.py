import os
import json
import telebot
from telebot import types
from flask import Flask, request

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
        return {"users": {}, "steps": {}, "all_users": [], "validated_count": 0, "referrals": {}, "admin_broadcast": {}}

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

data = load_data()

user_steps = data["steps"]
user_data = data["users"]
all_users = set(data["all_users"])
validated_count = data["validated_count"]
referrals = data.get("referrals", {})
admin_broadcast = data.get("admin_broadcast", {})

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
            "✅ Parfait !\n\n"
            "👉 Pour accéder aux scores VIP :\n\n"
            "1️⃣ Crée un compte authentique sur Paripesa ou 1xbet avec le code promo authentique <b>THU50</b>\n\n"
            "2️⃣ Dépose 3000 FCFA minimum pour activer ton compte\n\n"
            "3️⃣ Envoie capture inscription + dépôt\n\n"
            "⚠️ <b>ID visible obligatoire</b>",
            parse_mode="HTML"
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

    referral_points = referrals.get(chat_id, 0)
    
    bot.send_photo(
        ADMIN_CHAT_ID,
        file_id,
        caption=f"User: {user_data[chat_id].get('name','?')} | ID: {chat_id}\nPoints de partage: {referral_points}",
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

# ================= ADMIN PANEL =================
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.chat.id != ADMIN_CHAT_ID:
        return

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📊 Statistiques Complètes", callback_data="stats_full"))
    markup.add(types.InlineKeyboardButton("📢 Message à TOUS", callback_data="msg_all"))
    markup.add(types.InlineKeyboardButton("⏳ Message aux EN ATTENTE", callback_data="msg_pending"))
    markup.add(types.InlineKeyboardButton("👤 Message PERSONNALISÉ", callback_data="msg_custom"))
    markup.add(types.InlineKeyboardButton("🎯 Voir Utilisateurs", callback_data="list_users"))

    bot.send_message(message.chat.id, "🔥 PANEL ADMIN COMPLET :", reply_markup=markup)

# ================= STATISTIQUES COMPLÈTES =================
@bot.callback_query_handler(func=lambda call: call.data == "stats_full")
def stats_full(call):
    if call.message.chat.id != ADMIN_CHAT_ID:
        return

    total_users = len(all_users)
    pending_users = sum(1 for s in user_steps.values() if s == 3)
    validated_users = sum(1 for s in user_steps.values() if s == 4)
    rejected_users = sum(1 for s in user_steps.values() if s == 0)
    total_referrals = sum(referrals.values())

    stats_text = (
        f"📊 STATISTIQUES COMPLÈTES\n\n"
        f"👥 Total utilisateurs : <b>{total_users}</b>\n"
        f"✅ Validés : <b>{validated_users}</b>\n"
        f"⏳ En attente : <b>{pending_users}</b>\n"
        f"❌ Refusés : <b>{rejected_users}</b>\n"
        f"🎁 Total partages : <b>{total_referrals}</b>\n\n"
        f"📈 Taux de conversion : <b>{round((validated_users/total_users*100) if total_users > 0 else 0)}%</b>"
    )

    bot.send_message(call.message.chat.id, stats_text, parse_mode="HTML")
    bot.answer_callback_query(call.id)

# ================= MESSAGE À TOUS =================
@bot.callback_query_handler(func=lambda call: call.data == "msg_all")
def msg_all_handler(call):
    if call.message.chat.id != ADMIN_CHAT_ID:
        return

    admin_broadcast[str(ADMIN_CHAT_ID)] = {"mode": "all", "type": None}
    data["admin_broadcast"] = admin_broadcast
    save_data()

    bot.send_message(call.message.chat.id,
        "📢 Mode : MESSAGE À TOUS\n\n"
        "Envoie ton message (texte ou photo avec légende)"
    )
    bot.answer_callback_query(call.id)

# ================= MESSAGE AUX EN ATTENTE =================
@bot.callback_query_handler(func=lambda call: call.data == "msg_pending")
def msg_pending_handler(call):
    if call.message.chat.id != ADMIN_CHAT_ID:
        return

    admin_broadcast[str(ADMIN_CHAT_ID)] = {"mode": "pending", "type": None}
    data["admin_broadcast"] = admin_broadcast
    save_data()

    bot.send_message(call.message.chat.id,
        "⏳ Mode : MESSAGE AUX EN ATTENTE\n\n"
        "Envoie ton message (texte ou photo avec légende)"
    )
    bot.answer_callback_query(call.id)

# ================= MESSAGE PERSONNALISÉ =================
@bot.callback_query_handler(func=lambda call: call.data == "msg_custom")
def msg_custom_handler(call):
    if call.message.chat.id != ADMIN_CHAT_ID:
        return

    user_list = "\n".join([f"• {user_data.get(uid, {}).get('name', 'Unknown')} ({uid})" for uid in all_users])
    
    bot.send_message(call.message.chat.id,
        f"👤 UTILISATEURS DISPONIBLES :\n\n{user_list}\n\n"
        "Réponds avec le format : ID,message\n"
        "Exemple : 123456789,Salut !\n\n"
        "(Tu peux aussi envoyer une photo avec légende après)"
    )
    bot.answer_callback_query(call.id)

# ================= VOIR UTILISATEURS =================
@bot.callback_query_handler(func=lambda call: call.data == "list_users")
def list_users_handler(call):
    if call.message.chat.id != ADMIN_CHAT_ID:
        return

    user_list = "\n".join([f"✅ {user_data.get(uid, {}).get('name', 'Unknown')} | ID: {uid}" for uid in all_users])
    
    if not user_list:
        user_list = "Aucun utilisateur"

    bot.send_message(call.message.chat.id,
        f"👥 LISTE DES UTILISATEURS ({len(all_users)})\n\n{user_list}"
    )
    bot.answer_callback_query(call.id)

# ================= RECEVOIR MESSAGES ADMIN =================
@bot.message_handler(func=lambda m: str(m.chat.id) == str(ADMIN_CHAT_ID) and str(m.chat.id) in admin_broadcast)
def admin_send_message(message):
    chat_id = str(message.chat.id)
    broadcast_data = admin_broadcast.get(chat_id, {})
    mode = broadcast_data.get("mode")

    if mode == "all":
        if message.content_type == "text":
            msg = message.text
            for user in all_users:
                try:
                    bot.send_message(user, msg, parse_mode="HTML")
                except:
                    pass
        elif message.content_type == "photo":
            file_id = message.photo[-1].file_id
            caption = message.caption or ""
            for user in all_users:
                try:
                    bot.send_photo(user, file_id, caption=caption, parse_mode="HTML")
                except:
                    pass

        bot.send_message(chat_id, "✅ Message envoyé à TOUS")
        admin_broadcast.pop(chat_id, None)
        data["admin_broadcast"] = admin_broadcast
        save_data()

    elif mode == "pending":
        if message.content_type == "text":
            msg = message.text
            for user_id, step in user_steps.items():
                if step == 3:
                    try:
                        bot.send_message(user_id, msg, parse_mode="HTML")
                    except:
                        pass
        elif message.content_type == "photo":
            file_id = message.photo[-1].file_id
            caption = message.caption or ""
            for user_id, step in user_steps.items():
                if step == 3:
                    try:
                        bot.send_photo(user_id, file_id, caption=caption, parse_mode="HTML")
                    except:
                        pass

        bot.send_message(chat_id, "✅ Message envoyé aux EN ATTENTE")
        admin_broadcast.pop(chat_id, None)
        data["admin_broadcast"] = admin_broadcast
        save_data()

# ================= MESSAGE PERSONNALISÉ (TEXTE) =================
@bot.message_handler(func=lambda m: str(m.chat.id) == str(ADMIN_CHAT_ID) and "," in m.text)
def admin_send_custom(message):
    try:
        parts = message.text.split(",", 1)
        target_id = parts[0].strip()
        msg = parts[1].strip()

        if target_id in all_users:
            bot.send_message(target_id, msg, parse_mode="HTML")
            bot.send_message(message.chat.id, f"✅ Message envoyé à {user_data.get(target_id, {}).get('name', target_id)}")
        else:
            bot.send_message(message.chat.id, "❌ Utilisateur introuvable")
    except:
        bot.send_message(message.chat.id, "❌ Format invalide. Utilise : ID,message")

# ================= MESSAGE PERSONNALISÉ (PHOTO) =================
@bot.message_handler(content_types=['photo'], func=lambda m: str(m.chat.id) == str(ADMIN_CHAT_ID))
def admin_send_custom_photo(message):
    chat_id = str(message.chat.id)
    
    if chat_id in admin_broadcast:
        broadcast_data = admin_broadcast[chat_id]
        mode = broadcast_data.get("mode")
        
        if mode in ["all", "pending"]:
            # Déjà géré dans admin_send_message
            return

    reply_text = message.reply_to_message.text if message.reply_to_message else None
    
    if reply_text and "," in reply_text:
        try:
            parts = reply_text.split(",", 1)
            target_id = parts[0].strip()
            
            file_id = message.photo[-1].file_id
            caption = message.caption or ""

            if target_id in all_users:
                bot.send_photo(target_id, file_id, caption=caption, parse_mode="HTML")
                bot.send_message(message.chat.id, f"✅ Photo envoyée à {user_data.get(target_id, {}).get('name', target_id)}")
            else:
                bot.send_message(message.chat.id, "❌ Utilisateur introuvable")
        except:
            bot.send_message(message.chat.id, "❌ Erreur lors de l'envoi")

# ================= RUN BOT =================
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    
    # Set webhook
    bot.remove_webhook()
    bot.set_webhook(url=f"https://score-exact-bot.onrender.com/webhook")
    
    app.run(host="0.0.0.0", port=port)
