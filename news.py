import os
import json
import re
import hashlib
import requests
import feedparser
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse


# ============================================================
# SETTINGS
# ============================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

HISTORY_FILE = "news_history.json"

TEHRAN = timezone(timedelta(hours=3, minutes=30))

MAX_HISTORY = 1000


# ============================================================
# SOURCES
# ============================================================

SOURCES = [

    {
        "name": "فولادبان",
        "url": "https://fouladban.com/feed/"
    },

    {
        "name": "Financial Times",
        "url": "https://www.ft.com/?format=rss"
    },

    {
        "name": "WSJ",
        "url": "https://feeds.a.dj.com/rss/RSSMarketsMain.xml"
    },

    {
        "name": "Economist",
        "url": "https://www.economist.com/finance-and-economics/rss.xml"
    },

    {
        "name": "Yahoo Finance",
        "url": "https://finance.yahoo.com/news/rssindex"
    },

    {
        "name": "MarketWatch",
        "url": "https://feeds.marketwatch.com/marketwatch/topstories/"
    },

    {
        "name": "Investing",
        "url": "https://www.investing.com/rss/news.rss"
    }
]


# ============================================================
# ECONOMIC KEYWORDS
# ============================================================

KEYWORDS = [

    # Economy
    "economy",
    "economic",
    "inflation",
    "interest rate",
    "rates",
    "fed",
    "federal reserve",
    "central bank",
    "gdp",
    "recession",
    "growth",
    "employment",
    "jobs",
    "unemployment",

    # Markets
    "market",
    "markets",
    "stocks",
    "stock",
    "bond",
    "bonds",
    "treasury",
    "dollar",
    "currency",
    "forex",
    "finance",
    "financial",
    "bank",
    "banking",

    # Commodities
    "commodity",
    "commodities",
    "oil",
    "crude",
    "brent",
    "wti",
    "gas",
    "natural gas",
    "gold",
    "silver",
    "copper",

    # Steel
    "steel",
    "iron ore",
    "iron",
    "scrap",
    "rebar",
    "billet",
    "metals",
    "aluminum",
    "aluminium",

    # China
    "china",
    "chinese",
    "beijing",

    # Trade
    "tariff",
    "tariffs",
    "trade",
    "export",
    "exports",
    "import",
    "imports",

    # Industry
    "construction",
    "manufacturing",
    "industrial",
    "factory",
    "production",
    "supply",
    "demand"
]


STEEL_KEYWORDS = [

    "steel",
    "iron ore",
    "iron",
    "scrap",
    "rebar",
    "billet",
    "steel mill",
    "steelmaker",
    "steelmakers",
    "metals",
    "construction",
    "infrastructure",
    "iron and steel",
    "steel production"
]


# ============================================================
# LOAD HISTORY
# ============================================================

def load_history():

    try:

        with open(
            HISTORY_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

            if isinstance(data, list):
                return data

    except Exception:
        pass

    return []


history = load_history()


# ============================================================
# SAVE HISTORY
# ============================================================

def save_history():

    global history

    history = history[-MAX_HISTORY:]

    with open(
        HISTORY_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            history,
            f,
            ensure_ascii=False,
            indent=2
        )


# ============================================================
# NORMALIZE TEXT
# ============================================================

def clean_text(text):

    if not text:
        return ""

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

    return text.strip()


# ============================================================
# CHECK ECONOMIC NEWS
# ============================================================

def is_economic(title, summary=""):

    text = (
        title + " " + summary
    ).lower()

    for keyword in KEYWORDS:

        if keyword.lower() in text:
            return True

    return False


# ============================================================
# STEEL RELATED
# ============================================================

def is_steel_related(title, summary=""):

    text = (
        title + " " + summary
    ).lower()

    for keyword in STEEL_KEYWORDS:

        if keyword.lower() in text:
            return True

    return False


# ============================================================
# NEWS ID
# ============================================================

def make_id(title, link):

    raw = (
        title.strip()
        + "|"
        + link.strip()
    )

    return hashlib.sha256(
        raw.encode("utf-8")
    ).hexdigest()


# ============================================================
# FETCH RSS
# ============================================================

def fetch_source(source):

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
            timeout=25
        )

        print(
            source["name"],
            "status:",
            response.status_code
        )

        if response.status_code != 200:

            return []

        feed = feedparser.parse(
            response.content
        )

        print(
            source["name"],
            "items:",
            len(feed.entries)
        )

        results = []

        for entry in feed.entries:

            title = clean_text(
                entry.get(
                    "title",
                    ""
                )
            )

            summary = clean_text(
                entry.get(
                    "summary",
                    ""
                )
            )

            link = entry.get(
                "link",
                ""
            )

            if not title or not link:
                continue

            if not is_economic(
                title,
                summary
            ):
                continue

            item_id = make_id(
                title,
                link
            )

            if item_id in history:
                continue

            results.append({

                "id": item_id,

                "source":
                source["name"],

                "title":
                title,

                "summary":
                summary,

                "link":
                link,

                "steel":
                is_steel_related(
                    title,
                    summary
                )
            })

        return results

    except Exception as e:

        print(
            "ERROR:",
            source["name"],
            e
        )

        return []


