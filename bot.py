import os
import json
import asyncio
from datetime import datetime, time
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import pytz

# ─── KONFİQURASİYA ───────────────────────────────────────────────
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8576432885:AAHQBY3aKVmKH9v9H6oysd16s9hH9ym1fXQ")
MANAGER_ID = int(os.environ.get("MANAGER_ID", "0"))  # Sənin Telegram ID-n
STANDUP_HOUR = int(os.environ.get("STANDUP_HOUR", "9"))   # Standup saatı (09:00)
STANDUP_MINUTE = int(os.environ.get("STANDUP_MINUTE", "0"))
TIMEZONE = os.environ.get("TIMEZONE", "Asia/Baku")

# Mühəndislər: { telegram_id: ad }
ENGINEERS = {}  # /adduser əmri ilə doldurulur

# ─── VƏZİYYƏT SAXLAYıCı ──────────────────────────────────────────
# { user_id: { "step": 0/1/2, "answers": [] } }
sessions = {}

# { date_str: { user_id: { "name": ..., "answers": [...] } } }
standup_data = {}

QUESTIONS = [
    "✅ Dünən nə etdin?",
    "🎯 Bu gün nə edəcəksən?",
    "🚧 Sənə mane olan bir şey varmı?"
]

DATA_FILE = "data.json"

def load_data():
    global ENGINEERS, standup_data
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            d = json.load(f)
            ENGINEERS = {int(k): v for k, v in d.get("engineers", {}).items()}
            standup_data = d.get("standup_data", {})

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump({
            "engineers": {str(k): v for k, v in ENGINEERS.items()},
            "standup_data": standup_data
        }, f, ensure_ascii=False, indent=2)

# ─── ƏMRLƏR ──────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Salam! Mən Standup Botuyam 🤖\n\n"
        "Hər səhər saat 09:00-da sənə 3 sual verəcəyəm.\n"
        "Rəhbər sizi əlavə etdikdən sonra avtomatik işə düşəcəyəm.\n\n"
        f"Sənin ID-n: <code>{update.effective_user.id}</code>\n"
        "Bu ID-ni rəhbərə ver.",
        parse_mode="HTML"
    )

