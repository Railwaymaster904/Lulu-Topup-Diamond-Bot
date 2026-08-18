from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import ContextTypes, ConversationHandler
from datetime import datetime
import io
import database as db
from keyboards import *
from states import UserStates, AdminStates
from config import ADMINS, CHANNEL_ID, CHANNEL_LINK
import os

# ==================== HELPER FUNCTIONS ====================

async def get_lang(user_id):
    user = await db.get_user(user_id)
    return user["language"] if user and user["language"] else "bn"

def t(key, lang="bn"):
    """Simple translation helper"""
    texts = {
        "welcome": {
            "bn": "🎮 স্বাগতম! Free Fire Top-Up বটে\n\n💰 আপনার ব্যালেন্স: ৳{balance}\n🎖 লেভেল: {level}\n\nনিচ থেকে অপশন বেছে নিন:",
            "en": "🎮 Welcome to Free Fire Top-Up Bot!\n\n💰 Your Balance: ৳{balance}\n🎖 Level: {level}\n\nChoose an option below:"
        },
        "banned": {
            "bn": "🚫 আপনাকে ব্যান করা হয়েছে।\nকারণ: {reason}\n\nসাপোর্টে যোগাযোগ করুন।",
            "en": "🚫 You are banned.\nReason: {reason}\n\nContact support."
        },
        "maintenance": {
            "bn": "🔧 বট বর্তমানে মেইনটেনেন্স মোডে আছে।\nকিছুক্ষণ পর আবার চেষ্টা করুন।",
            "en": "🔧 Bot is under maintenance.\nPlease try again later."
        },
        "force_join": {
            "bn": "⚠️ বট ব্যবহার করতে আমাদের চ্যানেলে জয়েন করতে হবে।\n\nনিচের বাটনে ক্লিক করে জয়েন করুন, তারপর ✅ I Have Joined বাটনে চাপুন।",
            "en": "⚠️ To use this bot you must join our channel.\n\nClick the button below to join, then press ✅ I Have Joined."
        },
        "not_joined": {
            "bn": "❌ আপনি এখনো চ্যানেলে জয়েন করেননি।\nঅনুগ্রহ করে আগে জয়েন করুন।",
            "en": "❌ You have not joined the channel yet.\nPlease join first."
        },
        "no_offers": {
            "bn": "😔 এখন কোনো অফার নেই।",
            "en": "😔 No offers available right now."
        },
        "enter_uid": {
            "bn": "💎 {name}\n\n💰 মূল্য: ৳{price}\n⚡ ডেলিভারি: {delivery}\n\nঅনুগ্রহ করে আপনার Free Fire UID লিখুন:",
            "en": "💎 {name}\n\n💰 Price: ৳{price}\n⚡ Delivery: {delivery}\n\nPlease enter your Free Fire UID:"
        },
        "low_balance": {
            "bn": "❌ আপনার ব্যালেন্স অপর্যাপ্ত!\nপ্রয়োজন: ৳{need}\nআপনার ব্যালেন্স: ৳{balance}\n\nআগে Deposit করুন।",
            "en": "❌ Insufficient balance!\nRequired: ৳{need}\nYour Balance: ৳{balance}\n\nPlease Deposit first."
        },
        "order_confirm": {
            "bn": "📦 অর্ডার কনফার্মেশন\n\n💎 {name}\n💰 মূল্য: ৳{price}\n🆔 UID: {uid}\n⚡ ডেলিভারি: {delivery}\n\nঅর্ডার করতে চাও?",
            "en": "📦 Order Confirmation\n\n💎 {name}\n💰 Price: ৳{price}\n🆔 UID: {uid}\n⚡ Delivery: {delivery}\n\nConfirm your order?"
        },
        "order_created": {
            "bn": "✅ অর্ডার সফলভাবে তৈরি হয়েছে!\n\n📦 Order ID: `{order_id}`\n💎 {name}\n🆔 UID: {uid}\n💰 Amount: ৳{price}\n⏳ Status: Pending\n\nঅ্যাডমিন শীঘ্রই প্রসেস করবে।",
            "en": "✅ Order Created Successfully!\n\n📦 Order ID: `{order_id}`\n💎 {name}\n🆔 UID: {uid}\n💰 Amount: ৳{price}\n⏳ Status: Pending\n\nAdmin will process it soon."
        }
    }
    return texts.get(key, {}).get(lang, texts.get(key, {}).get("bn", key))


async def is_user_banned(user_id):
    user = await db.get_user(user_id)
    return user and user["is_banned"] == 1


async def check_maintenance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    maintenance = await db.get_setting("maintenance_mode")
    if str(maintenance).lower() == "true":
        lang = await get_lang(update.effective_user.id)
        text = t("maintenance", lang)
        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(text)
        else:
            await update.message.reply_text(text)
        return True
    return False


async def check_force_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    force = await db.get_setting("force_join")
    if str(force).lower() != "true":
        return True  # Force join বন্ধ থাকলে পাস

    user_id = update.effective_user.id
    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        if member.status in ["member", "administrator", "creator"]:
            return True
    except:
        pass

    lang = await get_lang(user_id)
    text = t("force_join", lang)
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, reply_markup=force_join_keyboard())
    else:
        await update.message.reply_text(text, reply_markup=force_join_keyboard())
    return False


