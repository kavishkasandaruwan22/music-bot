import json
import requests
from bs4 import BeautifulSoup
from rapidfuzz import process, fuzz

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

TOKEN = "8659920045:AAEC5zc1t7R_tBOmxJmpGIkxjV5-GL_FQzc"

# ---------------- LOAD SONGS ----------------
with open("songs.json", "r", encoding="utf-8") as f:
    SONGS = json.load(f)


# ---------------- SEARCH ----------------
def search_songs(query):
    titles = [s["title"] for s in SONGS]
    results = process.extract(query, titles, scorer=fuzz.WRatio, limit=10)

    matched = []
    for title, score, idx in results:
        if score > 40:
            matched.append(SONGS[idx])

    return matched


# ---------------- EXTRACT MP3 ----------------
def get_mp3_from_page(url):
    try:
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        button = soup.find("button", attrs={"url": True})
        if button:
            return button["url"]

        return None

    except Exception as e:
        print("Error:", e)
        return None


# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("[BOT STARTED]")
    await update.message.reply_text("🎵 Send a song name to search.")


# ---------------- MESSAGE HANDLER ----------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.lower()

    # ✅ CMD LOGGING
    print("=" * 50)
    print(f"[USER MESSAGE] {update.message.chat_id} -> {update.message.text}")

    # 💖 THARUSHIKA SPECIAL MODE
    if "tharushika" in query:
        print("[LOVE MODE TRIGGERED]")
        await update.message.reply_text(
            "💖 Special Search Mode Activated 💖\n\n"
            "For Tharushika 🌸\n"
            "Every song here carries a feeling, not just sound.\n"
            "Some names are meant to be remembered forever.\n\n"
            "🎧 Finding beautiful songs for her..."
        )

    results = search_songs(query)

    # CMD LOGGING
    print(f"[SEARCH QUERY] {query}")
    print(f"[RESULT COUNT] {len(results)}")

    if not results:
        print("[NO RESULTS FOUND]")
        await update.message.reply_text("❌ No songs found")
        return

    keyboard = []

    for i, song in enumerate(results):
        keyboard.append([
            InlineKeyboardButton(
                song["title"],
                callback_data=str(i)
            )
        ])

    context.user_data["results"] = results

    await update.message.reply_text(
        "🎧 Select a song:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ---------------- BUTTON CLICK ----------------
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    results = context.user_data.get("results", [])
    idx = int(query.data)

    if idx >= len(results):
        print("[INVALID BUTTON CLICK]")
        return

    song = results[idx]
    link = song["link"]

    print("=" * 50)
    print(f"[SONG SELECTED] {song['title']}")
    print(f"[LINK] {link}")

    await query.message.reply_text("⏳ Fetching audio...")

    mp3 = get_mp3_from_page(link)

    if mp3:
        print(f"[MP3 FOUND] {mp3}")

        await context.bot.send_audio(
            chat_id=query.message.chat_id,
            audio=mp3,
            title=song["title"],
            caption="🎵 Enjoy the music 💖"
        )
    else:
        print("[MP3 NOT FOUND]")
        await query.message.reply_text(f"❌ MP3 not found\n🔗 {link}")


# ---------------- ERROR HANDLER ----------------
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    print("[ERROR]")
    print(context.error)


# ---------------- MAIN ----------------
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_click))
    app.add_error_handler(error_handler)

    print("🤖 Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()