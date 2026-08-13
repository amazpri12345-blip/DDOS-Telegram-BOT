import secrets, sqlite3, string
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Bot configuration
TOKEN = "8639810090:AAFOZieP3RyttBslr8aWJOprV3nWXUOYkLo"
ADMIN_IDS = {7218406158}
DB = "bot.db"

def db():
    c = sqlite3.connect(DB)
    c.execute("CREATE TABLE IF NOT EXISTS users(user_id INTEGER PRIMARY KEY,premium INTEGER DEFAULT 0,key TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS keys(key TEXT PRIMARY KEY,days INTEGER,used_by INTEGER)")
    c.commit()
    return c

def prem(uid):
    c = db()
    r = c.execute("SELECT premium FROM users WHERE user_id=?", (uid,)).fetchone()
    c.close()
    return bool(r and r[0])

def make_key():
    letters = ''.join(secrets.choice(string.ascii_letters) for _ in range(4))
    digits = ''.join(secrets.choice(string.digits) for _ in range(4))
    return f"Nexus_{letters}_{digits}"

async def start(u, ctx):
    uid = u.effective_user.id
    c = db()
    c.execute("INSERT OR IGNORE INTO users(user_id) VALUES(?)", (uid,))
    c.commit(); c.close()
    await u.message.reply_text(
        f"❄️ Welcome to Nexus Checker\n\nUser ID ➜ {uid}\n"
        f"Access ➜ {'PREMIUM' if prem(uid) else 'FREE'}\n\n"
        "Sandbox/test data only.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Checker", callback_data="checker")],
            [InlineKeyboardButton("Premium", callback_data="premium"),
             InlineKeyboardButton("Support", callback_data="support")]
        ])
    )

async def checker(u, ctx):
    q = u.callback_query; await q.answer()
    await q.edit_message_text(
        "Gates Status:\nSingle Gates ➜ DEMO\nMass Gates ➜ DEMO\n\nSelect Checker Type",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Single", callback_data="single"),
             InlineKeyboardButton("Mass", callback_data="mass")],
            [InlineKeyboardButton("« Back", callback_data="back")]
        ])
    )

async def single(u, ctx):
    q = u.callback_query; await q.answer()
    await q.edit_message_text(
        "Single Checker\n\nDemo/sandbox validation only.\n"
        "Real payment-card authorization is disabled."
    )

async def mass(u, ctx):
    q = u.callback_query; await q.answer()
    await q.edit_message_text(
        "⭐ Premium Mass Checker\n\nDemo/sandbox data only."
        if prem(q.from_user.id)
        else "🔒 Mass Checker is Premium.\nUse /redeem YOUR_KEY"
    )

async def premium(u, ctx):
    q = u.callback_query; await q.answer()
    await q.edit_message_text(
        "⭐ Premium Access\n\nAdmin: /gen DAYS QUANTITY\nUser: /redeem YOUR_KEY"
    )

async def support(u, ctx):
    q = u.callback_query; await q.answer()
    await q.edit_message_text("🛠 Configure your support contact in bot.py.")

async def back(u, ctx):
    q = u.callback_query; await q.answer()
    await q.edit_message_text(
        "❄️ Nexus Checker",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Checker", callback_data="checker"),
             InlineKeyboardButton("Premium", callback_data="premium")]
        ])
    )

async def gen(u, ctx):
    if u.effective_user.id not in ADMIN_IDS:
        await u.message.reply_text("⛔ Admin only.")
        return
    if len(ctx.args) != 2:
        await u.message.reply_text("Usage: /gen DAYS QUANTITY\nExample: /gen 30 10")
        return
    try:
        days, qty = int(ctx.args[0]), int(ctx.args[1])
    except ValueError:
        await u.message.reply_text("❌ DAYS and QUANTITY must be numbers.")
        return
    if not 1 <= days <= 3650 or not 1 <= qty <= 100:
        await u.message.reply_text("❌ DAYS: 1-3650, QUANTITY: 1-100.")
        return

    c = db()
    keys = []
    for _ in range(qty):
        while True:
            key = make_key()
            try:
                c.execute("INSERT INTO keys VALUES(?,?,NULL)", (key, days))
                keys.append(key)
                break
            except sqlite3.IntegrityError:
                pass
    c.commit(); c.close()
    await u.message.reply_text(
        f"✅ Generated {qty} premium key(s)\nDuration: {days} days\n\n" +
        "\n".join(keys)
    )

async def redeem(u, ctx):
    if not ctx.args:
        await u.message.reply_text("Usage: /redeem YOUR_KEY")
        return
    key = ctx.args[0].strip()
    c = db()
    r = c.execute("SELECT days,used_by FROM keys WHERE key=?", (key,)).fetchone()
    if not r:
        c.close(); await u.message.reply_text("❌ Invalid key."); return
    if r[1] is not None:
        c.close(); await u.message.reply_text("❌ Key already used."); return

    c.execute("INSERT OR IGNORE INTO users(user_id) VALUES(?)", (u.effective_user.id,))
    c.execute("UPDATE keys SET used_by=? WHERE key=?", (u.effective_user.id, key))
    c.execute("UPDATE users SET premium=1,key=? WHERE user_id=?", (key, u.effective_user.id))
    c.commit(); c.close()
    await u.message.reply_text(f"⭐ Premium activated for {r[0]} days.")

async def status(u, ctx):
    await u.message.reply_text(
        f"Access ➜ {'PREMIUM' if prem(u.effective_user.id) else 'FREE'}"
    )

app = Application.builder().token(TOKEN).build()

for cmd, fn in [("start", start), ("gen", gen), ("redeem", redeem), ("status", status)]:
    app.add_handler(CommandHandler(cmd, fn))

for pat, fn in [
    ("checker", checker), ("single", single), ("mass", mass),
    ("premium", premium), ("support", support), ("back", back)
]:
    app.add_handler(CallbackQueryHandler(fn, pattern=f"^{pat}$"))

app.run_polling()
