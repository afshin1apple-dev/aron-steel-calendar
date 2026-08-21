import os
import json
import re
import hashlib
import requests
import feedparser
from datetime import datetime, timezone, timedelta


# ============================================================
# SETTINGS
# ============================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

HISTORY_FILE = "news_history.json"

MAX_HISTORY = 1000
MAX_NEWS_PER_RUN = 2

FOREIGN_SOURCES = {
    "Financial Times",
    "WSJ",
    "Economist",
    "Yahoo Finance",
    "MarketWatch",
    "Investing"
}


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
# KEYWORDS
# ============================================================

ECONOMIC_KEYWORDS = [
    "economy", "economic", "inflation", "interest rate",
    "interest rates", "fed", "federal reserve", "central bank",
    "gdp", "recession", "growth", "employment", "jobs",
    "unemployment", "market", "markets", "stocks", "stock",
    "bond", "bonds", "treasury", "dollar", "currency",
    "forex", "finance", "financial", "bank", "banking",
    "commodity", "commodities", "oil", "crude", "brent",
    "wti", "natural gas", "gold", "silver", "copper",
    "steel", "iron ore", "iron", "scrap", "rebar", "billet",
    "metals", "aluminum", "aluminium", "china", "chinese",
    "beijing", "tariff", "tariffs", "trade", "export",
    "exports", "import", "imports", "construction",
    "manufacturing", "industrial", "factory", "production",
    "supply", "demand"
]

STEEL_KEYWORDS = [
    "steel", "iron ore", "iron", "scrap", "rebar",
    "billet", "steel mill", "steelmaker", "steelmakers",
    "metals", "construction", "infrastructure",
    "iron and steel", "steel production"
]


# ============================================================
# HISTORY
# ============================================================

def load_history():
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

            if isinstance(data, list):
                return data

    except Exception:
        pass

    return []


history = load_history()


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
# TEXT
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


def make_id(title, link):
    raw = title.strip() + "|" + link.strip()

    return hashlib.sha256(
        raw.encode("utf-8")
    ).hexdigest()


# ============================================================
# FILTER
# ============================================================

def is_economic(title, summary=""):
    text = (
        title + " " + summary
    ).lower()

    return any(
        keyword.lower() in text
        for keyword in ECONOMIC_KEYWORDS
    )


def is_steel_related(title, summary=""):
    text = (
        title + " " + summary
    ).lower()

    return any(
        keyword.lower() in text
        for keyword in STEEL_KEYWORDS
    )


# ============================================================
# RSS
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
                "source": source["name"],
                "title": title,
                "summary": summary,
                "link": link,
                "steel": is_steel_related(
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

def translate_with_mymemory(text):

    try:

        response = requests.get(
            "https://api.mymemory.translated.net/get",
            params={
                "q": text,
                "langpair": "en|fa"
            },
            timeout=20
        )

        print(
            "MyMemory status:",
            response.status_code
        )

        if response.status_code != 200:
            return None

        data = response.json()

        translated = (
            data
            .get("responseData", {})
            .get("translatedText")
        )

        if translated:
            return translated.strip()

    except Exception as e:

        print(
            "MyMemory error:",
            e
        )

    return None


def translate_with_libretranslate(text):

    servers = [
        "https://libretranslate.com/translate",
        "https://translate.astian.org/translate"
    ]

    for url in servers:

        try:

            response = requests.post(
                url,
                json={
                    "q": text,
                    "source": "en",
                    "target": "fa",
                    "format": "text"
                },
                timeout=25
            )

            print(
                "LibreTranslate:",
                url,
                response.status_code
            )

            if not response.ok:
                continue

            data = response.json()

            translated = data.get(
                "translatedText"
            )

            if translated:
                return translated.strip()

        except Exception as e:

            print(
                "LibreTranslate error:",
                e
            )

    return None


def translate_text(text):

    if not text:
        return ""

    # اول MyMemory
    translated = translate_with_mymemory(
        text
    )

    if translated:
        return translated

    # بعد LibreTranslate
    translated = translate_with_libretranslate(
        text
    )

    if translated:
        return translated

    # اگر ترجمه پیدا نشد، None
    # برمی‌گردانیم تا خبر انگلیسی منتشر نشود.
    return None


# ============================================================
# IMAGE
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
                "query": query,
                "per_page": 10
            },
            timeout=20
        )

        print(
            "Pexels status:",
            response.status_code
        )

        if response.status_code != 200:
            return None

        data = response.json()

        photos = data.get(
            "photos",
            []
        )

        if not photos:
            return None

        return (
            photos[0]
            .get("src", {})
            .get("large")
        )

    except Exception as e:

        print(
            "Image error:",
            e
        )

        return None


