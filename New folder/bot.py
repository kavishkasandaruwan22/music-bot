import requests
from bs4 import BeautifulSoup
import json
import time
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

BASE_URL = "https://songhub.lk/song"
PAGES = 1025

DATA_FILE = "songs.json"

BOT_TOKEN = "8659920045:AAEC5zc1t7R_tBOmxJmpGIkxjV5-GL_FQzc"


# -----------------------------
# SCRAPER FUNCTION
# -----------------------------
def scrape_all():
    all_songs = []

    print("Starting scraping...")

    for page in range(1, PAGES + 1):
        url = f"{BASE_URL}?page={page}"
        print(f"Scraping page {page}/{PAGES}")

        try:
            r = requests.get(url, timeout=10)
            soup = BeautifulSoup(r.text, "html.parser")

            items = soup.select("div.item a")

            for item in items:
                link = item.get("href")
                title_tag = item.select_one("span")

                title = title_tag.text.strip() if title_tag else "Unknown"

                all_songs.append({
                    "title": title.lower(),
                    "link": link
                })

        except Exception as e:
            print("Error:", e)

        time.sleep(0.2)

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(all_songs, f, indent=4, ensure_ascii=False)

    print(f"\nDONE! Saved {len(all_songs)} songs into {DATA_FILE}")


# -----------------------------
# LOAD DATA
# -----------------------------
def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []


# -----------------------------
# SEARCH FUNCTION (BEST MATCH)
# -----------------------------
def search_songs(query, data):
    query = query.lower().split()

    results = []

    for song in data:
        score = 0
        title = song["title"]

        for q in query:
            if q in title:
                score += 1

        if score > 0:
            results.append((score, song))

    results.sort(key=lambda x: x[0], reverse=True)

    return [r[1] for r in results[:10]]


# -----------------------------
# TELEGRAM COMMANDS
# -----------------------------
def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Send song name or /scrape to build database."
    )


def scrape_cmd(update: Update, context: CallbackContext):
    update.message.reply_text("Scraping started... check terminal")

    scrape_all()

    update.message.reply_text("DONE ✅ JSON file created with all songs")


def search_cmd(update: Update, context: CallbackContext):
    data = load_data()

    if not data:
        update.message.reply_text("No data found. Run /scrape first.")
        return

    query = " ".join(context.args)

    if not query:
        update.message.reply_text("Usage: /search song name")
        return

    results = search_songs(query, data)

    if not results:
        update.message.reply_text("No match found")
        return

    msg = "🎵 Best Matches:\n\n"

    for r in results:
        msg += f"{r['title']}\n{r['link']}\n\n"

    update.message.reply_text(msg)


# -----------------------------
# NORMAL TEXT HANDLER
# -----------------------------
def handle_message(update: Update, context: CallbackContext):
    data = load_data()

    text = update.message.text.lower()

    if text.startswith("http"):
        update.message.reply_text(
            "Link received ✅\nYou can open it directly or reuse in system."
        )
        return

    results = search_songs(text, data)

    if not results:
        update.message.reply_text("No match found ❌")
        return

    msg = "🎵 Best Match Songs:\n\n"

    for r in results:
        msg += f"{r['title']}\n{r['link']}\n\n"

    msg += "\nNow copy the link and send it again if needed."

    update.message.reply_text(msg)


# -----------------------------
# MAIN BOT
# -----------------------------
def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("scrape", scrape_cmd))
    dp.add_handler(CommandHandler("search", search_cmd))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    print("Bot running...")
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()