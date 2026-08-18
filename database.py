import aiosqlite
from config import DB_NAME, DEFAULT_SETTINGS
from datetime import datetime

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                balance REAL DEFAULT 0,
                is_banned INTEGER DEFAULT 0,
                ban_reason TEXT,
                referred_by INTEGER,
                total_deposited REAL DEFAULT 0,
                total_spent REAL DEFAULT 0,
                total_orders INTEGER DEFAULT 0,
                level INTEGER DEFAULT 0,
                language TEXT DEFAULT 'bn',
                joined_at TEXT
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS offers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                diamonds INTEGER NOT NULL,
                price REAL NOT NULL,
                button_name TEXT NOT NULL,
                description TEXT,
                delivery_time TEXT DEFAULT '1-5 Minutes',
                image_file_id TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT UNIQUE,
                user_id INTEGER,
                offer_id INTEGER,
                offer_name TEXT,
                diamonds INTEGER,
                price REAL,
                uid TEXT,
                status TEXT DEFAULT 'Pending',
                created_at TEXT,
                completed_at TEXT
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS deposits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount REAL,
                method TEXT,
                trx_id TEXT UNIQUE,
                status TEXT DEFAULT 'Pending',
                reject_reason TEXT,
                created_at TEXT,
                processed_at TEXT
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS promo_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE,
                discount REAL,
                discount_type TEXT DEFAULT 'fixed',
                max_uses INTEGER,
                used_count INTEGER DEFAULT 0,
                min_purchase REAL DEFAULT 0,
                expiry_date TEXT,
                is_active INTEGER DEFAULT 1
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                user_id INTEGER PRIMARY KEY,
                role TEXT DEFAULT 'Admin'
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS referrals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER,
                referred_id INTEGER,
                reward REAL,
                created_at TEXT
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER,
                action TEXT,
                details TEXT,
                created_at TEXT
            )
        """)

        await db.commit()

        for key, value in DEFAULT_SETTINGS.items():
            await db.execute(
                "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                (key, str(value))
            )
        await db.commit()


# ========== USER ==========
async def add_user(user_id, username, full_name, referred_by=None):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """INSERT OR IGNORE INTO users 
               (user_id, username, full_name, referred_by, joined_at) 
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, username, full_name, referred_by, datetime.now().isoformat())
        )
        await db.commit()

async def get_user(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        return await cursor.fetchone()

async def update_balance(user_id, amount):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE users SET balance = balance + ? WHERE user_id = ?",
            (amount, user_id)
        )
        await db.commit()

async def set_balance(user_id, amount):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE users SET balance = ? WHERE user_id = ?",
            (amount, user_id)
        )
        await db.commit()

async def ban_user(user_id, reason=""):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE users SET is_banned = 1, ban_reason = ? WHERE user_id = ?",
            (reason, user_id)
        )
        await db.commit()

async def unban_user(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE users SET is_banned = 0, ban_reason = NULL WHERE user_id = ?",
            (user_id,)
        )
        await db.commit()

async def get_all_users():
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM users ORDER BY joined_at DESC")
        return await cursor.fetchall()

async def set_language(user_id, lang):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE users SET language = ? WHERE user_id = ?",
            (lang, user_id)
        )
        await db.commit()

async def increase_order_count(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE users SET total_orders = total_orders + 1 WHERE user_id = ?",
            (user_id,)
        )
        await db.commit()
        # Level আপডেট
        user = await get_user(user_id)
        level = 0
        if user["total_orders"] >= 100:
            level = 3
        elif user["total_orders"] >= 50:
            level = 2
        elif user["total_orders"] >= 20:
            level = 1
        await db.execute(
            "UPDATE users SET level = ? WHERE user_id = ?",
            (level, user_id)
        )
        await db.commit()


# ========== OFFER ==========
async def add_offer(name, diamonds, price, button_name, description="", delivery_time="1-5 Minutes", image_file_id=None):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """INSERT INTO offers 
               (name, diamonds, price, button_name, description, delivery_time, image_file_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (name, diamonds, price, button_name, description, delivery_time, image_file_id, datetime.now().isoformat())
        )
        await db.commit()
        return cursor.lastrowid

async def get_all_offers(active_only=True):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        if active_only:
            cursor = await db.execute("SELECT * FROM offers WHERE is_active = 1 ORDER BY price ASC")
        else:
            cursor = await db.execute("SELECT * FROM offers ORDER BY id DESC")
        return await cursor.fetchall()

async def get_offer(offer_id):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM offers WHERE id = ?", (offer_id,))
        return await cursor.fetchone()

async def update_offer(offer_id, **kwargs):
    async with aiosqlite.connect(DB_NAME) as db:
        fields = []
        values = []
        for key, value in kwargs.items():
            fields.append(f"{key} = ?")
            values.append(value)
        values.append(offer_id)
        query = f"UPDATE offers SET {', '.join(fields)} WHERE id = ?"
        await db.execute(query, values)
        await db.commit()

async def delete_offer(offer_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM offers WHERE id = ?", (offer_id,))
        await db.commit()


# ========== ORDER ==========
async def create_order(user_id, offer_id, offer_name, diamonds, price, uid):
    order_id = f"FF{datetime.now().strftime('%y%m%d%H%M%S')}{user_id % 1000}"
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """INSERT INTO orders 
               (order_id, user_id, offer_id, offer_name, diamonds, price, uid, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (order_id, user_id, offer_id, offer_name, diamonds, price, uid, datetime.now().isoformat())
        )
        await db.commit()
        return order_id

