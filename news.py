import os
import json
import hashlib
import re
import html
import requests
import feedparser

from datetime import datetime, timezone
from zoneinfo import ZoneInfo


# =========================
# SETTINGS
# =========================

TOKEN = os.environ["BOT_TOKEN"]
CHANNEL = os.environ["CHANNEL_ID"]

PEXELS_API_KEY = os.environ.get(
    "PEXELS_API_KEY",
    ""
)

HISTORY_FILE = "news_history.json"

TEHRAN = ZoneInfo("Asia/Tehran")


# =========================
# NEWS SOURCES
# =========================

FEEDS = [

    {
        "name": "فولادبان",
        "url": "https://fouladban.com/feed/",
        "foreign": False,
    },

    {
        "name": "Reuters",
        "url": "https://www.reuters.com/my-news/feed/",
        "foreign": True,
    },

    {
        "name": "Financial Times",
        "url": "https://www.ft.com/?format=rss",
        "foreign": True,
    },

]


# =========================
# KEYWORDS
# =========================

KEYWORDS = [

    # فارسی
    "اقتصاد",
    "اقتصادی",
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
    "بنزین",
    "سوخت",
    "تورم",
    "بازار",
    "تعرفه",
    "تجارت",

    # English
    "economy",
    "economic",
    "market",
    "markets",
    "steel",
    "iron",
    "rebar",
    "billet",
    "commodity",
    "commodities",
    "oil",
    "gold",
    "silver",
    "copper",
    "aluminum",
    "inflation",
    "interest rate",
    "tariff",
    "trade",
    "bank",
    "energy",
    "fuel",
]


# =========================
# HISTORY
# =========================

