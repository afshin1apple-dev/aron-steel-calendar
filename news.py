import os
import re
import json
import html
import requests
import feedparser
from bs4 import BeautifulSoup
from urllib.parse import quote

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHANNEL_ID = os.environ["CHANNEL_ID"]
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")

TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
HISTORY_FILE = "news_history.json"

COMPANY_FOOTER = """
━━━━━━━━━━━━━━
🏭 آروند استیل
👤 مدیریت: افشین آورزمانی
📞 021-22122239
📱 @arvand_aron_steel
"""

# =========================================================
# منابع خبری
# =========================================================

FEEDS = [
    {
        "name": "Reuters",
        "url": "https://feeds.reuters.com/reuters/businessNews"
    },
    {
        "name": "Bloomberg",
        "url": "https://feeds.bloomberg.com/markets/news.rss"
    },
    {
        "name": "Commodity",
        "url": "https://www.commodity.com/feed/"
    },
    {
        "name": "Fooladban",
        "url": "https://fooladban.com/feed/"
    },
    {
        "name": "Eghtesad News",
        "url": "https://www.eghtesadnews.com/rss"
    },
    {
        "name": "Steel.com",
        "url": "https://www.steel.com/feed/"
    }
]

# =========================================================
# موضوعات مورد نظر
# =========================================================

KEYWORDS = [
    # فولاد
    "steel",
    "iron",
    "iron ore",
    "rebar",
    "billet",
    "slab",
    "scrap",
    "steel mill",
    "steelmaker",
    "steelmaking",
    "metals",
    "metal",
    "coking coal",
    "coke",
    "hot rolled",
    "cold rolled",
    "stainless steel",

    # اقتصاد
    "economy",
    "economic",
    "inflation",
    "interest rate",
    "central bank",
    "fed",
    "federal reserve",
    "manufacturing",
    "construction",
    "industry",
    "industrial",

    # دلار و ارز
    "dollar",
    "usd",
    "currency",
    "exchange rate",
    "forex",
    "rial",
    "yuan",

    # تحریم و سیاست تجاری
    "sanction",
    "sanctions",
    "tariff",
    "tariffs",
    "trade war",
    "export ban",
    "import ban",
    "embargo",

    # چین
    "china",
    "chinese",
    "beijing",
    "property market",
    "real estate",

    # انرژی و کامودیتی
    "oil",
    "crude",
    "energy",
    "commodity",
    "commodities",
    "gold",
    "copper",

    # فارسی
    "فولاد",
    "آهن",
    "میلگرد",
    "شمش",
    "سنگ آهن",
    "سنگ‌آهن",
    "قراضه",
    "کک",
    "زغال سنگ",
    "بازار فولاد",
    "دلار",
    "ارز",
    "نرخ ارز",
    "ریال",
    "تحریم",
    "تحریم‌ها",
    "تعرفه",
    "اقتصاد",
    "تورم",
    "چین",
    "صادرات",
    "واردات",
    "نفت",
    "طلا",
    "مس",
    "کامودیتی",
    "بازار"
]

# =========================================================
# تاریخچه
# =========================================================

