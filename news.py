import os
import re
import json
import hashlib
import requests
import feedparser
from datetime import datetime, timezone

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

HISTORY_FILE = "news_history.json"

RSS_FEEDS = [
    ("Reuters Business", "https://feeds.reuters.com/reuters/businessNews"),
    ("Google Finance", "https://news.google.com/rss/search?q=economy+steel+iron+market&hl=en-US&gl=US&ceid=US:en"),
    ("Google Iran Economy", "https://news.google.com/rss/search?q=Iran+economy+currency+steel&hl=en-US&gl=US&ceid=US:en"),
]

KEYWORDS = [
    "steel", "iron", "metal", "ore", "copper",
    "oil", "energy", "tariff", "sanction",
    "inflation", "interest rate", "fed",
    "dollar", "currency", "china",
    "iran", "ایران", "فولاد", "آهن", "میلگرد",
    "دلار", "ارز", "تحریم", "بورس", "تورم"
]

def clean(text):
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def load_history():
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except Exception:
        return set()


def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(list(history)[-500:], f, ensure_ascii=False, indent=2)


def make_id(title, link):
    return hashlib.sha256(
        (title + link).encode("utf-8")
    ).hexdigest()


def relevance(title, summary):
    text = (title + " " + summary).lower()

    score = 0

    for keyword in KEYWORDS:
        if keyword.lower() in text:
            score += 1

    return score


def impact_analysis(title, summary):
    text = (title + " " + summary).lower()

    bullish_words = [
        "tariff", "sanction", "shortage", "supply cut",
        "oil rises", "inflation rises", "dollar rises",
        "yuan weakens", "stimulus", "demand rises",
        "قیمت دلار", "افزایش دلار", "تحریم",
        "کاهش عرضه", "افزایش تقاضا", "تورم"
    ]

    bearish_words = [
        "demand falls", "recession", "oversupply",
        "production rises", "steel demand drops",
        "oil falls", "interest rate hike",
        "دلار کاهش", "کاهش تقاضا", "رکود",
        "افزایش عرضه", "کاهش قیمت"
    ]

    bullish = sum(word.lower() in text for word in bullish_words)
    bearish = sum(word.lower() in text for word in bearish_words)

    if bullish > bearish:
        return (
            "🟢 صعودی",
            "این خبر می‌تواند در کوتاه‌مدت از افزایش قیمت آهن و فولاد حمایت کند.",
            "متوسط"
        )

    if bearish > bullish:
        return (
            "🔴 کاهشی",
            "این خبر می‌تواند در کوتاه‌مدت فشار کاهشی روی قیمت آهن و فولاد ایجاد کند.",
            "متوسط"
        )

    return (
        "🟡 خنثی / نامشخص",
        "اثر مستقیم این خبر بر بازار آهن و فولاد قطعی نیست و باید واکنش بازار بررسی شود.",
        "کم"
    )


def telegram_send(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    response = requests.post(
        url,
        data={
            "chat_id": CHANNEL_ID,
            "text": message,
            "disable_web_page_preview": False
        },
        timeout=30
    )

    if response.status_code != 200:
        print("Telegram error:", response.text)

    return response.status_code == 200


def main():

    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is missing")

    if not CHANNEL_ID:
        raise RuntimeError("CHANNEL_ID is missing")

    history = load_history()

    candidates = []

    for source_name, feed_url in RSS_FEEDS:

        try:
            print("Reading:", source_name)

            feed = feedparser.parse(feed_url)

            for entry in feed.entries[:15]:

                title = clean(entry.get("title", ""))
                summary = clean(entry.get("summary", ""))
                link = entry.get("link", "")

                if not title or not link:
                    continue

                news_id = make_id(title, link)

                if news_id in history:
                    continue

                score = relevance(title, summary)

                if score <= 0:
                    continue

                candidates.append({
                    "id": news_id,
                    "source": source_name,
                    "title": title,
                    "summary": summary,
                    "link": link,
                    "score": score
                })

        except Exception as e:
            print("Feed error:", source_name, e)

    candidates.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    if not candidates:
        print("No new relevant news.")
        save_history(history)
        return

    # حداکثر 3 خبر در هر اجرا
    selected = candidates[:3]

    for item in selected:

        direction, explanation, strength = impact_analysis(
            item["title"],
            item["summary"]
        )

        message = (
            "📰 خبر مهم اقتصادی\n\n"
            f"🔹 {item['title']}\n\n"
            f"📌 منبع: {item['source']}\n\n"
            "━━━━━━━━━━━━━━\n"
            "📊 تأثیر احتمالی بر بازار آهن و فولاد\n\n"
            f"جهت اثر: {direction}\n"
            f"شدت اثر: {strength}\n\n"
            f"💡 تحلیل: {explanation}\n\n"
            f"🔗 منبع خبر:\n{item['link']}\n\n"
            "━━━━━━━━━━━━━━\n"
            "⚠️ این تحلیل برآورد احتمالی بازار است و توصیه خرید یا فروش نیست."
        )

        print("\nSending:", item["title"])

        if telegram_send(message):
            print("SENT OK")
            history.add(item["id"])

    save_history(history)


if __name__ == "__main__":
    main()