async def admin_only(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await db.is_admin(user_id):
        if update.callback_query:
            await update.callback_query.answer("আপনার অনুমতি নেই!", show_alert=True)
        else:
            await update.message.reply_text("আপনার অনুমতি নেই!")
        return False
    return True


# ==================== START & LANGUAGE & JOIN ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    referred_by = None

    if context.args and context.args[0].startswith("ref"):
        try:
            referred_by = int(context.args[0].replace("ref", ""))
        except:
            pass

    await db.add_user(user.id, user.username, user.full_name, referred_by)

    if await is_user_banned(user.id):
        user_data = await db.get_user(user.id)
        reason = user_data["ban_reason"] or "No reason"
        lang = await get_lang(user.id)
        await update.message.reply_text(t("banned", lang).format(reason=reason))
        return

    if await check_maintenance(update, context):
        return

    # Force Join Check
    if not await check_force_join(update, context):
        return

    # Language select if first time
    user_data = await db.get_user(user.id)
    if not user_data["language"] or user_data["language"] == "bn":
        # ডিফল্ট বাংলা, চাইলে চেঞ্জ করতে পারবে
        pass

    lang = await get_lang(user.id)
    balance = user_data["balance"] if user_data else 0
    level = user_data["level"] if user_data else 0

    text = t("welcome", lang).format(balance=f"{balance:.2f}", level=level)
    await update.message.reply_text(text, reply_markup=main_menu_keyboard(lang))


async def check_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        if member.status in ["member", "administrator", "creator"]:
            lang = await get_lang(user_id)
            user_data = await db.get_user(user_id)
            text = t("welcome", lang).format(balance=f"{user_data['balance']:.2f}", level=user_data['level'])
            await query.edit_message_text(text, reply_markup=main_menu_keyboard(lang))
            return
    except:
        pass

    lang = await get_lang(user_id)
    await query.edit_message_text(t("not_joined", lang), reply_markup=force_join_keyboard())


async def change_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🌐 Select Language / ভাষা নির্বাচন করুন:", reply_markup=language_keyboard())


async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data.split("_")[1]  # bn or en
    await db.set_language(query.from_user.id, lang)

    user_data = await db.get_user(query.from_user.id)
    text = t("welcome", lang).format(balance=f"{user_data['balance']:.2f}", level=user_data['level'])
    await query.edit_message_text(text, reply_markup=main_menu_keyboard(lang))


async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if await is_user_banned(query.from_user.id):
        return
    if await check_maintenance(update, context):
        return
    if not await check_force_join(update, context):
        return

    lang = await get_lang(query.from_user.id)
    user_data = await db.get_user(query.from_user.id)
    text = t("welcome", lang).format(balance=f"{user_data['balance']:.2f}", level=user_data['level'])
    await query.edit_message_text(text, reply_markup=main_menu_keyboard(lang))


# ==================== DIAMOND TOP-UP ====================

async def diamond_topup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if await is_user_banned(query.from_user.id) or await check_maintenance(update, context):
        return
    if not await check_force_join(update, context):
        return

    offers = await db.get_all_offers(active_only=True)
    lang = await get_lang(query.from_user.id)

    if not offers:
        await query.edit_message_text(t("no_offers", lang), reply_markup=back_to_main_keyboard())
        return

    text = "💎 <b>FREE FIRE DIAMOND OFFERS</b>\n\n" if lang == "en" else "💎 <b>ফ্রি ফায়ার ডায়মন্ড অফার</b>\n\n"
    for offer in offers:
        text += f"🔹 {offer['name']} — ৳{offer['price']}\n"

    text += "\nনিচ থেকে অফার সিলেক্ট করুন:" if lang == "bn" else "\nSelect an offer below:"
    await query.edit_message_text(text, reply_markup=offers_keyboard(offers), parse_mode="HTML")


async def select_offer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    offer_id = int(query.data.split("_")[-1])
    offer = await db.get_offer(offer_id)
    lang = await get_lang(query.from_user.id)

    if not offer or offer["is_active"] == 0:
        await query.edit_message_text(t("no_offers", lang), reply_markup=back_to_main_keyboard())
        return

    context.user_data["selected_offer"] = offer_id
    text = t("enter_uid", lang).format(
        name=offer["name"],
        price=offer["price"],
        delivery=offer["delivery_time"]
    )
    await query.edit_message_text(text)
    return UserStates.WAITING_UID


async def receive_uid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.text.strip()
    offer_id = context.user_data.get("selected_offer")
    offer = await db.get_offer(offer_id)
    lang = await get_lang(update.effective_user.id)
    user = await db.get_user(update.effective_user.id)

    if not offer:
        await update.message.reply_text(t("no_offers", lang), reply_markup=main_menu_keyboard(lang))
        return ConversationHandler.END

    if user["balance"] < offer["price"]:
        await update.message.reply_text(
            t("low_balance", lang).format(need=offer["price"], balance=f"{user['balance']:.2f}"),
            reply_markup=main_menu_keyboard(lang)
        )
        return ConversationHandler.END

    context.user_data["uid"] = uid
    text = t("order_confirm", lang).format(
        name=offer["name"],
        price=offer["price"],
        uid=uid,
        delivery=offer["delivery_time"]
    )
    await update.message.reply_text(text, reply_markup=confirm_order_keyboard(offer_id))
    return ConversationHandler.END


async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    offer_id = int(query.data.split("_")[-1])
    offer = await db.get_offer(offer_id)
    uid = context.user_data.get("uid")
    user_id = query.from_user.id
    lang = await get_lang(user_id)

    user = await db.get_user(user_id)
    if user["balance"] < offer["price"]:
        await query.edit_message_text(t("low_balance", lang).format(need=offer["price"], balance=f"{user['balance']:.2f}"), reply_markup=back_to_main_keyboard())
        return

    await db.update_balance(user_id, -offer["price"])
    order_id = await db.create_order(user_id, offer_id, offer["name"], offer["diamonds"], offer["price"], uid)
    await db.increase_order_count(user_id)

    text = t("order_created", lang).format(
        order_id=order_id,
        name=offer["name"],
        uid=uid,
        price=offer["price"]
    )
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=back_to_main_keyboard())

    # Admin Notification
    for admin_id in ADMINS:
        try:
            await context.bot.send_message(
                admin_id,
                f"📦 <b>New Order Received!</b>\n\n"
                f"🆔 Order: <code>{order_id}</code>\n"
                f"👤 User: <code>{user_id}</code>\n"
                f"💎 Product: {offer['name']}\n"
                f"🎮 UID: <code>{uid}</code>\n"
                f"💰 Amount: ৳{offer['price']}",
                parse_mode="HTML",
                reply_markup=order_action_keyboard(order_id)
            )
        except:
            pass