def load_history():

    if not os.path.exists(HISTORY_FILE):
        return []

    try:

        with open(
            HISTORY_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except Exception:

        return []


def save_history(history):

    with open(
        HISTORY_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            history[-500:],
            f,
            ensure_ascii=False,
            indent=2
        )


history = load_history()

# =========================================================
# تمیز کردن متن
# =========================================================

def clean_text(text):

    text = BeautifulSoup(
        html.unescape(text or ""),
        "html.parser"
    ).get_text(
        " ",
        strip=True
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# =========================================================
# تشخیص خبر مرتبط
# =========================================================

def is_relevant(title, description):

    text = (
        title + " " + description
    ).lower()

    for keyword in KEYWORDS:

        if keyword.lower() in text:
            return True

    return False


# =========================================================
# دریافت اخبار
# =========================================================

def get_news():

    results = []

    for feed_info in FEEDS:

        print(
            "Checking:",
            feed_info["name"]
        )

        try:

            feed = feedparser.parse(
                feed_info["url"]
            )

            if not feed.entries:

                print(
                    "No entries:",
                    feed_info["name"]
                )

                continue

            for item in feed.entries[:30]:

                title = clean_text(
                    item.get(
                        "title",
                        ""
                    )
                )

                description = clean_text(
                    item.get(
                        "summary",
                        ""
                    )
                )

                link = item.get(
                    "link",
                    ""
                )

                if not title:
                    continue

                if not is_relevant(
                    title,
                    description
                ):
                    continue

                news_id = re.sub(
                    r"\s+",
                    " ",
                    title.lower()
                ).strip()

                if news_id in history:
                    continue

                results.append({

                    "source":
                        feed_info["name"],

                    "title":
                        title,

                    "description":
                        description,

                    "link":
                        link,

                    "id":
                        news_id

                })

        except Exception as e:

            print(
                f"Feed error {feed_info['name']}: {e}"
            )

    return results


# =========================================================
# ترجمه کامل تیتر
# =========================================================

def translate_title(title):

    try:

        encoded = quote(title)

        url = (
            "https://translate.googleapis.com/"
            "translate_a/single"
            f"?client=gtx"
            f"&sl=auto"
            f"&tl=fa"
            f"&dt=t"
            f"&q={encoded}"
        )

        response = requests.get(
            url,
            timeout=20
        )

        if response.status_code != 200:
            return title

        data = response.json()

        translated_parts = []

        for part in data[0]:

            if part and part[0]:
                translated_parts.append(
                    part[0]
                )

        translated = "".join(
            translated_parts
        )

        translated = clean_text(
            translated
        )

        if not translated:
            return title

        return translated

    except Exception as e:

        print(
            "Translation error:",
            e
        )

        return title


# =========================================================
# تحلیل اثر روی بازار فولاد
# =========================================================

def impact_analysis(
    title,
    description
):

    text = (
        title + " " + description
    ).lower()

    positive_words = [

        "steel price rise",
        "steel prices rise",
        "steel prices increase",
        "iron ore rise",
        "iron ore prices rise",
        "strong demand",
        "demand increase",
        "production cut",
        "supply cut",
        "stimulus",
        "tariff",
        "sanctions",
        "sanction",
        "oil rise",
        "oil prices rise",
        "dollar falls",
        "weaker dollar",
        "weak dollar",
        "china stimulus",
        "export restriction"

    ]

    negative_words = [

        "steel price fall",
        "steel prices fall",
        "steel prices decrease",
        "iron ore fall",
        "iron ore prices fall",
        "weak demand",
        "demand falls",
        "oversupply",
        "production increase",
        "recession",
        "dollar rises",
        "strong dollar",
        "china property slump",
        "construction slowdown"

    ]

    positive = any(
        word in text
        for word in positive_words
    )

    negative = any(
        word in text
        for word in negative_words
    )

    # تحریم معمولا برای بازار ایران
    # اثر افزایشی روی هزینه واردات و نرخ ارز دارد
    if (
        "sanction" in text
        or "تحریم" in text
    ):

        return (
            "⚠️ اثر احتمالی بر بازار فولاد ایران: "
            "ریسک افزایشی؛ تشدید تحریم‌ها می‌تواند "
            "هزینه تجارت، حمل‌ونقل و نرخ ارز را افزایش دهد."
        )

    if positive and not negative:

        return (
            "📈 اثر احتمالی بر بازار فولاد: "
            "مثبت و متمایل به افزایش قیمت‌ها."
        )

    if negative and not positive:

        return (
            "📉 اثر احتمالی بر بازار فولاد: "
            "منفی و متمایل به کاهش قیمت‌ها."
        )

    if (
        "dollar" in text
        or "usd" in text
        or "دلار" in text
    ):

        return (
            "💵 اثر احتمالی بر بازار فولاد: "
            "وابسته به مسیر نرخ ارز؛ تغییرات دلار "
            "می‌تواند مستقیماً بر هزینه و قیمت فولاد اثر بگذارد."
        )

    if (
        "china" in text
        or "چین" in text
    ):

        return (
            "🇨🇳 اثر احتمالی بر بازار فولاد: "
            "مهم؛ تغییرات تقاضا و تولید چین "
            "می‌تواند بر بازار جهانی فولاد و سنگ‌آهن اثرگذار باشد."
        )

    return (
        "⚖️ اثر احتمالی بر بازار فولاد: "
        "خنثی تا وابسته به واکنش عرضه، تقاضا و نرخ ارز."
    )


# =========================================================
# عکس مرتبط
# =========================================================

def get_image(query):

    if not PEXELS_API_KEY:
        return None

    try:

        headers = {
            "Authorization":
                PEXELS_API_KEY
        }

        response = requests.get(
            "https://api.pexels.com/v1/search",
            headers=headers,
            params={
                "query": query,
                "per_page": 10,
                "orientation": "landscape"
            },
            timeout=20
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

        return photos[0]["src"]["large"]

    except Exception as e:

        print(
            "Pexels error:",
            e
        )

        return None


# =========================================================
# ارسال پیام
# =========================================================

def send_message(text):

    try:

        response = requests.post(
            f"{TELEGRAM_URL}/sendMessage",
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
            "Telegram:",
            response.status_code,
            response.text[:500]
        )

        return response.ok

    except Exception as e:

        print(
            "Telegram error:",
            e
        )

        return False


# =========================================================
# ارسال عکس
# =========================================================

def send_photo(
    image_url,
    caption
):

    try:

        response = requests.post(
            f"{TELEGRAM_URL}/sendPhoto",
            data={
                "chat_id":
                    CHANNEL_ID,

                "photo":
                    image_url,

                "caption":
                    caption
            },
            timeout=40
        )

        print(
            "Telegram photo:",
            response.status_code,
            response.text[:500]
        )

        return response.ok

    except Exception as e:

        print(
            "Telegram photo error:",
            e
        )

        return False


# =========================================================
# ساخت پست
# =========================================================

def make_post(news):

    source = news["source"]

    original_title = news["title"]

    translated = translate_title(
        original_title
    )

    impact = impact_analysis(
        original_title,
        news["description"]
    )

    post = f"""
📰 خبر اقتصادی و بازار فولاد

📰 منبع:
{source}

🔹 تیتر اصلی:
{original_title}

🇮🇷 ترجمه تیتر:
{translated}

{impact}

🔗 منبع:
{news['link']}
"""

    post += COMPANY_FOOTER

    return post.strip()


# =========================================================
# اجرای اصلی
# =========================================================

def main():

    print(
        "Starting economic news bot..."
    )

    news_items = get_news()

    print(
        "Relevant new news:",
        len(news_items)
    )

    if not news_items:

        print(
            "No new relevant news."
        )

        return

    # حداکثر 2 خبر در هر اجرا
    news_items = news_items[:2]

    for news in news_items:

        print(
            "Processing:",
            news["title"]
        )

        post = make_post(
            news
        )

        # عکس بر اساس موضوع خبر
        image_query = (
            "steel industry "
            "iron ore "
            "steel factory "
            "commodity market"
        )

        image_url = get_image(
            image_query
        )

        if image_url:

            success = send_photo(
                image_url,
                post
            )

        else:

            success = send_message(
                post
            )

        if success:

            history.append(
                news["id"]
            )

            save_history(
                history
            )

            print(
                "POSTED:",
                news["title"]
            )

        else:

            print(
                "FAILED:",
                news["title"]
            )


if __name__ == "__main__":

    main()