def load_history():

    if not os.path.exists(HISTORY_FILE):
        return set()

    try:

        with open(
            HISTORY_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            return set(
                json.load(file)
            )

    except Exception:

        return set()


def save_history(history):

    try:

        with open(
            HISTORY_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                list(history)[-1000:],
                file,
                ensure_ascii=False,
                indent=2
            )

    except Exception as error:

        print(
            "History save error:",
            error
        )


# =========================
# TEXT CLEANING
# =========================

def clean_text(text):

    if not text:
        return ""

    text = html.unescape(text)

    text = re.sub(
        r"<[^>]+>",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    # حذف عبارت‌های اضافه RSS
    bad_parts = [

        "اولین بار در فولادبان",
        "پدیدار شد",
        "This article first appeared",
        "appeared first on",

    ]

    for part in bad_parts:

        index = text.lower().find(
            part.lower()
        )

        if index != -1:

            text = text[:index]

    return text.strip()


# =========================
# NEWS ID
# =========================

def make_id(title, link):

    value = (
        title.strip()
        + link.strip()
    )

    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()


# =========================
# RELEVANCE
# =========================

def is_relevant(title, summary):

    text = (
        title
        + " "
        + summary
    ).lower()

    for keyword in KEYWORDS:

        if keyword.lower() in text:

            return True

    return False


# =========================
# DATE
# =========================

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

        utc_date = datetime(
            *published[:6],
            tzinfo=timezone.utc
        )

        return utc_date.astimezone(
            TEHRAN
        )

    except Exception:

        return None


# =========================
# GET NEWS
# =========================

def get_news():

    result = []

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

                # تاریخ نامشخص
                if item_date is None:

                    print(
                        "No date:",
                        title
                    )

                    continue

                # فقط اخبار امروز
                if item_date.date() != today:

                    continue

                # فقط اخبار اقتصادی
                if not is_relevant(
                    title,
                    summary
                ):

                    continue

                news_id = make_id(
                    title,
                    link
                )

                result.append({

                    "id": news_id,

                    "title": title,

                    "summary": summary,

                    "link": link,

                    "source":
                        source["name"],

                    "foreign":
                        source["foreign"],

                    "date":
                        item_date

                })

        except Exception as error:

            print(
                "Source error:",
                source["name"],
                error
            )

    # جدیدترین خبرها اول
    result.sort(
        key=lambda x: x["date"],
        reverse=True
    )

    return result


# =========================
# TRANSLATION
# =========================

def translate_text(text):

    if not text:
        return ""

    # متن فارسی نیاز به ترجمه ندارد
    if not re.search(
        r"[A-Za-z]",
        text
    ):

        return text

    services = [

        "https://translate.astian.org/translate",

        "https://libretranslate.com/translate",

    ]

    for url in services:

        try:

            response = requests.post(

                url,

                json={
                    "q": text,
                    "source": "en",
                    "target": "fa",
                    "format": "text"
                },

                timeout=15
            )

            if not response.ok:
                continue

            data = response.json()

            translated = data.get(
                "translatedText",
                ""
            )

            if translated:

                return translated.strip()

        except Exception as error:

            print(
                "Translation error:",
                error
            )

    # اگر ترجمه در دسترس نبود
    # متن اصلی را برمی‌گردانیم
    return text


# =========================
# PEXELS IMAGE
# =========================

def get_image(query):

    if not PEXELS_API_KEY:

        print(
            "PEXELS_API_KEY not found"
        )

        return None

    try:

        response = requests.get(

            "https://api.pexels.com/v1/search",

            headers={
                "Authorization":
                    PEXELS_API_KEY
            },

            params={
                "query": query,
                "per_page": 5,
                "orientation": "landscape"
            },

            timeout=20
        )

        if not response.ok:

            print(
                "Pexels error:",
                response.status_code
            )

            return None

        data = response.json()

        photos = data.get(
            "photos",
            []
        )

        if not photos:

            return None

        photo = photos[0]

        return photo.get(
            "src",
            {}
        ).get(
            "large2x"
        ) or photo.get(
            "src",
            {}
        ).get(
            "large"
        )

    except Exception as error:

        print(
            "Image error:",
            error
        )

        return None


# =========================
# IMAGE QUERY
# =========================

def image_query(news):

    title = news["title"]

    # برای خبرهای فارسی
    if not news["foreign"]:

        if any(
            word in title
            for word in [
                "فولاد",
                "آهن",
                "میلگرد",
                "تیرآهن",
                "شمش"
            ]
        ):

            return "steel iron factory"

        if any(
            word in title
            for word in [
                "طلا",
                "سکه"
            ]
        ):

            return "gold market"

        if any(
            word in title
            for word in [
                "دلار",
                "ارز"
            ]
        ):

            return "currency market"

        return "economy market"

    # خارجی
    return title


# =========================
# SEND TELEGRAM
# =========================

def send_news(news):

    original_title = clean_text(
        news["title"]
    )

    summary = clean_text(
        news["summary"]
    )

    # ترجمه خبر خارجی
    if news["foreign"]:

        title = translate_text(
            original_title
        )

        if summary:

            summary = translate_text(
                summary[:500]
            )

        header = (
            "🌍 <b>خبر اقتصادی جهان</b>"
        )

    else:

        title = original_title

        header = (
            "🇮🇷 <b>خبر اقتصادی ایران</b>"
        )

    # اگر ترجمه خالی شد
    if not title:

        title = original_title

    # خلاصه کوتاه
    if len(summary) > 500:

        summary = (
            summary[:500]
            + "..."
        )

    # عکس مرتبط
    image_url = get_image(
        image_query(news)
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
        f"📰 منبع: {news['source']}\n"
        f"🔗 {news['link']}\n\n"
        "🆔 @Arvand_Aron_Steel\n"
        "☎️ 021-22122239"
    )

    # -------------------------
    # اگر عکس پیدا شد
    # -------------------------

    if image_url:

        response = requests.post(

            f"https://api.telegram.org/"
            f"bot{TOKEN}/sendPhoto",

            data={

                "chat_id": CHANNEL,

                "photo": image_url,

                "caption": message,

                "parse_mode": "HTML"

            },

            timeout=30
        )

    # -------------------------
    # اگر عکس پیدا نشد
    # -------------------------

    else:

        response = requests.post(

            f"https://api.telegram.org/"
            f"bot{TOKEN}/sendMessage",

            data={

                "chat_id": CHANNEL,

                "text": message,

                "parse_mode": "HTML",

                "disable_web_page_preview":
                    False

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


# =========================
# TIME CONTROL
# =========================

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


# =========================
# MAIN
# =========================

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

    except Exception as error:

        print(
            "Send error:",
            error
        )

    # حداکثر 2 خبر در هر اجرا
    if sent >= 2:

        break


save_history(history)

print(
    f"Finished. Sent: {sent}"
)