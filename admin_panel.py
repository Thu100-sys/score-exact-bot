# ================= ADMIN MENU PRO =================

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.chat.id != ADMIN_CHAT_ID:
        return

    markup = types.InlineKeyboardMarkup()

    markup.add(types.InlineKeyboardButton("📊 Stats", callback_data="stats"))
    markup.add(types.InlineKeyboardButton("📢 Broadcast ALL", callback_data="broadcast_all"))
    markup.add(types.InlineKeyboardButton("🎯 Pending Users", callback_data="pending"))
    markup.add(types.InlineKeyboardButton("👑 VIP Message", callback_data="vip"))
    markup.add(types.InlineKeyboardButton("🔁 Relance", callback_data="relance"))

    bot.send_message(message.chat.id, "🔥 MENU ADMIN PRO :", reply_markup=markup)


# ================= ACTIONS =================

@bot.callback_query_handler(func=lambda call: True)
def admin_actions(call):

    if call.message.chat.id != ADMIN_CHAT_ID:
        return

    data = call.data

    # 📊 STATS
    if data == "stats":
        total_users = len(all_users)
        pending_users = sum(1 for s in user_steps.values() if s == 3)

        bot.send_message(call.message.chat.id,
            f"📊 STATISTIQUES\n\n"
            f"👥 Total users : {total_users}\n"
            f"⏳ En attente : {pending_users}"
        )

    # 📢 BROADCAST ALL
    elif data == "broadcast_all":
        bot.send_message(call.message.chat.id,
            "📢 Utilise la commande :\n/sendall ton message"
        )

    # 🎯 PENDING USERS
    elif data == "pending":
        count = sum(1 for s in user_steps.values() if s == 3)

        bot.send_message(call.message.chat.id,
            f"⏳ Utilisateurs en attente : {count}"
        )

    # 👑 VIP MESSAGE
    elif data == "vip":
        for user in all_users:
            try:
                bot.send_message(user,
                    "👑 OFFRE VIP DISPONIBLE 🔥\n"
                    "👉 Nouveau pronostic en ligne !"
                )
            except:
                pass

        bot.send_message(call.message.chat.id, "✅ Message VIP envoyé")

    # 🔁 RELANCE
    elif data == "relance":
        for user_id, step in user_steps.items():
            if step == 3:
                try:
                    bot.send_message(user_id,
                        "⏳ Dernier rappel 🔥\n"
                        "Envoie ta capture pour validation"
                    )
                except:
                    pass

        bot.send_message(call.message.chat.id, "✅ Relance envoyée")