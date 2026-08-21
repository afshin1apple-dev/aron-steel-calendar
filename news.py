import os
import json
import hashlib
import re
import requests
import feedparser
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from html import unescape

TOKEN = os.environ["BOT_TOKEN"]
CHANNEL = os.environ["CHANNEL_ID"]

HISTORY_FILE = "news_history.json"

TEHRAN = ZoneInfo("Asia/Tehran")

# ---------------------------------
# منابع خبری
# ---------------------------------

FEEDS = [
    # ایران
    {
        "name": "فولادبان",
        "url": "https://fouladban.com/feed/",
        "foreign": False,
    },

    # Reuters
    {
        "name": "Reuters",
        "url": "https://www.reuters.com/my-news/feed/",
        "foreign": True,
    },

    # Financial Times
    {
        "name": "Financial Times",
        "url": "https://www.ft.com/?format=rss",
        "foreign": True,
    },

    # Commodity / S&P Global
    {
        "name": "S&P Global Commodity",
        "url": "https://www.spglobal.com/commodityinsights/en/rss-feeds",
        "foreign": True,
    },
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
    "سوخت",
    "بنزین",
    "steel",
    "iron",
    "rebar",
    "billet",
    "commodity",
    "commodities",
    "oil",
    "gold",
    "copper",
    "aluminum",
    "inflation",
    "economy",
    "economic",
    "market",
    "markets",
    "tariff",
    "trade",
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

    except Exception:
        return set()


def save_history(history):

    with open(
        HISTORY_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            list(history)[-1000:],
            f,
            ensure_ascii=False,
            indent=2
        )


def make_id(title, link):

    return hashlib.sha256(
        (title + link).encode("utf-8")
    ).hexdigest()


def clean_text(text):

    if not text:
        return ""

    text = unescape(text)

    text = re.sub(
        r"<[^>]+>",
        " ",
        text
    )

    garbage = [
        r"اولین بار در فولادبان.*",
        r"پدیدار شد.*",
        r"this article first appeared.*",
    ]

    for pattern in garbage:

        text = re.sub(
            pattern,
            "",
            text,
            flags=re.IGNORECASE
        )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def is_relevant(title, summary):

    text = (
        title + " " + summary
    ).lower()

    return any(
        word.lower() in text
        for word in KEYWORDS
    )


def get_item_date(item):

    published = item.get(
        "published_parsed"
    )

    if not published:

        published = item.get(
            "updated_parsed"
        )

    if not published:
        return None

    try:

        dt = datetime(
            *published[:6],
            tzinfo=timezone.utc
        )

        return dt.astimezone(
            TEHRAN
        )

    except Exception:

        return None


def get_news():

    all_news = []

    today = datetime.now(
        TEHRAN
    ).date()

    for source in FEEDS:

        print(
            "Checking:",
            source["name"]
        )

        try:

            response = requests.get(
                source["url"],
                headers={
                    "User-Agent":
                        "Mozilla/5.0"
                },
                timeout=20
            )

            if not response.ok:

                print(
                    "Feed unavailable:",
                    source["name"],
                    response.status_code
                )

                continue

            feed = feedparser.parse(
                response.content
            )

            print(
                source["name"],
                "items:",
                len(feed.entries)
            )

            for item in feed.entries[:30]:

                title = clean_text(
                    item.get(
                        "title",
                        ""
                    )
                )

                link = item.get(
                    "link",
                    ""
                ).strip()

                summary = clean_text(
                    item.get(
                        "summary",
                        ""
                    )
                )

                if not title or not link:
                    continue

                item_date = get_item_date(
                    item
                )

                # اگر تاریخ مشخص نبود، رد کن
                if item_date is None:

                    print(
                        "No date:",
                        title
                    )

                    continue

                # فقط امروز
                if item_date.date() != today:

                    continue

                # فیلتر اقتصادی
                if not is_relevant(
                    title,
                    summary
                ):

                    continue

                news_id = make_id(
                    title,
                    link
                )

                all_news.append({

                    "id": news_id,

                    "title": title,

                    "link": link,

                    "summary": summary,

                    "source":
                        source["name"],

                    "foreign":
                        source["foreign"],

                    "date":
                        item_date
                })

        except Exception as e:

            print(
                "ERROR:",
                source["name"],
                str(e)
            )

    # جدیدترین اول
    all_news.sort(
        key=lambda x: x["date"],
        reverse=True
    )

    return all_news


def translate_title(title):

    # ترجمه کاملاً رایگان و بدون API
    # فعلاً برای جلوگیری از خطای سرویس خارجی
    # اگر عنوان انگلیسی بود، همان عنوان را نگه می‌داریم

    return title


def send_news(news):

    title = clean_text(
        news["title"]
    )

    summary = clean_text(
        news["summary"]
    )

    source = news["source"]

    if news["foreign"]:

        title = translate_title(
            title
        )

        header = (
            "🌍 <b>خبر اقتصادی جهان</b>"
        )

    else:

        header = (
            "🇮🇷 <b>خبر اقتصادی ایران</b>"
        )

    if len(summary) > 450:

        summary = (
            summary[:450]
            + "..."
        )

    message = (
        f"{header}\n\n"
        f"📌 <b>{title}</b>\n\n"
    )

    if summary:

        message += (
            f"📝 {summary}\n\n"
        )

    message += (
        f"📰 منبع: {source}\n"
        f"🔗 {news['link']}\n\n"
        "🆔 @Arvand_Aron_Steel\n"
        "☎️ 021-22122239"
    )

    response = requests.post(

        f"https://api.telegram.org/"
        f"bot{TOKEN}/sendMessage",

        data={

            "chat_id": CHANNEL,

            "text": message,

            "parse_mode": "HTML",

            "disable_web_page_preview": False
        },

        timeout=30
    )

    if not response.ok:

        print(
            "Telegram error:",
            response.text
        )

    response.raise_for_status()

    print(
        "SENT:",
        title
    )


# =================================
# ساعت انتشار
# =================================

now = datetime.now(
    TEHRAN
)

start_time = now.replace(
    hour=8,
    minute=30,
    second=0,
    microsecond=0
)

end_time = now.replace(
    hour=17,
    minute=0,
    second=0,
    microsecond=0
)

if not (
    start_time
    <= now
    <= end_time
):

    print(
        "Outside schedule."
    )

    exit()


# =================================
# اجرای اصلی
# =================================

history = load_history()

news = get_news()

print(
    "Today's relevant news:",
    len(news)
)

sent = 0

for item in news:

    if item["id"] in history:

        continue

    try:

        send_news(item)

        history.add(
            item["id"]
        )

        sent += 1

    except Exception as e:

        print(
            "Send error:",
            str(e)
        )

    # حداکثر 2 خبر در هر اجرا
    if sent >= 2:

        break


save_history(history)

print(
    f"Finished. Sent: {sent}"
)