async def cancel_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = await get_lang(query.from_user.id)
    await query.edit_message_text("❌ Order Cancelled." if lang == "en" else "❌ অর্ডার বাতিল করা হয়েছে।", reply_markup=back_to_main_keyboard())


# ==================== WEEKLY / MONTHLY (Basic) ====================

async def buy_weekly(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("📅 Weekly প্যাকেজ শীঘ্রই আসছে...", reply_markup=back_to_main_keyboard())


async def buy_monthly(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("📆 Monthly প্যাকেজ শীঘ্রই আসছে...", reply_markup=back_to_main_keyboard())


# ==================== DEPOSIT ====================

async def deposit_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if await is_user_banned(query.from_user.id) or await check_maintenance(update, context):
        return
    if not await check_force_join(update, context):
        return

    lang = await get_lang(query.from_user.id)
    text = "💰 <b>DEPOSIT</b>\n\nপেমেন্ট মেথড সিলেক্ট করুন:" if lang == "bn" else "💰 <b>DEPOSIT</b>\n\nSelect Payment Method:"
    await query.edit_message_text(text, reply_markup=deposit_method_keyboard(), parse_mode="HTML")


async def deposit_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    method = query.data.split("_")[1]
    context.user_data["deposit_method"] = method.capitalize()
    lang = await get_lang(query.from_user.id)
    text = "💰 ডিপোজিট এমাউন্ট লিখুন (শুধু সংখ্যা):" if lang == "bn" else "💰 Enter Deposit Amount (numbers only):"
    await query.edit_message_text(text)
    return UserStates.WAITING_DEPOSIT_AMOUNT


async def receive_deposit_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text.strip())
    except:
        await update.message.reply_text("সঠিক সংখ্যা লিখুন / Enter valid number:")
        return UserStates.WAITING_DEPOSIT_AMOUNT

    min_deposit = float(await db.get_setting("min_deposit") or 100)
    if amount < min_deposit:
        await update.message.reply_text(f"সর্বনিম্ন ডিপোজিট ৳{min_deposit}")
        return UserStates.WAITING_DEPOSIT_AMOUNT

    context.user_data["deposit_amount"] = amount
    method = context.user_data["deposit_method"]

    if method == "Bkash":
        number = await db.get_setting("bkash_number")
    elif method == "Nagad":
        number = await db.get_setting("nagad_number")
    elif method == "Rocket":
        number = await db.get_setting("rocket_number")
    else:
        number = await db.get_setting("binance_address")

    text = (
        f"💰 Deposit Amount: ৳{amount}\n\n"
        f"Send payment to:\n"
        f"📱 {method}: `{number}`\n\n"
        f"Then enter Transaction ID:"
    )
    await update.message.reply_text(text, parse_mode="Markdown")
    return UserStates.WAITING_TRX_ID


async def receive_trx_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    trx_id = update.message.text.strip()
    user_id = update.effective_user.id
    amount = context.user_data["deposit_amount"]
    method = context.user_data["deposit_method"]
    lang = await get_lang(user_id)

    success = await db.create_deposit(user_id, amount, method, trx_id)
    if not success:
        await update.message.reply_text("❌ এই Transaction ID আগে ব্যবহার করা হয়েছে!", reply_markup=main_menu_keyboard(lang))
        return ConversationHandler.END

    await update.message.reply_text(
        "✅ Deposit Request পাঠানো হয়েছে!\nঅ্যাডমিন Approve করলে Balance যোগ হবে।" if lang == "bn" else "✅ Deposit Request sent!\nBalance will be added after Admin approval.",
        reply_markup=main_menu_keyboard(lang)
    )

    # Admin Notification
    for admin_id in ADMINS:
        try:
            deposits = await db.get_pending_deposits()
            dep = next((d for d in deposits if d["trx_id"] == trx_id), None)
            if dep:
                text = (
                    f"💵 <b>NEW DEPOSIT REQUEST</b>\n\n"
                    f"👤 User: @{update.effective_user.username or 'N/A'}\n"
                    f"🆔 ID: <code>{user_id}</code>\n"
                    f"💰 Amount: ৳{amount}\n"
                    f"💳 Method: {method}\n"
                    f"🧾 TxID: <code>{trx_id}</code>"
                )
                await context.bot.send_message(
                    admin_id, text, parse_mode="HTML",
                    reply_markup=deposit_action_keyboard(dep["id"])
                )
        except:
            pass

    return ConversationHandler.END


# ==================== MY ACCOUNT / ORDERS / REFERRAL / SUPPORT / HELP ====================

async def my_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = await db.get_user(query.from_user.id)
    lang = await get_lang(query.from_user.id)

    text = (
        f"👤 <b>MY ACCOUNT</b>\n\n"
        f"👤 Name: {user['full_name']}\n"
        f"🆔 ID: <code>{user['user_id']}</code>\n"
        f"🔗 Username: @{user['username'] or 'N/A'}\n\n"
        f"💰 Balance: ৳{user['balance']:.2f}\n"
        f"🎖 Level: {user['level']}\n"
        f"📦 Total Orders: {user['total_orders']}\n"
        f"💵 Total Deposited: ৳{user['total_deposited']:.2f}\n"
        f"📅 Joined: {user['joined_at'][:10]}"
    )
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=back_to_main_keyboard())


async def my_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    orders = await db.get_user_orders(query.from_user.id)
    lang = await get_lang(query.from_user.id)

    if not orders:
        await query.edit_message_text("আপনার কোনো Order নেই।" if lang == "bn" else "You have no orders.", reply_markup=back_to_main_keyboard())
        return

    text = "📜 <b>MY ORDERS</b>\n\n"
    for order in orders[:10]:
        text += f"📦 <code>{order['order_id']}</code>\n💎 {order['offer_name']}\n💰 ৳{order['price']} | {order['status']}\n\n"
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=back_to_main_keyboard())