# ============================================================
# STEEL IMPACT
# ============================================================

def steel_impact(title, summary):

    text = (
        title + " " + summary
    ).lower()

    increase_words = [
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
        "export restriction",
        "production restriction",
        "steel tariff"
    ]

    decrease_words = [
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

    increase = any(
        word in text
        for word in increase_words
    )

    decrease = any(
        word in text
        for word in decrease_words
    )

    if increase and not decrease:

        return (
            "🟢 این خبر احتمالاً باعث "
            "افزایش قیمت فولاد می‌شود.\n"
            "📝 دلیل: شرایط ایجادشده "
            "می‌تواند از تقاضا یا قیمت "
            "فولاد حمایت کند."
        )

    if decrease and not increase:

        return (
            "🔴 این خبر احتمالاً باعث "
            "کاهش قیمت فولاد می‌شود.\n"
            "📝 دلیل: شرایط ایجادشده "
            "می‌تواند فشار کاهشی بر "
            "تقاضا یا قیمت فولاد ایجاد کند."
        )

    return (
        "🟡 این خبر احتمالاً تأثیر "
        "خاصی بر قیمت فولاد نخواهد داشت."
    )


# ============================================================
# TELEGRAM
# ============================================================

def send_telegram(text, image_url=None):

    try:

        if image_url:

            url = (
                "https://api.telegram.org/"
                f"bot{BOT_TOKEN}/sendPhoto"
            )

            response = requests.post(
                url,
                data={
                    "chat_id": CHANNEL_ID,
                    "photo": image_url,
                    "caption": text
                },
                timeout=30
            )

        else:

            url = (
                "https://api.telegram.org/"
                f"bot{BOT_TOKEN}/sendMessage"
            )

            response = requests.post(
                url,
                data={
                    "chat_id": CHANNEL_ID,
                    "text": text,
                    "disable_web_page_preview": False
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

    if source in FOREIGN_SOURCES:

        translated_title = translate_text(
            original_title
        )

        if not translated_title:

            print(
                "Translation failed:",
                original_title
            )

            return None

        translated_summary = ""

        if summary:

            translated_summary = (
                translate_text(
                    summary[:700]
                )
                or ""
            )

        message = (
            "🌍 خبر اقتصادی جهان\n\n"
            f"📌 {translated_title}\n"
        )

        if translated_summary:

            message += (
                "\n"
                f"📝 {translated_summary}\n"
            )

    else:

        message = (
            "🇮🇷 خبر اقتصادی ایران\n\n"
            f"📌 {original_title}\n"
        )

        if summary:

            message += (
                "\n"
                f"📝 {summary[:700]}\n"
            )

    message += (
        "\n"
        "📊 تأثیر احتمالی بر بازار فولاد:\n"
        + steel_impact(
            original_title,
            summary
        )
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
        score += 20

    if item["source"] == "فولادبان":
        score += 10

    if item["source"] == "Financial Times":
        score += 8

    if item["source"] == "WSJ":
        score += 7

    if item["source"] == "Economist":
        score += 6

    return score


all_news.sort(
    key=priority,
    reverse=True
)


# ============================================================
# SEND
# ============================================================

sent = 0

for item in all_news:

    if sent >= MAX_NEWS_PER_RUN:
        break

    message = build_message(
        item
    )

    # اگر ترجمه خبر خارجی انجام نشد
    # اصلاً ارسال نمی‌کنیم.
    if not message:

        print(
            "SKIPPED - translation failed:",
            item["title"]
        )

        continue

    image = get_image(
        "steel economy market "
        + item["title"]
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