import os
import json
import hashlib
import requests
import feedparser
from datetime import datetime
from zoneinfo import ZoneInfo

TOKEN = os.environ["BOT_TOKEN"]
CHANNEL = os.environ["CHANNEL_ID"]

HISTORY_FILE = "news_history.json"

TEHRAN = ZoneInfo("Asia/Tehran")

FEEDS = [
    "https://fouladban.com/feed/",
]

KEYWORDS = [
    "فولاد",
    "آهن",
    "میلگرد",
    "تیرآهن",
    "شمش",
    "بورس کالا",
    "بورس",
    "دلار",
    "طلا",
    "سکه",
    "ارز",
    "بانک مرکزی",
    "وزارت صمت",
    "صادرات",
    "واردات",
    "نفت",
    "پتروشیمی",
    "اقتصاد",
]


def load_history():

    if not os.path.exists(HISTORY_FILE):
        return set()

    try:
        with open(
            HISTORY_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            return set(json.load(f))

    except:
        return set()


def save_history(history):

    with open(
        HISTORY_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            list(history)[-500:],
            f,
            ensure_ascii=False,
            indent=2
        )


def make_id(title, link):

    text = title + link

    return hashlib.sha256(
        text.encode("utf-8")
    ).hexdigest()


def is_relevant(title, summary):

    text = (
        title + " " + summary
    ).lower()

    return any(
        keyword.lower() in text
        for keyword in KEYWORDS
    )


def get_news():

    news = []

    for feed_url in FEEDS:

        try:

            response = requests.get(
                feed_url,
                headers={
                    "User-Agent": "Mozilla/5.0"
                },
                timeout=20
            )

            response.raise_for_status()

            feed = feedparser.parse(
                response.content
            )

            for item in feed.entries[:20]:

                title = item.get(
                    "title",
                    ""
                ).strip()

                link = item.get(
                    "link",
                    ""
                ).strip()

                summary = item.get(
                    "summary",
                    ""
                ).strip()

                if not title or not link:
                    continue

                if not is_relevant(
                    title,
                    summary
                ):
                    continue

                news_id = make_id(
                    title,
                    link
                )

                news.append({
                    "id": news_id,
                    "title": title,
                    "link": link,
                    "summary": summary
                })

        except Exception as e:

            print(
                "Feed error:",
                feed_url,
                e
            )

    return news


def clean_summary(text):

    text = text.replace(
        "<p>",
        ""
    )

    text = text.replace(
        "</p>",
        ""
    )

    text = text.replace(
        "<br>",
        "\n"
    )

    return text.strip()


def send_news(news):

    title = news["title"]

    summary = clean_summary(
        news["summary"]
    )

    if len(summary) > 500:
        summary = summary[:500] + "..."

    message = (
        "🚨 <b>خبر فوری اقتصادی</b>\n\n"
        f"📌 <b>{title}</b>\n\n"
    )

    if summary:
        message += (
            f"{summary}\n\n"
        )

    message += (
        f"📰 منبع: فولادبان\n"
        f"🔗 {news['link']}\n\n"
        "🆔 @Arvand_Aron_Steel\n"
        "☎️ 021-22122239"
    )

    response = requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={
            "chat_id": CHANNEL,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": False
        },
        timeout=30
    )

    response.raise_for_status()

    print(
        "News sent:",
        title
    )


history = load_history()

news = get_news()

news.sort(
    key=lambda x: x["id"]
)

sent = 0

for item in news:

    if item["id"] in history:
        continue

    send_news(item)

    history.add(
        item["id"]
    )

    sent += 1

    # در هر اجرا حداکثر 2 خبر
    if sent >= 2:
        break


save_history(history)

print(
    f"News check finished. Sent: {sent}"
)