async def referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    bot_info = await context.bot.get_me()
    link = f"https://t.me/{bot_info.username}?start=ref{user_id}"
    reward = await db.get_setting("referral_reward") or 5

    text = (
        f"🤝 <b>REFERRAL SYSTEM</b>\n\n"
        f"🔗 Your Link:\n<code>{link}</code>\n\n"
        f"🎁 Referral Bonus: ৳{reward}\n\n"
        f"বন্ধুদের শেয়ার করুন এবং বোনাস পান!"
    )
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=back_to_main_keyboard())


async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    support_user = await db.get_setting("support_username") or "@Support"
    await query.edit_message_text(f"📞 Support: {support_user}\n\nযেকোনো সমস্যায় যোগাযোগ করুন।", reply_markup=back_to_main_keyboard())


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = (
        "ℹ️ <b>HELP</b>\n\n"
        "1️⃣ আগে Deposit করে Balance যোগ করুন\n"
        "2️⃣ Diamond Top-Up থেকে অফার সিলেক্ট করুন\n"
        "3️⃣ Free Fire UID দিন\n"
        "4️⃣ Confirm করুন\n\n"
        "কোনো সমস্যা হলে Support এ যোগাযোগ করুন।"
    )
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=back_to_main_keyboard())


# ==================== ADMIN PART (Dashboard + Download Users) ====================

async def dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update, context):
        return

    stats = await db.get_stats()
    text = (
        f"👑 <b>ADMIN DASHBOARD</b>\n\n"
        f"👥 Total Users: <b>{stats['total_users']}</b>\n"
        f"🟢 Active: {stats['active_users']}\n"
        f"🚫 Banned: {stats['banned_users']}\n"
        f"📦 Total Orders: {stats['total_orders']}\n"
        f"⏳ Pending Orders: {stats['pending_orders']}\n"
        f"💵 Total Deposits: ৳{stats['total_deposits']:.2f}\n"
        f"💎 Total Sales: ৳{stats['total_sales']:.2f}\n\n"
        f"Choose an option:"
    )
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, parse_mode="HTML", reply_markup=admin_dashboard_keyboard())
    else:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=admin_dashboard_keyboard())


