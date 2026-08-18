import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# মেইন অ্যাডমিন আইডি (এখানে নিজের আইডি দাও)
ADMINS = [123456789]   # তোমার Telegram ID

DB_NAME = "freefire_bot.db"

# Channel Info
CHANNEL_USERNAME = "Napa_Extra_Channel"
CHANNEL_LINK = "https://t.me/Napa_Extra_Channel"
CHANNEL_ID = -1003958718736

DEFAULT_SETTINGS = {
    "bkash_number": "01XXXXXXXXX",
    "nagad_number": "01XXXXXXXXX",
    "rocket_number": "01XXXXXXXXX",
    "binance_address": "YourBinanceAddress",
    "min_deposit": 100,
    "min_purchase": 50,
    "referral_reward": 5,                    # ডিফল্ট ৫ টাকা
    "new_offer_notification": True,
    "maintenance_mode": False,
    "support_username": "@YourSupport",
    "terms": "আমাদের টার্মস এন্ড কন্ডিশনস।",
    "delivery_message": "✅ আপনার অর্ডার সফলভাবে সম্পন্ন হয়েছে! ১-৫ মিনিটের মধ্যে ডায়মন্ড পেয়ে যাবেন।",
    "force_join": True,                      # Mandatory Channel Join
    "level_1_orders": 20,                    # Level আপ হওয়ার জন্য অর্ডার সংখ্যা
    "level_2_orders": 50,
    "level_3_orders": 100,
    "level_discount": 5                      # Level অনুযায়ী ডিসকাউন্ট %
}
