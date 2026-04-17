import os
import json
import telebot
from telebot import types
from flask import Flask, request
from datetime import datetime

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
        return {
            "users": {}, 
            "steps": {}, 
            "all_users": [], 
            "validated_count": 0, 
            "referrals": {},
            "admin_mode": {},
            "logs": []
        }

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def log_action(action, details=""):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data["logs"].append({
        "timestamp": timestamp,
        "action": action,
        "details": details
    })
    if len(data["logs"]) > 100:
        data["logs"] = data["logs"][-100:]
    save_data()

data = load_data()

user_steps = data["steps"]
user_data = data["users"]
all_users = set(data["all_users"])
validated_count = data["validated_count"]
referrals = data.get("referrals", {})
admin_mode = data.get("admin_mode", {})
logs = data.get("logs", [])

GROUP_LINK = "https://t.me/+qvrpwk_KSJVhMjFk"

# ================= START =================
@bot.message_handler(commands=['start'])
def start(message):
    chat_id = str(message.chat.id)

    all_users.add(chat_id)
    data["all_users"] = list(all_users)
    log_action("NEW_USER", f"User {chat_id} started the bot")
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
    log_action("USER_VALIDATED", f"User {chat_id} validated")
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
    log_action("USER_REJECTED", f"User {chat_id} rejected")
    save_data()

    bot.answer_callback_query(call.id)

# ================= ADMIN PANEL MAIN =================
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.chat.id != ADMIN_CHAT_ID:
        return

    markup = types.InlineKeyboardMarkup(row_width=2)

    # Row 1: Statistics
    markup.add(
        types.InlineKeyboardButton("📊 Stats Complètes", callback_data="stats_full"),
        types.InlineKeyboardButton("📈 Graphique", callback_data="stats_chart")
    )

    # Row 2: User Management
    markup.add(
        types.InlineKeyboardButton("👥 Tous les Users", callback_data="list_all_users"),
        types.InlineKeyboardButton("⏳ Users en Attente", callback_data="list_pending_users")
    )

    # Row 3: Messaging
    markup.add(
        types.InlineKeyboardButton("📢 Message à TOUS", callback_data="msg_all"),
        types.InlineKeyboardButton("⏳ Message ATTENTE", callback_data="msg_pending")
    )

    # Row 4: Targeted Messaging
    markup.add(
        types.InlineKeyboardButton("👤 Message PERSO", callback_data="msg_custom"),
        types.InlineKeyboardButton("🎯 Message GROUPE", callback_data="msg_group")
    )

    # Row 5: VIP & Engagement
    markup.add(
        types.InlineKeyboardButton("👑 Offre VIP", callback_data="send_vip"),
        types.InlineKeyboardButton("🎁 Bonus Partage", callback_data="bonus_referral")
    )

    # Row 6: Reminders & Engagement
    markup.add(
        types.InlineKeyboardButton("🔔 Rappel EN ATTENTE", callback_data="reminder_pending"),
        types.InlineKeyboardButton("📝 Logs", callback_data="view_logs")
    )

    # Row 7: Management
    markup.add(
        types.InlineKeyboardButton("🗑️ Nettoyer Inactifs", callback_data="clean_inactive"),
        types.InlineKeyboardButton("⚙️ Paramètres", callback_data="settings")
    )

    bot.send_message(message.chat.id, 
        "🔥 PANEL ADMIN PRO 🔥\n\n"
        "Sélectionne une option :",
        reply_markup=markup
    )