async def download_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not await admin_only(update, context):
        return

    users = await db.get_all_users()
    if not users:
        await query.edit_message_text("কোনো ইউজার নেই।", reply_markup=back_to_admin_keyboard())
        return

    lines = ["Username | Chat ID | Balance | Level\n" + "-"*50]
    for u in users:
        username = u["username"] or "N/A"
        lines.append(f"{username} | {u['user_id']} | ৳{u['balance']:.2f} | Level {u['level']}")

    content = "\n".join(lines)
    file = io.BytesIO(content.encode("utf-8"))
    file.name = f"users_data_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"

    await context.bot.send_document(
        chat_id=query.from_user.id,
        document=InputFile(file),
        caption=f"📥 To
        # ==================== ADMIN OFFERS ====================

async def admin_offers_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not await admin_only(update, context):
        return
    await query.edit_message_text("🎁 <b>Manage Offers</b>", parse_mode="HTML", reply_markup=admin_offers_keyboard())


async def add_offer_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not await admin_only(update, context):
        return ConversationHandler.END
    await query.edit_message_text("🎁 নতুন অফারের নাম লিখুন:")
    return AdminStates.ADD_OFFER_NAME


async def add_offer_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["offer_name"] = update.message.text.strip()
    await update.message.reply_text("💎 Diamond Amount লিখুন (শুধু সংখ্যা):")
    return AdminStates.ADD_OFFER_DIAMONDS


async def add_offer_diamonds(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["offer_diamonds"] = int(update.message.text.strip())
        await update.message.reply_text("💰 Price লিখুন:")
        return AdminStates.ADD_OFFER_PRICE
    except:
        await update.message.reply_text("সঠিক সংখ্যা লিখুন:")
        return AdminStates.ADD_OFFER_DIAMONDS


async def add_offer_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["offer_price"] = float(update.message.text.strip())
        await update.message.reply_text("🔘 Button Name লিখুন (উদাহরণ: 💎 100 Diamonds):")
        return AdminStates.ADD_OFFER_BUTTON
    except:
        await update.message.reply_text("সঠিক দাম লিখুন:")
        return AdminStates.ADD_OFFER_PRICE


async def add_offer_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["offer_button"] = update.message.text.strip()
    await update.message.reply_text("📝 Description লিখুন (না থাকলে skip লিখুন):")
    return AdminStates.ADD_OFFER_DESCRIPTION


async def add_offer_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    desc = update.message.text.strip()
    context.user_data["offer_description"] = "" if desc.lower() == "skip" else desc
    await update.message.reply_text("⚡ Delivery Time লিখুন (উদাহরণ: 1-5 Minutes):")
    return AdminStates.ADD_OFFER_DELIVERY


async def add_offer_delivery(update: Update, context: ContextTypes.DEFAULT_TYPE):
    delivery = update.message.text.strip()
    context.user_data["offer_delivery"] = delivery

    text = (
        f"🎁 <b>NEW OFFER PREVIEW</b>\n\n"
        f"💎 Name: {context.user_data['offer_name']}\n"
        f"💎 Diamonds: {context.user_data['offer_diamonds']}\n"
        f"💰 Price: ৳{context.user_data['offer_price']}\n"
        f"🔘 Button: {context.user_data['offer_button']}\n"
        f"📝 Desc: {context.user_data['offer_description'] or 'N/A'}\n"
        f"⚡ Delivery: {delivery}\n\n"
        f"Save করতে চাও?"
    )
    keyboard = [
        [
            InlineKeyboardButton("✅ Save", callback_data="save_offer"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_add_offer")
        ]
    ]
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
    return ConversationHandler.END


async def save_offer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    offer_id = await db.add_offer(
        name=context.user_data["offer_name"],
        diamonds=context.user_data["offer_diamonds"],
        price=context.user_data["offer_price"],
        button_name=context.user_data["offer_button"],
        description=context.user_data.get("offer_description", ""),
        delivery_time=context.user_data["offer_delivery"]
    )
    await query.edit_message_text(f"✅ অফার সফলভাবে অ্যাড হয়েছে! (ID: {offer_id})")


async def cancel_add_offer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("❌ অফার অ্যাড বাতিল করা হয়েছে।")


async def all_offers_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not await admin_only(update, context):
        return
    offers = await db.get_all_offers(active_only=False)
    if not offers:
        await query.edit_message_text("কোনো অফার নেই।", reply_markup=back_to_admin_keyboard())
        return
    text = "📋 <b>ALL OFFERS</b>\n\n"
    for offer in offers:
        status = "🟢" if offer["is_active"] else "🔴"
        text += f"{status} ID:{offer['id']} | {offer['name']} | ৳{offer['price']}\n"
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=back_to_admin_keyboard())


# ==================== BAN / UNBAN / BALANCE ====================

async def ban_user_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not await admin_only(update, context):
        return ConversationHandler.END
    await query.edit_message_text("🚫 ব্যান করতে User ID লিখুন:")
    return AdminStates.BAN_USER_ID


async def ban_user_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["ban_user_id"] = int(update.message.text.strip())
        await update.message.reply_text("Reason লিখুন:")
        return AdminStates.BAN_REASON
    except:
        await update.message.reply_text("সঠিক User ID লিখুন:")
        return AdminStates.BAN_USER_ID


async def ban_reason(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reason = update.message.text.strip()
    user_id = context.user_data["ban_user_id"]
    await db.ban_user(user_id, reason)
    await update.message.reply_text(f"✅ User <code>{user_id}</code> ব্যান করা হয়েছে।\nReason: {reason}", parse_mode="HTML")
    return ConversationHandler.END


async def unban_user_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not await admin_only(update, context):
        return ConversationHandler.END
    await query.edit_message_text("✅ আনব্যান করতে User ID লিখুন:")
    return AdminStates.UNBAN_USER_ID


async def unban_user_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = int(update.message.text.strip())
        await db.unban_user(user_id)
        await update.message.reply_text(f"✅ User <code>{user_id}</code> আনব্যান করা হয়েছে।", parse_mode="HTML")
    except:
        await update.message.reply_text("সঠিক User ID লিখুন:")
        return AdminStates.UNBAN_USER_ID
    return ConversationHandler.END


async def add_balance_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not await admin_only(update, context):
        return ConversationHandler.END
    await query.edit_message_text("💰 Balance অ্যাড করতে User ID লিখুন:")
    return AdminStates.ADD_BALANCE_USER


async def add_balance_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["balance_user_id"] = int(update.message.text.strip())
        await update.message.reply_text("কত টাকা অ্যাড করবেন?")
        return AdminStates.ADD_BALANCE_AMOUNT
    except:
        await update.message.reply_text("সঠিক User ID লিখুন:")
        return AdminStates.ADD_BALANCE_USER


async def add_balance_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text.strip())
        user_id = context.user_data["balance_user_id"]
        await db.update_balance(user_id, amount)
        await update.message.reply_text(f"✅ ৳{amount} অ্যাড করা হয়েছে User <code>{user_id}</code>-এ।", parse_mode="HTML")
        try:
            await context.bot.send_message(user_id, f"💰 আপনার অ্যাকাউন্টে ৳{amount} যোগ করা হয়েছে।")
        except:
            pass
    except:
        await update.message.reply_text("সঠিক পরিমাণ লিখুন:")
        return AdminStates.ADD_BALANCE_AMOUNT
    return ConversationHandler.END


async def remove_balance_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not await admin_only(update, context):
        return ConversationHandler.END
    await query.edit_message_text("➖ Balance কাটতে User ID লিখুন:")
    return AdminStates.REMOVE_BALANCE_USER


async def remove_balance_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["balance_user_id"] = int(update.message.text.strip())
        await update.message.reply_text("কত টাকা কাটবেন?")
        return AdminStates.REMOVE_BALANCE_AMOUNT
    except:
        await update.message.reply_text("সঠিক User ID লিখুন:")
        return AdminStates.REMOVE_BALANCE_USER


async def remove_balance_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text.strip())
        user_id = context.user_data["balance_user_id"]
        await db.update_balance(user_id, -amount)
        await update.message.reply_text(f"✅ ৳{amount} কাটা হয়েছে User <code>{user_id}</code> থেকে।", parse_mode="HTML")
    except:
        await update.message.reply_text("সঠিক পরিমাণ লিখুন:")
        return AdminStates.REMOVE_BALANCE_AMOUNT
    return ConversationHandler.END


# ==================== DEPOSIT APPROVE / REJECT WITH REASON ====================

async def pending_deposits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not await admin_only(update, context):
        return
    deposits = await db.get_pending_deposits()
    if not deposits:
        await query.edit_message_text("কোনো Pending Deposit নেই।", reply_markup=back_to_admin_keyboard())
        return
    for dep in deposits[:8]:
        user = await db.get_user(dep["user_id"])
        text = (
            f"💵 <b>DEPOSIT REQUEST</b>\n\n"
            f"👤 @{user['username'] or 'N/A'}\n"
            f"🆔 <code>{dep['user_id']}</code>\n"
            f"💰 ৳{dep['amount']}\n"
            f"💳 {dep['method']}\n"
            f"🧾 <code>{dep['trx_id']}</code>"
        )
        await context.bot.send_message(
            query.from_user.id, text, parse_mode="HTML",
            reply_markup=deposit_action_keyboard(dep["id"])
        )
    await query.edit_message_text("Pending Deposits পাঠানো হয়েছে।", reply_markup=back_to_admin_keyboard())


async def approve_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not await admin_only(update, context):
        return
    deposit_id = int(query.data.split("_")[-1])
    dep = await db.get_deposit(deposit_id)
    if not dep or dep["status"] != "Pending":
        await query.edit_message_text("ইতিমধ্যে প্রসেস করা হয়েছে।")
        return
    await db.update_deposit_status(deposit_id, "Approved")
    await db.update_balance(dep["user_id"], dep["amount"])
    await query.edit_message_text(f"✅ Deposit Approved! ৳{dep['amount']} যোগ করা হয়েছে।")
    try:
        await context.bot.send_message(dep["user_id"], f"✅ আপনার Deposit Approve হয়েছে!\n💰 ৳{dep['amount']} Balance-এ যোগ করা হয়েছে।")
    except:
        pass


async def reject_deposit_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not await admin_only(update, context):
        return ConversationHandler.END
    deposit_id = int(query.data.split("_")[-1])
    context.user_data["reject_deposit_id"] = deposit_id
    await query.edit_message_text("❌ Reject Reason লিখুন:")
    return AdminStates.REJECT_DEPOSIT_REASON


async def reject_deposit_reason(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reason = update.message.text.strip()
    deposit_id = context.user_data["reject_deposit_id"]
    dep = await db.get_deposit(deposit_id)
    if not dep or dep["status"] != "Pending":
        await update.message.reply_text("ইতিমধ্যে প্রসেস করা হয়েছে।")
        return ConversationHandler.END
    await db.update_deposit_status(deposit_id, "Rejected", reason)
    await update.message.reply_text(f"❌ Deposit Rejected.\nReason: {reason}")
    try:
        await context.bot.send_message(
            dep["user_id"],
            f"❌ আপনার Deposit Request Reject করা হয়েছে।\n\nকারণ: {reason}"
        )
    except:
        pass
    return ConversationHandler.END


# ==================== ORDERS ADMIN ====================

async def pending_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not await admin_only(update, context):
        return
    orders = await db.get_orders_by_status("Pending")
    if not orders:
        await query.edit_message_text("কোনো Pending Order নেই।", reply_markup=back_to_admin_keyboard())
        return
    for order in orders[:8]:
        text = (
            f"📦 <b>ORDER</b> <code>{order['order_id']}</code>\n\n"
            f"👤 User: <code>{order['user_id']}</code>\n"
            f"💎 {order['offer_name']}\n"
            f"🆔 UID: <code>{order['uid']}</code>\n"
            f"💰 ৳{order['price']}"
        )
        await context.bot.send_message(
            query.from_user.id, text, parse_mode="HTML",
            reply_markup=order_action_keyboard(order["order_id"])
        )
    await query.edit_message_text("Pending Orders পাঠানো হয়েছে।", reply_markup=back_to_admin_keyboard())


async def complete_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not await admin_only(update, context):
        return
    order_id = query.data.split("_")[-1]
    order = await db.get_order(order_id)
    if not order:
        await query.edit_message_text("Order পাওয়া যায়নি।")
        return
    await db.update_order_status(order_id, "Completed")
    await query.edit_message_text(f"✅ Order <code>{order_id}</code> Completed!", parse_mode="HTML")
    try:
        delivery_msg = await db.get_setting("delivery_message")
        await context.bot.send_message(
            order["user_id"],
            f"✅ আপনার Order সম্পন্ন হয়েছে!\n📦 Order ID: <code>{order_id}</code>\n\n{delivery_msg}",
            parse_mode="HTML"
        )
    except:
        pass


async def process_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not await admin_only(update, context):
        return
    order_id = query.data.split("_")[-1]
    await db.update_order_status(order_id, "Processing")
    await query.edit_message_text(f"⚡ Order <code>{order_id}</code> Processing করা হয়েছে।", parse_mode="HTML")


async def cancel_order_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not await admin_only(update, context):
        return
    order_id = query.data.split("_")[-1]
    order = await db.get_order(order_id)
    if order and order["status"] in ["Pending", "Processing"]:
        await db.update_balance(order["user_id"], order["price"])
        await db.update_order_status(order_id, "Cancelled")
        await query.edit_message_text(f"❌ Order <code>{order_id}</code> Cancel করা হয়েছে + টাকা ফেরত।", parse_mode="HTML")
        try:
            await context.bot.send_message(
                order["user_id"],
                f"❌ আপনার Order <code>{order_id}</code> Cancel করা হয়েছে।\n💰 ৳{order['price']} ফেরত দেওয়া হয়েছে।"
            )
        except:
            pass
    else:
        await query.edit_message_text("Order Cancel করা যায়নি।")


# ==================== BROADCAST ====================

async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not await admin_only(update, context):
        return ConversationHandler.END
    await query.edit_message_text("📢 Broadcast মেসেজ লিখুন:")
    return AdminStates.BROADCAST_MESSAGE


async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["broadcast_text"] = update.message.text
    keyboard = [
        [InlineKeyboardButton("✅ Send to All", callback_data="broadcast_all")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_broadcast")]
    ]
    await update.message.reply_text(
        f"Preview:\n\n{context.user_data['broadcast_text']}\n\nপাঠাবেন?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ConversationHandler.END


async def broadcast_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = context.user_data.get("broadcast_text")
    users = await db.get_all_users()
    success = fail = 0
    await query.edit_message_text("📤 Broadcast শুরু হয়েছে...")
    for user in users:
        if user["is_banned"] == 0:
            try:
                await context.bot.send_message(user["user_id"], text)
                success += 1
            except:
                fail += 1
    await context.bot.send_message(query.from_user.id, f"✅ Broadcast শেষ!\nসফল: {success}\nব্যর্থ: {fail}")


async def cancel_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("❌ Broadcast বাতিল করা হয়েছে।")


# ==================== STATS ====================

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not await admin_only(update, context):
        return
    stats = await db.get_stats()
    text = (
        f"📊 <b>BOT STATISTICS</b>\n\n"
        f"👥 Total Users: {stats['total_users']}\n"
        f"🟢 Active: {stats['active_users']}\n"
        f"🚫 Banned: {stats['banned_users']}\n\n"
        f"💵 Total Deposit: ৳{stats['total_deposits']:.2f}\n"
        f"💎 Total Sales: ৳{stats['total_sales']:.2f}\n\n"
        f"📦 Orders: {stats['total_orders']}\n"
        f"✅ Completed: {stats['completed_orders']}\n"
        f"⏳ Pending: {stats['pending_orders']}"
    )
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=back_to_admin_keyboardEND
  # ==================== SEARCH USER + ALL USERS ====================

async def admin_users_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not await admin_only(update, context):
        return
    await query.edit_message_text("👥 <b>Users Management</b>", parse_mode="HTML", reply_markup=admin_users_keyboard())


async def search_user_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not await admin_only(update, context):
        return ConversationHandler.END
    await query.edit_message_text("🔎 User ID লিখুন:")
    return AdminStates.SEARCH_USER


async def search_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = int(update.message.text.strip())
        user = await db.get_user(user_id)
        if not user:
            await update.message.reply_text("User পাওয়া যায়নি।")
            return ConversationHandler.END

        text = (
            f"👥 <b>USER DETAILS</b>\n\n"
            f"👤 Name: {user['full_name']}\n"
            f"🆔 ID: <code>{user['user_id']}</code>\n"
            f"🔗 Username: @{user['username'] or 'N/A'}\n\n"
            f"💰 Balance: ৳{user['balance']:.2f}\n"
            f"🎖 Level: {user['level']}\n"
            f"📦 Total Orders: {user['total_orders']}\n"
            f"💵 Total Deposited: ৳{user['total_deposited']:.2f}\n"
            f"📅 Joined: {user['joined_at'][:10]}\n"
            f"Status: {'🚫 Banned' if user['is_banned'] else '🟢 Active'}"
        )
        keyboard = [
            [
                InlineKeyboardButton("💰 Add Balance", callback_data=f"quick_add_{user_id}"),
                InlineKeyboardButton("➖ Remove", callback_data=f"quick_remove_{user_id}")
            ],
            [
                InlineKeyboardButton("🚫 Ban", callback_data=f"quick_ban_{user_id}"),
                InlineKeyboardButton("✅ Unban", callback_data=f"quick_unban_{user_id}")
            ],
            [InlineKeyboardButton("🔙 Back", callback_data="admin_users")]
        ]
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
    except:
        await update.message.reply_text("সঠিক User ID লিখুন:")
        return AdminStates.SEARCH_USER
    return ConversationHandler.END


async def all_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not await admin_only(update, context):
        return
    users = await db.get_all_users()
    if not users:
        await query.edit_message_text("কোনো ইউজার নেই।", reply_markup=back_to_admin_keyboard())
        return

    text = f"👥 <b>ALL USERS</b> (Total: {len(users)})\n\n"
    for user in users[:25]:
        status = "🚫" if user["is_banned"] else "🟢"
        text += f"{status} <code>{user['user_id']}</code> | @{user['username'] or 'N/A'} | ৳{user['balance']:.0f} | Lv.{user['level']}\n"

    if len(users) > 25:
        text += f"\n... এবং আরও {len(users)-25} জন"
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=back_to_admin_keyboard())


async def quick_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = int(query.data.split("_")[-1])
    await db.ban_user(user_id, "Banned by Admin")
    await query.edit_message_text(f"🚫 User <code>{user_id}</code> ব্যান করা হয়েছে।", parse_mode="HTML")


async def quick_unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = int(query.data.split("_")[-1])
    await db.unban_user(user_id)
    await query.edit_message_text(f"✅ User <code>{user_id}</code> আনব্যান করা হয়েছে।", parse_mode="HTML")


# ==================== PROMO CODE ====================

async def add_promo_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not await admin_only(update, context):
        return ConversationHandler.END
    await query.edit_message_text("🎟 Promo Code লিখুন (উদাহরণ: FF50):")
    return AdminStates.ADD_PROMO_CODE


async def add_promo_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["promo_code"] = update.message.text.strip().upper()
    await update.message.reply_text("Discount Amount লিখুন (৳):")
    return AdminStates.ADD_PROMO_DISCOUNT


async def add_promo_discount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["promo_discount"] = float(update.message.text.strip())
        await update.message.reply_text("Maximum Uses লিখুন:")
        return AdminStates.ADD_PROMO_USES
    except:
        await update.message.reply_text("সঠিক সংখ্যা লিখুন:")
        return AdminStates.ADD_PROMO_DISCOUNT


async def add_promo_uses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["promo_uses"] = int(update.message.text.strip())
        await update.message.reply_text("Minimum Purchase Amount লিখুন:")
        return AdminStates.ADD_PROMO_MIN
    except:
        await update.message.reply_text("সঠিক সংখ্যা লিখুন:")
        return AdminStates.ADD_PROMO_USES


async def add_promo_min(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["promo_min"] = float(update.message.text.strip())
        await update.message.reply_text("Expiry Date লিখুন (উদাহরণ: 2026-12-31):")
        return AdminStates.ADD_PROMO_EXPIRY
    except:
        await update.message.reply_text("সঠিক সংখ্যা লিখুন:")
        return AdminStates.ADD_PROMO_MIN


async def add_promo_expiry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    expiry = update.message.text.strip()
    await db.add_promo(
        code=context.user_data["promo_code"],
        discount=context.user_data["promo_discount"],
        max_uses=context.user_data["promo_uses"],
        min_purchase=context.user_data["promo_min"],
        expiry_date=expiry
    )
    await update.message.reply_text(
        f"✅ Promo Code তৈরি হয়েছে!\n\n"
        f"Code: <code>{context.user_data['promo_code']}</code>\n"
        f"Discount: ৳{context.user_data['promo_discount']}\n"
        f"Uses: {context.user_data['promo_uses']}\n"
        f"Min Purchase: ৳{context.user_data['promo_min']}\n"
        f"Expiry: {expiry}",
        parse_mode="HTML"
    )
    return ConversationHandler.END


# ==================== SETTINGS ====================

async def admin_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not await admin_only(update, context):
        return

    bkash = await db.get_setting("bkash_number")
    nagad = await db.get_setting("nagad_number")
    rocket = await db.get_setting("rocket_number")
    binance = await db.get_setting("binance_address")
    min_dep = await db.get_setting("min_deposit")
    ref_reward = await db.get_setting("referral_reward")
    force_join = await db.get_setting("force_join")
    maintenance = await db.get_setting("maintenance_mode")
    support = await db.get_setting("support_username")

    text = (
        f"⚙️ <b>SETTINGS</b>\n\n"
        f"💳 bKash: <code>{bkash}</code>\n"
        f"💳 Nagad: <code>{nagad}</code>\n"
        f"💳 Rocket: <code>{rocket}</code>\n"
        f"💳 Binance: <code>{binance}</code>\n\n"
        f"💰 Min Deposit: ৳{min_dep}\n"
        f"🤝 Referral Reward: ৳{ref_reward}\n"
        f"📢 Force Join: {force_join}\n"
        f"🔧 Maintenance: {maintenance}\n"
        f"📞 Support: {support}"
    )

    keyboard = [
        [InlineKeyboardButton("✏️ Edit bKash", callback_data="set_bkash_number")],
        [InlineKeyboardButton("✏️ Edit Nagad", callback_data="set_nagad_number")],
        [InlineKeyboardButton("✏️ Edit Rocket", callback_data="set_rocket_number")],
        [InlineKeyboardButton("✏️ Edit Binance", callback_data="set_binance_address")],
        [InlineKeyboardButton("✏️ Min Deposit", callback_data="set_min_deposit")],
        [InlineKeyboardButton("✏️ Referral Reward", callback_data="set_referral_reward")],
        [InlineKeyboardButton("📢 Toggle Force Join", callback_data="toggle_force_join")],
        [InlineKeyboardButton("🔧 Toggle Maintenance", callback_data="toggle_maintenance")],
        [InlineKeyboardButton("📞 Edit Support", callback_data="set_support_username")],
        [InlineKeyboardButton("🔙 Back", callback_data="admin_dashboard")]
    ]
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))


async def edit_setting_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    key = query.data.replace("set_", "")
    context.user_data["edit_setting_key"] = key
    await query.edit_message_text(f"নতুন মান লিখুন ({key}):")
    return AdminStates.EDIT_SETTING_VALUE


async def edit_setting_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    value = update.message.text.strip()
    key = context.user_data["edit_setting_key"]
    await db.set_setting(key, value)
    await update.message.reply_text(f"✅ <b>{key}</b> আপডেট করা হয়েছে!", parse_mode="HTML")
    return ConversationHandler.END


async def toggle_force_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    current = await db.get_setting("force_join")
    new_value = "False" if str(current).lower() == "true" else "True"
    await db.set_setting("force_join", new_value)
    status = "চালু" if new_value == "True" else "বন্ধ"
    await query.edit_message_text(f"📢 Force Join {status} করা হয়েছে!")


async def toggle_maintenance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    current = await db.get_setting("maintenance_mode")
    new_value = "False" if str(current).lower() == "true" else "True"
    await db.set_setting("maintenance_mode", new_value)
    status = "চালু" if new_value == "True" else "বন্ধ"
    await query.edit_message_text(f"🔧 Maintenance Mode {status} করা হয়েছে!")


# ==================== ADMIN MANAGEMENT ====================

async def admin_management(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not await admin_only(update, context):
        return
    keyboard = [
        [InlineKeyboardButton("➕ Add Admin", callback_data="add_admin")],
        [InlineKeyboardButton("➖ Remove Admin", callback_data="remove_admin")],
        [InlineKeyboardButton("🔙 Back", callback_data="admin_dashboard")]
    ]
    await query.edit_message_text("🛡️ <b>Admin Management</b>", parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))


async def add_admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("নতুন Admin-এর User ID লিখুন:")
    return AdminStates.ADD_ADMIN_ID


async def add_admin_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = int(update.message.text.strip())
        await db.add_admin(user_id)
        await update.message.reply_text(f"✅ User <code>{user_id}</code> Admin করা হয়েছে।", parse_mode="HTML")
    except:
        await update.message.reply_text("সঠিক User ID লিখুন:")
        return AdminStates.ADD_ADMIN_ID
    return ConversationHandler.END


async def remove_admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("কোন Admin রিমুভ করবেন? User ID লিখুন:")
    return AdminStates.REMOVE_ADMIN_ID


async def remove_admin_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = int(update.message.text.strip())
        await db.remove_admin(user_id)
        await update.message.reply_text(f"✅ User <code>{user_id}</code> Admin থেকে রিমুভ করা হয়েছে।", parse_mode="HTML")
    except:
        await update.message.reply_text("সঠিক User ID লিখুন:")
        return AdminStates.REMOVE_ADMIN_ID
    return ConversationHandler.END


# ==================== EXTRA MENUS ====================

async def admin_deposits_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not await admin_only(update, context):
        return
    await query.edit_message_text("💵 <b>Deposits</b>", parse_mode="HTML", reply_markup=admin_deposits_keyboard())


async def admin_orders_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not await admin_only(update, context):
        return
    await query.edit_message_text("📦 <b>Orders</b>", parse_mode="HTML", reply_markup=admin_orders_keyboard())


async def special_offers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await diamond_topup(update, context): {len(users)}"
    )
    await query.edit_message_text("✅ Users data পাঠানো হয়েছে!", reply_markup=back_to_admin_keyboard())


async def close_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Dashboard বন্ধ করা হয়েছে।")


# ==================== CANCEL ====================

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = await get_lang(update.effective_user.id)
    await update.message.reply_text("❌ বাতিল করা হয়েছে।" if lang == "bn" else "❌ Cancelled.", reply_markup=main_menu_keyboard(lang))
    return ConversationHandler.END