async def add_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Yalnız rəhbər istifadə edə bilər: /adduser 123456789 Ad Soyad"""
    if update.effective_user.id != MANAGER_ID:
        await update.message.reply_text("❌ Bu əmri yalnız rəhbər istifadə edə bilər.")
        return
    if len(context.args) < 2:
        await update.message.reply_text("İstifadə: /adduser [telegram_id] [Ad]")
        return
    uid = int(context.args[0])
    name = " ".join(context.args[1:])
    ENGINEERS[uid] = name
    save_data()
    await update.message.reply_text(f"✅ {name} ({uid}) əlavə edildi.")

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != MANAGER_ID:
        return
    if not ENGINEERS:
        await update.message.reply_text("Hələ heç kim əlavə edilməyib.")
        return
    text = "👥 Komanda:\n"
    for uid, name in ENGINEERS.items():
        text += f"• {name} ({uid})\n"
    await update.message.reply_text(text)

async def remove_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != MANAGER_ID:
        return
    if not context.args:
        await update.message.reply_text("İstifadə: /removeuser [telegram_id]")
        return
    uid = int(context.args[0])
    name = ENGINEERS.pop(uid, None)
    save_data()
    if name:
        await update.message.reply_text(f"✅ {name} silindi.")
    else:
        await update.message.reply_text("Belə istifadəçi tapılmadı.")

async def standup_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Rəhbər manual olaraq standupı başlatmaq üçün: /standupnow"""
    if update.effective_user.id != MANAGER_ID:
        return
    await trigger_standup(context.application.bot)
    await update.message.reply_text("✅ Standup göndərildi.")

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bu günün hesabatı: /report"""
    if update.effective_user.id != MANAGER_ID:
        return
    await send_report(context.application.bot, update.effective_chat.id)

# ─── STANDUP MƏNTIQI ─────────────────────────────────────────────

async def trigger_standup(bot: Bot):
    """Bütün mühəndislərə standup suallarını göndər"""
    if not ENGINEERS:
        return
    for uid in ENGINEERS:
        sessions[uid] = {"step": 0, "answers": []}
        try:
            await bot.send_message(
                chat_id=uid,
                text=f"🌅 Sabahın xeyir! Günlük standup vaxtı.\n\n{QUESTIONS[0]}"
            )
        except Exception as e:
            print(f"Xəta {uid}: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in ENGINEERS:
        await update.message.reply_text(
            f"Salam! Sən hələ komandaya əlavə edilməmisən.\n"
            f"ID-ni rəhbərə ver: <code>{uid}</code>",
            parse_mode="HTML"
        )
        return

    if uid not in sessions:
        await update.message.reply_text("Standup hələ başlamamışdır. Rəhbər /standupnow əmri ilə başlada bilər.")
        return

    session = sessions[uid]
    step = session["step"]
    session["answers"].append(update.message.text)
    session["step"] += 1

    if session["step"] < len(QUESTIONS):
        # Növbəti sual
        await update.message.reply_text(QUESTIONS[session["step"]])
    else:
        # Bütün suallar cavablandı
        today = datetime.now(pytz.timezone(TIMEZONE)).strftime("%Y-%m-%d")
        if today not in standup_data:
            standup_data[today] = {}
        standup_data[today][str(uid)] = {
            "name": ENGINEERS[uid],
            "answers": session["answers"],
            "time": datetime.now(pytz.timezone(TIMEZONE)).strftime("%H:%M")
        }
        save_data()
        del sessions[uid]

        await update.message.reply_text(
            "✅ Təşəkkür edirik! Cavabların qeyd edildi.\n"
            "Uğurlu iş günü! 💪"
        )

        # Rəhbərə bildiriş
        answered = len(standup_data[today])
        total = len(ENGINEERS)
        if MANAGER_ID:
            try:
                await context.application.bot.send_message(
                    chat_id=MANAGER_ID,
                    text=f"📊 {ENGINEERS[uid]} standup-u tamamladı. ({answered}/{total})"
                )
            except:
                pass

        # Hamı cavab verdisə tam hesabat göndər
        if answered == total:
            await send_report(context.application.bot, MANAGER_ID)

async def send_report(bot: Bot, chat_id: int):
    """Bu günün tam hesabatını göndər"""
    today = datetime.now(pytz.timezone(TIMEZONE)).strftime("%Y-%m-%d")
    data = standup_data.get(today, {})

    text = f"📋 *Günlük Standup Hesabatı*\n📅 {today}\n\n"

    answered_ids = set(data.keys())
    all_ids = set(str(uid) for uid in ENGINEERS.keys())

    for uid_str, entry in data.items():
        text += f"👤 *{entry['name']}* ({entry['time']})\n"
        text += f"✅ {entry['answers'][0]}\n"
        text += f"🎯 {entry['answers'][1]}\n"
        blocker = entry['answers'][2]
        if blocker.lower() in ["yox", "xeyr", "yoxdur", "heç nə", "hec ne", "no", "yok"]:
            text += f"🟢 Maneə yoxdur\n"
        else:
            text += f"🔴 *Maneə: {blocker}*\n"
        text += "\n"

    missing = all_ids - answered_ids
    if missing:
        text += "⚠️ *Cavab verməyənlər:*\n"
        for uid_str in missing:
            uid = int(uid_str)
            text += f"• {ENGINEERS.get(uid, uid_str)}\n"

    try:
        await bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")
    except Exception as e:
        print(f"Hesabat göndərilmədi: {e}")

# ─── ZAMANLAYICI ──────────────────────────────────────────────────

async def schedule_standup(app):
    tz = pytz.timezone(TIMEZONE)
    while True:
        now = datetime.now(tz)
        target = now.replace(hour=STANDUP_HOUR, minute=STANDUP_MINUTE, second=0, microsecond=0)
        if now >= target:
            target = target.replace(day=target.day + 1)
        wait_seconds = (target - now).total_seconds()
        print(f"Növbəti standup: {target.strftime('%Y-%m-%d %H:%M')} ({wait_seconds:.0f} saniyə sonra)")
        await asyncio.sleep(wait_seconds)
        await trigger_standup(app.bot)

# ─── ANA FUNKSIYA ─────────────────────────────────────────────────

def main():
    load_data()
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("adduser", add_user))
    app.add_handler(CommandHandler("listusers", list_users))
    app.add_handler(CommandHandler("removeuser", remove_user))
    app.add_handler(CommandHandler("standupnow", standup_now))
    app.add_handler(CommandHandler("report", report))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    async def post_init(app):
        asyncio.create_task(schedule_standup(app))

    app.post_init = post_init

    print("Bot işə düşdü...")
    app.run_polling()

if __name__ == "__main__":
    main()