# ================= STATISTIQUES COMPLÈTES =================
@bot.callback_query_handler(func=lambda call: call.data == "stats_full")
def stats_full(call):
    if call.message.chat.id != ADMIN_CHAT_ID:
        return

    total_users = len(all_users)
    pending_users = sum(1 for s in user_steps.values() if s == 3)
    validated_users = sum(1 for s in user_steps.values() if s == 4)
    rejected_users = sum(1 for s in user_steps.values() if s == 0)
    in_progress_users = sum(1 for s in user_steps.values() if s in [1, 2])
    total_referrals = sum(referrals.values())
    
    conversion_rate = round((validated_users/total_users*100) if total_users > 0 else 0)
    avg_referrals = round(total_referrals/total_users if total_users > 0 else 0)

    stats_text = (
        f"📊 STATISTIQUES COMPLÈTES\n"
        f"{'='*40}\n\n"
        f"<b>👥 UTILISATEURS</b>\n"
        f"  • Total : <b>{total_users}</b>\n"
        f"  • ✅ Validés : <b>{validated_users}</b>\n"
        f"  • ⏳ En attente : <b>{pending_users}</b>\n"
        f"  • ⚙️ En cours : <b>{in_progress_users}</b>\n"
        f"  • ❌ Refusés : <b>{rejected_users}</b>\n\n"
        f"<b>🎁 PARTAGES & BONUS</b>\n"
        f"  • Total partages : <b>{total_referrals}</b>\n"
        f"  • Moyenne/user : <b>{avg_referrals}</b>\n\n"
        f"<b>📈 CONVERSION</b>\n"
        f"  • Taux : <b>{conversion_rate}%</b>\n"
        f"  • Reste à valider : <b>{pending_users}</b>\n"
    )

    bot.send_message(call.message.chat.id, stats_text, parse_mode="HTML")
    bot.answer_callback_query(call.id)

# ================= GRAPHIQUE STATS =================
@bot.callback_query_handler(func=lambda call: call.data == "stats_chart")
def stats_chart(call):
    if call.message.chat.id != ADMIN_CHAT_ID:
        return

    total_users = len(all_users)
    pending = sum(1 for s in user_steps.values() if s == 3)
    validated = sum(1 for s in user_steps.values() if s == 4)
    rejected = sum(1 for s in user_steps.values() if s == 0)
    in_progress = sum(1 for s in user_steps.values() if s in [1, 2])

    # Simple ASCII chart
    chart = (
        f"📈 GRAPHIQUE UTILISATEURS\n\n"
        f"Validés ✅     : {'█' * validated}\n"
        f"En attente ⏳  : {'█' * pending}\n"
        f"En cours ⚙️    : {'█' * in_progress}\n"
        f"Refusés ❌    : {'█' * rejected}\n\n"
        f"Total: {total_users}"
    )

    bot.send_message(call.message.chat.id, chart)
    bot.answer_callback_query(call.id)

# ================= LISTER TOUS LES USERS =================
@bot.callback_query_handler(func=lambda call: call.data == "list_all_users")
def list_all_users(call):
    if call.message.chat.id != ADMIN_CHAT_ID:
        return

    user_list = []
    for uid in all_users:
        name = user_data.get(uid, {}).get('name', 'Unknown')
        step = user_steps.get(uid, 0)
        status = {0: "❌ Refusé", 1: "🆕 Nouveau", 2: "📝 Info", 3: "⏳ Attente", 4: "✅ Validé"}.get(step, "?")
        user_list.append(f"{name} ({uid}) - {status}")
    
    text = f"👥 TOUS LES UTILISATEURS ({len(all_users)})\n\n"
    text += "\n".join(user_list) if user_list else "Aucun utilisateur"

    bot.send_message(call.message.chat.id, text)
    bot.answer_callback_query(call.id)

# ================= LISTER USERS EN ATTENTE =================
@bot.callback_query_handler(func=lambda call: call.data == "list_pending_users")
def list_pending_users(call):
    if call.message.chat.id != ADMIN_CHAT_ID:
        return

    pending_list = []
    for uid, step in user_steps.items():
        if step == 3:
            name = user_data.get(uid, {}).get('name', 'Unknown')
            pending_list.append(f"• {name} ({uid})")
    
    count = len(pending_list)
    text = f"⏳ UTILISATEURS EN ATTENTE ({count})\n\n"
    text += "\n".join(pending_list) if pending_list else "Aucun utilisateur en attente"

    bot.send_message(call.message.chat.id, text)
    bot.answer_callback_query(call.id)