# ============================================================
# TRANSLATION
# ============================================================

def translate_text(text):

    urls = [

        "https://libretranslate.com/translate",
        "https://translate.astian.org/translate"
    ]

    for url in urls:

        try:

            response = requests.post(

                url,

                json={

                    "q": text,

                    "source":
                    "en",

                    "target":
                    "fa",

                    "format":
                    "text"
                },

                timeout=20
            )

            print(
                "Translation status:",
                response.status_code
            )

            if response.ok:

                data = response.json()

                translated = data.get(
                    "translatedText"
                )

                if translated:

                    return translated.strip()

        except Exception as e:

            print(
                "Translation error:",
                e
            )

    return text


# ============================================================
# IMAGE SEARCH
# ============================================================

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

                "query":
                query,

                "per_page":
                10
            },

            timeout=20
        )

        if response.status_code != 200:

            print(
                "Pexels status:",
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

        return photos[0][
            "src"
        ][
            "large"
        ]

    except Exception as e:

        print(
            "Image error:",
            e
        )

        return None


# ============================================================
# STEEL IMPACT ANALYSIS
# ============================================================

def steel_impact(title, summary):

    text = (
        title + " " + summary
    ).lower()

    positive_words = [

        "supply cut",
        "production cut",
        "production cuts",
        "shortage",
        "shortfall",
        "demand rises",
        "demand increase",
        "stimulus",
        "rate cut",
        "interest rate cut",
        "infrastructure spending",
        "construction growth",
        "tariff on steel",
        "steel tariff",
        "export restriction",
        "production restriction"
    ]

    negative_words = [

        "demand falls",
        "demand decline",
        "recession",
        "economic slowdown",
        "production increase",
        "oversupply",
        "surplus",
        "steel imports rise",
        "weak construction",
        "construction slowdown",
        "rate hike",
        "interest rate hike"
    ]

    positive = any(
        word in text
        for word in positive_words
    )

    negative = any(
        word in text
        for word in negative_words
    )

    if positive and not negative:

        return (
            "🟢 این خبر احتمالاً باعث "
            "افزایش قیمت فولاد می‌شود."
            "\n"
            "📝 دلیل: شرایط ایجادشده "
            "می‌تواند از تقاضا یا قیمت "
            "فولاد حمایت کند."
        )

    if negative and not positive:

        return (
            "🔴 این خبر احتمالاً باعث "
            "کاهش قیمت فولاد می‌شود."
            "\n"
            "📝 دلیل: شرایط ایجادشده "
            "می‌تواند فشار کاهشی بر "
            "تقاضا یا قیمت فولاد ایجاد کند."
        )

    return (
        "🟡 این خبر احتمالاً تأثیر "
        "خاصی بر قیمت فولاد نخواهد داشت."
    )


# ============================================================
# SEND TELEGRAM
# ============================================================

def send_telegram(
    text,
    image_url=None
):

    try:

        if image_url:

            url = (
                f"https://api.telegram.org/"
                f"bot{BOT_TOKEN}/sendPhoto"
            )

            response = requests.post(

                url,

                data={

                    "chat_id":
                    CHANNEL_ID,

                    "photo":
                    image_url,

                    "caption":
                    text
                },

                timeout=30
            )

        else:

            url = (
                f"https://api.telegram.org/"
                f"bot{BOT_TOKEN}/sendMessage"
            )

            response = requests.post(

                url,

                data={

                    "chat_id":
                    CHANNEL_ID,

                    "text":
                    text,

                    "disable_web_page_preview":
                    False
                },

                timeout=30
            )

        print(
            "Telegram status:",
            response.status_code
        )

        if not response.ok:

            print(
                "Telegram error:",
                response.text
            )

            return False

        return True

    except Exception as e:

        print(
            "Telegram error:",
            e
        )

        return False


# ============================================================
# BUILD MESSAGE
# ============================================================

def build_message(item):

    source = item["source"]

    original_title = item["title"]

    summary = item["summary"]

    link = item["link"]

    foreign_sources = [

        "Financial Times",
        "WSJ",
        "Economist",
        "Yahoo Finance",
        "MarketWatch",
        "Investing"
    ]

    if source in foreign_sources:

        translated_title = translate_text(
            original_title
        )

        if summary:

            translated_summary = translate_text(
                summary[:700]
            )

        else:

            translated_summary = ""

        message = (
            "🌍 خبر اقتصادی جهان\n\n"
            f"📌 {translated_title}\n"
        )

        if translated_summary:

            message += (
                "\n"
                "📝 "
                + translated_summary
                + "\n"
            )

    else:

        message = (
            "🇮🇷 خبر اقتصادی ایران\n\n"
            f"📌 {original_title}\n"
        )

        if summary:

            message += (
                "\n"
                "📝 "
                + summary[:700]
                + "\n"
            )

    # Steel impact
    message += (
        "\n"
        "📊 تأثیر احتمالی بر بازار فولاد:\n"
    )

    message += steel_impact(
        original_title,
        summary
    )

    message += (
        "\n\n"
        f"📰 منبع: {source}\n"
        f"🔗 {link}\n\n"
        "🆔 @Arvand_Aron_Steel\n"
        "☎️ 021-22122239"
    )

    return message


# ============================================================
# MAIN
# ============================================================

print()
print(
    "======================================"
)
print(
    "       ECONOMIC NEWS BOT"
)
print(
    "======================================"
)
print()

all_news = []

for source in SOURCES:

    news = fetch_source(
        source
    )

    all_news.extend(
        news
    )


print()
print(
    "Today's relevant news:",
    len(all_news)
)
print()


# ============================================================
# PRIORITY
# ============================================================

def priority(item):

    score = 0

    if item["steel"]:
        score += 10

    if item["source"] == "Financial Times":
        score += 5

    if item["source"] == "فولادبان":
        score += 5

    if item["source"] == "WSJ":
        score += 4

    if item["source"] == "Economist":
        score += 4

    return score


all_news.sort(
    key=priority,
    reverse=True
)


# ============================================================
# LIMIT
# ============================================================

# برای جلوگیری از بمباران کانال،
# در هر اجرای ربات حداکثر 2 خبر ارسال می‌شود.

all_news = all_news[:2]


sent = 0


# ============================================================
# SEND
# ============================================================

for item in all_news:

    message = build_message(
        item
    )

    # Image search
    image_query = (
        "steel market economy "
        + item["title"]
    )

    image = get_image(
        image_query
    )

    success = send_telegram(
        message,
        image
    )

    if success:

        history.append(
            item["id"]
        )

        sent += 1

        print(
            "SENT:",
            item["title"]
        )

    else:

        print(
            "FAILED:",
            item["title"]
        )


# ============================================================
# SAVE
# ============================================================

save_history()


print()
print(
    "Finished. Sent:",
    sent
)