async def get_order(order_id):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,))
        return await cursor.fetchone()

async def update_order_status(order_id, status):
    async with aiosqlite.connect(DB_NAME) as db:
        completed_at = datetime.now().isoformat() if status == "Completed" else None
        await db.execute(
            "UPDATE orders SET status = ?, completed_at = ? WHERE order_id = ?",
            (status, completed_at, order_id)
        )
        await db.commit()

async def get_user_orders(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC", (user_id,)
        )
        return await cursor.fetchall()

async def get_orders_by_status(status):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM orders WHERE status = ? ORDER BY id DESC", (status,)
        )
        return await cursor.fetchall()


# ========== DEPOSIT ==========
async def create_deposit(user_id, amount, method, trx_id):
    async with aiosqlite.connect(DB_NAME) as db:
        try:
            await db.execute(
                """INSERT INTO deposits 
                   (user_id, amount, method, trx_id, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (user_id, amount, method, trx_id, datetime.now().isoformat())
            )
            await db.commit()
            return True
        except aiosqlite.IntegrityError:
            return False

async def get_pending_deposits():
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM deposits WHERE status = 'Pending' ORDER BY id DESC"
        )
        return await cursor.fetchall()

async def update_deposit_status(deposit_id, status, reason=None):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE deposits SET status = ?, reject_reason = ?, processed_at = ? WHERE id = ?",
            (status, reason, datetime.now().isoformat(), deposit_id)
        )
        await db.commit()

async def get_deposit(deposit_id):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM deposits WHERE id = ?", (deposit_id,))
        return await cursor.fetchone()


# ========== SETTINGS ==========
async def get_setting(key):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = await cursor.fetchone()
        return row[0] if row else None

async def set_setting(key, value):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, str(value))
        )
        await db.commit()


# ========== PROMO ==========
async def add_promo(code, discount, max_uses, min_purchase, expiry_date, discount_type="fixed"):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """INSERT INTO promo_codes 
               (code, discount, discount_type, max_uses, min_purchase, expiry_date)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (code, discount, discount_type, max_uses, min_purchase, expiry_date)
        )
        await db.commit()

async def get_promo(code):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM promo_codes WHERE code = ? AND is_active = 1", (code,)
        )
        return await cursor.fetchone()


# ========== ADMIN ==========
async def is_admin(user_id):
    from config import ADMINS
    if user_id in ADMINS:
        return True
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT 1 FROM admins WHERE user_id = ?", (user_id,))
        return await cursor.fetchone() is not None

async def add_admin(user_id, role="Admin"):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR REPLACE INTO admins (user_id, role) VALUES (?, ?)",
            (user_id, role)
        )
        await db.commit()

async def remove_admin(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM admins WHERE user_id = ?", (user_id,))
        await db.commit()


# ========== STATS ==========
async def get_stats():
    async with aiosqlite.connect(DB_NAME) as db:
        stats = {}
        cursor = await db.execute("SELECT COUNT(*) FROM users")
        stats["total_users"] = (await cursor.fetchone())[0]

        cursor = await db.execute("SELECT COUNT(*) FROM users WHERE is_banned = 0")
        stats["active_users"] = (await cursor.fetchone())[0]

        cursor = await db.execute("SELECT COUNT(*) FROM users WHERE is_banned = 1")
        stats["banned_users"] = (await cursor.fetchone())[0]

        cursor = await db.execute("SELECT COUNT(*) FROM orders")
        stats["total_orders"] = (await cursor.fetchone())[0]

        cursor = await db.execute("SELECT COUNT(*) FROM orders WHERE status = 'Pending'")
        stats["pending_orders"] = (await cursor.fetchone())[0]

        cursor = await db.execute("SELECT COUNT(*) FROM orders WHERE status = 'Completed'")
        stats["completed_orders"] = (await cursor.fetchone())[0]

        cursor = await db.execute("SELECT COALESCE(SUM(amount), 0) FROM deposits WHERE status = 'Approved'")
        stats["total_deposits"] = (await cursor.fetchone())[0]

        cursor = await db.execute("SELECT COALESCE(SUM(price), 0) FROM orders WHERE status = 'Completed'")
        stats["total_sales"] = (await cursor.fetchone())[0]

        return stats