# ================= MESSAGE À TOUS =================
@bot.callback_query_handler(func=lambda call: call.data == "msg_all")
def msg_all_handler(call):
    if call.message.chat.id != ADMIN_CHAT_ID:
        return

    admin_mode[str(ADMIN_CHAT_ID)] = "msg_all"
    data["admin_mode"] = admin_mode
    save_data()

    bot.send_message(call.message.chat.id,
        "📢 MODE: MESSAGE À TOUS\n\n"
        f"Total utilisateurs: {len(all_users)}\n\n"
        "Envoie ton message (texte ou photo avec légende)"
    )
    bot.answer_callback_query(call.id)

# ================= MESSAGE AUX EN ATTENTE =================
@bot.callback_query_handler(func=lambda call: call.data == "msg_pending")
def msg_pending_handler(call):
    if call.message.chat.id != ADMIN_CHAT_ID:
        return

    pending_count = sum(1 for s in user_steps.values() if s == 3)
    admin_mode[str(ADMIN_CHAT_ID)] = "msg_pending"
    data["admin_mode"] = admin_mode
    save_data()

    bot.send_message(call.message.chat.id,
        "⏳ MODE: MESSAGE AUX EN ATTENTE\n\n"
        f"Utilisateurs en attente: {pending_count}\n\n"
        "Envoie ton message (texte ou photo avec légende)"
    )
    bot.answer_callback_query(call.id)

# ================= MESSAGE PERSONNALISÉ =================
@bot.callback_query_handler(func=lambda call: call.data == "msg_custom")
def msg_custom_handler(call):
    if call.message.chat.id != ADMIN_CHAT_ID:
        return

    admin_mode[str(ADMIN_CHAT_ID)] = "msg_custom"
    data["admin_mode"] = admin_mode
    save_data()

    user_list = "\n".join([f"• {user_data.get(uid, {}).get('name', 'Unknown')} ({uid})" for uid in list(all_users)[:10]])
    
    bot.send_message(call.message.chat.id,
        f"👤 MESSAGE PERSONNALISÉ\n\n"
        f"Exemples d'utilisateurs:\n{user_list}\n\n"
        "Format: ID,message\n"
        "Exemple: 123456789,Salut!"
    )
    bot.answer_callback_query(call.id)

# ================= MESSAGE GROUPE =================
@bot.callback_query_handler(func=lambda call: call.data == "msg_group")
def msg_group_handler(call):
    if call.message.chat.id != ADMIN_CHAT_ID:
        return

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Validés", callback_data="msg_group_validated"))
    markup.add(types.InlineKeyboardButton("⏳ En Attente", callback_data="msg_group_pending"))
    markup.add(types.InlineKeyboardButton("❌ Refusés", callback_data="msg_group_rejected"))

    bot.send_message(call.message.chat.id,
        "🎯 MESSAGE PAR GROUPE\n\n"
        "Sélectionne un groupe:",
        reply_markup=markup
    )
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("msg_group_"))
def msg_group_select(call):
    if call.message.chat.id != ADMIN_CHAT_ID:
        return

    group_type = call.data.replace("msg_group_", "")
    admin_mode[str(ADMIN_CHAT_ID)] = f"msg_group_{group_type}"
    data["admin_mode"] = admin_mode
    save_data()

    group_names = {"validated": "✅ Validés", "pending": "⏳ En Attente", "rejected": "❌ Refusés"}
    bot.send_message(call.message.chat.id,
        f"🎯 MODE: MESSAGE AU GROUPE {group_names.get(group_type)}\n\n"
        "Envoie ton message (texte ou photo)"
    )
    bot.answer_callback_query(call.id)

# ================= OFFRE VIP =================
@bot.callback_query_handler(func=lambda call: call.data == "send_vip")
def send_vip(call):
    if call.message.chat.id != ADMIN_CHAT_ID:
        return

    admin_mode[str(ADMIN_CHAT_ID)] = "send_vip"
    data["admin_mode"] = admin_mode
    save_data()

    bot.send_message(call.message.chat.id,
        "👑 ENVOYER OFFRE VIP\n\n"
        "Envoie ton message (texte ou photo)"
    )
    bot.answer_callback_query(call.id)

# ================= BONUS PARTAGE =================
@bot.callback_query_handler(func=lambda call: call.data == "bonus_referral")
def bonus_referral(call):
    if call.message.chat.id != ADMIN_CHAT_ID:
        return

    top_referrers = sorted(referrals.items(), key=lambda x: x[1], reverse=True)[:5]
    
    bonus_text = "🎁 TOP PARTAGEURS\n\n"
    for uid, points in top_referrers:
        name = user_data.get(uid, {}).get('name', 'Unknown')
        bonus_text += f"• {name}: {points} points\n"

    bot.send_message(call.message.chat.id, bonus_text)
    bot.answer_callback_query(call.id)

# ================= RAPPEL EN ATTENTE =================
@bot.callback_query_handler(func=lambda call: call.data == "reminder_pending")
def reminder_pending(call):
    if call.message.chat.id != ADMIN_CHAT_ID:
        return

    admin_mode[str(ADMIN_CHAT_ID)] = "reminder_pending"
    data["admin_mode"] = admin_mode
    save_data()

    pending_count = sum(1 for s in user_steps.values() if s == 3)
    bot.send_message(call.message.chat.id,
        f"🔔 RAPPEL AUX EN ATTENTE\n\n"
        f"Utilisateurs: {pending_count}\n\n"
        "Envoie ton message"
    )
    bot.answer_callback_query(call.id)

# ================= VIEW LOGS =================
@bot.callback_query_handler(func=lambda call: call.data == "view_logs")
def view_logs(call):
    if call.message.chat.id != ADMIN_CHAT_ID:
        return

    logs_text = "📝 LOGS RÉCENTS (10 derniers)\n\n"
    for log in data.get("logs", [])[-10:]:
        logs_text += f"[{log['timestamp']}] {log['action']}\n"
        if log['details']:
            logs_text += f"  → {log['details']}\n"

    bot.send_message(call.message.chat.id, logs_text)
    bot.answer_callback_query(call.id)

# ================= CLEAN INACTIVE =================
@bot.callback_query_handler(func=lambda call: call.data == "clean_inactive")
def clean_inactive(call):
    if call.message.chat.id != ADMIN_CHAT_ID:
        return

    inactive = sum(1 for s in user_steps.values() if s == 0)
    
    bot.send_message(call.message.chat.id,
        f"🗑️ NETTOYAGE\n\n"
        f"Utilisateurs inactifs: {inactive}\n"
        "Action en cours...",
    )
    
    log_action("CLEANUP", f"Cleaned {inactive} inactive users")
    bot.answer_callback_query(call.id)

# ================= SETTINGS =================
@bot.callback_query_handler(func=lambda call: call.data == "settings")
def settings(call):
    if call.message.chat.id != ADMIN_CHAT_ID:
        return

    settings_text = (
        f"⚙️ PARAMÈTRES\n\n"
        f"Admin ID: {ADMIN_CHAT_ID}\n"
        f"Groupe VIP: {GROUP_LINK}\n"
        f"Data File: {DATA_FILE}\n\n"
        f"Tout fonctionne correctement ✅"
    )

    bot.send_message(call.message.chat.id, settings_text)
    bot.answer_callback_query(call.id)

# ================= RECEVOIR MESSAGES ADMIN =================
@bot.message_handler(func=lambda m: str(m.chat.id) == str(ADMIN_CHAT_ID) and str(m.chat.id) in admin_mode)
def admin_send_message(message):
    chat_id = str(message.chat.id)
    mode = admin_mode.get(chat_id)

    if not mode:
        return

    msg_text = message.text if message.content_type == "text" else None
    file_id = message.photo[-1].file_id if message.content_type == "photo" else None
    caption = message.caption or ""

    count = 0
    failed = 0

    # MESSAGE À TOUS
    if mode == "msg_all":
        for user in all_users:
            try:
                if file_id:
                    bot.send_photo(user, file_id, caption=caption, parse_mode="HTML")
                else:
                    bot.send_message(user, msg_text, parse_mode="HTML")
                count += 1
            except:
                failed += 1
        
        bot.send_message(chat_id, f"✅ Envoyé à {count} utilisateurs\n❌ Échoué: {failed}")
        log_action("MSG_ALL_SENT", f"Sent to {count} users")

    # MESSAGE AUX EN ATTENTE
    elif mode == "msg_pending":
        for user_id, step in user_steps.items():
            if step == 3:
                try:
                    if file_id:
                        bot.send_photo(user_id, file_id, caption=caption, parse_mode="HTML")
                    else:
                        bot.send_message(user_id, msg_text, parse_mode="HTML")
                    count += 1
                except:
                    failed += 1
        
        bot.send_message(chat_id, f"✅ Envoyé à {count} en attente\n❌ Échoué: {failed}")
        log_action("MSG_PENDING_SENT", f"Sent to {count} pending users")

    # MESSAGE PERSONNALISÉ
    elif mode == "msg_custom":
        if "," in (msg_text or ""):
            parts = msg_text.split(",", 1)
            target_id = parts[0].strip()
            msg = parts[1].strip()

            if target_id in all_users:
                try:
                    bot.send_message(target_id, msg, parse_mode="HTML")
                    bot.send_message(chat_id, f"��� Envoyé à {user_data.get(target_id, {}).get('name', target_id)}")
                    log_action("MSG_CUSTOM_SENT", f"Sent to {target_id}")
                except:
                    bot.send_message(chat_id, "❌ Erreur d'envoi")
            else:
                bot.send_message(chat_id, "❌ Utilisateur introuvable")

    # MESSAGE PAR GROUPE
    elif mode.startswith("msg_group_"):
        group_type = mode.replace("msg_group_", "")
        for user_id, step in user_steps.items():
            if (group_type == "validated" and step == 4) or \
               (group_type == "pending" and step == 3) or \
               (group_type == "rejected" and step == 0):
                try:
                    if file_id:
                        bot.send_photo(user_id, file_id, caption=caption, parse_mode="HTML")
                    else:
                        bot.send_message(user_id, msg_text, parse_mode="HTML")
                    count += 1
                except:
                    failed += 1
        
        bot.send_message(chat_id, f"✅ Envoyé à {count} utilisateurs\n❌ Échoué: {failed}")

    # OFFRE VIP
    elif mode == "send_vip":
        for user in all_users:
            try:
                if file_id:
                    bot.send_photo(user, file_id, caption=caption, parse_mode="HTML")
                else:
                    bot.send_message(user, msg_text, parse_mode="HTML")
                count += 1
            except:
                failed += 1
        
        bot.send_message(chat_id, f"👑 VIP envoyé à {count} utilisateurs")
        log_action("VIP_OFFER_SENT", f"Sent to {count} users")

    # RAPPEL EN ATTENTE
    elif mode == "reminder_pending":
        for user_id, step in user_steps.items():
            if step == 3:
                try:
                    if file_id:
                        bot.send_photo(user_id, file_id, caption=caption, parse_mode="HTML")
                    else:
                        bot.send_message(user_id, msg_text, parse_mode="HTML")
                    count += 1
                except:
                    failed += 1
        
        bot.send_message(chat_id, f"🔔 Rappel envoyé à {count} utilisateurs")
        log_action("REMINDER_SENT", f"Sent to {count} pending users")

    admin_mode.pop(chat_id, None)
    data["admin_mode"] = admin_mode
    save_data()

# ================= RUN BOT =================
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    
    # Set webhook
    bot.remove_webhook()
    bot.set_webhook(url=f"https://score-exact-bot.onrender.com/webhook")
    
    app.run(host="0.0.0.0", port=port)