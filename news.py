import os
import re
import json
import html
import random
import requests
import feedparser

from bs4 import BeautifulSoup
from urllib.parse import quote


# =========================================================
# تنظیمات
# =========================================================

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHANNEL_ID = os.environ["CHANNEL_ID"]
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")

TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

HISTORY_FILE = "news_history.json"


# =========================================================
# اطلاعات آروند استیل
# =========================================================

COMPANY_FOOTER = """
━━━━━━━━━━━━━━
🏭 آروند استیل
👤 مدیریت: افشین آورزمانی
📞 021-22122239
🆔 @arvand_aron_steel
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
# کلمات مرتبط با اخبار مورد نظر
# =========================================================

KEYWORDS = [

    # فولاد
    "steel",
    "steel price",
    "steel prices",
    "steel mill",
    "steelmaker",
    "steelmaking",
    "iron",
    "iron ore",
    "iron ore price",
    "rebar",
    "billet",
    "slab",
    "scrap",
    "coking coal",
    "coke",
    "hot rolled",
    "cold rolled",
    "stainless steel",
    "metals",
    "metal",

    # اقتصاد
    "economy",
    "economic",
    "inflation",
    "interest rate",
    "central bank",
    "federal reserve",
    "fed",
    "manufacturing",
    "construction",
    "industry",
    "industrial",
    "recession",

    # دلار و ارز
    "dollar",
    "usd",
    "currency",
    "exchange rate",
    "forex",
    "rial",
    "yuan",

    # تحریم و تجارت
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

    # کامودیتی
    "commodity",
    "commodities",
    "oil",
    "crude",
    "energy",
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
    "قیمت فولاد",
    "قیمت آهن",
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
# تاریخچه اخبار
# =========================================================

def load_history():

    if not os.path.exists(HISTORY_FILE):
        return []

    try:

        with open(
            HISTORY_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except Exception:

        return []


def save_history(history):

    try:

        with open(
            HISTORY_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                history[-500:],
                file,
                ensure_ascii=False,
                indent=2
            )

    except Exception as e:

        print(
            "History save error:",
            e
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
# بررسی ارتباط خبر
# =========================================================

def is_relevant(title, description):

    text = (
        title +
        " " +
        description
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

        encoded_title = quote(
            title
        )

        url = (
            "https://translate.googleapis.com/"
            "translate_a/single"
            "?client=gtx"
            "&sl=auto"
            "&tl=fa"
            "&dt=t"
            f"&q={encoded_title}"
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
# تحلیل اثر خبر روی بازار فولاد
# =========================================================

def impact_analysis(
    title,
    description
):

    text = (
        title +
        " " +
        description
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
        "sanction",
        "sanctions",
        "oil rise",
        "oil prices rise",
        "dollar falls",
        "weaker dollar",
        "weak dollar",
        "china stimulus",
        "export restriction",

        "افزایش قیمت",
        "افزایش تقاضا",
        "کاهش تولید",
        "کاهش عرضه",
        "محرک اقتصادی",
        "رشد قیمت"
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
        "construction slowdown",

        "کاهش قیمت",
        "کاهش تقاضا",
        "افزایش تولید",
        "مازاد عرضه",
        "رکود",
        "افت قیمت"
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
            "🟢 اثر احتمالی بر بازار فولاد: "
            "افزایش"
        )


    if negative and not positive:

        return (
            "🔴 اثر احتمالی بر بازار فولاد: "
            "کاهش"
        )


    return (
        "🟡 اثر احتمالی بر بازار فولاد: "
        "خنثی"
    )


# =========================================================
# ساخت جستجوی عکس بر اساس خود خبر
# =========================================================

def make_image_query(news):

    title = news["title"].lower()

    description = news["description"].lower()

    text = title + " " + description


    # موضوعات تخصصی‌تر اولویت دارند

    if (
        "iron ore" in text
        or "سنگ آهن" in text
        or "سنگ‌آهن" in text
    ):

        return (
            "iron ore mining "
            "iron ore industry"
        )


    if (
        "rebar" in text
        or "میلگرد" in text
    ):

        return (
            "steel rebar "
            "construction steel"
        )


    if (
        "billet" in text
        or "شمش" in text
    ):

        return (
            "steel billet "
            "steel factory"
        )


    if (
        "scrap" in text
        or "قراضه" in text
    ):

        return (
            "steel scrap "
            "metal recycling"
        )


    if (
        "dollar" in text
        or "usd" in text
        or "دلار" in text
        or "ارز" in text
    ):

        return (
            "US dollar currency "
            "financial market"
        )


    if (
        "sanction" in text
        or "تحریم" in text
    ):

        return (
            "international trade "
            "global economy"
        )


    if (
        "oil" in text
        or "crude" in text
        or "نفت" in text
    ):

        return (
            "oil refinery "
            "oil market"
        )


    if (
        "gold" in text
        or "طلا" in text
    ):

        return (
            "gold financial market "
            "gold trading"
        )


    if (
        "copper" in text
        or "مس" in text
    ):

        return (
            "copper mining "
            "copper industry"
        )


    if (
        "china" in text
        or "چین" in text
    ):

        return (
            "China steel industry "
            "Chinese factory"
        )


    # حالت پیش‌فرض

    return (
        "steel industry "
        "steel factory "
        "metal market"
    )


# =========================================================
# دریافت عکس متفاوت از Pexels
# =========================================================

def get_image(query):

    if not PEXELS_API_KEY:

        print(
            "Pexels API key not configured."
        )

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

                "query":
                    query,

                "per_page":
                    20,

                "orientation":
                    "landscape"
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


        # انتخاب تصادفی از بین 20 عکس

        selected_photo = random.choice(
            photos
        )


        image_url = selected_photo.get(
            "src",
            {}
        ).get(
            "large"
        )


        return image_url


    except Exception as e:

        print(
            "Pexels error:",
            e
        )

        return None


# =========================================================
# ارسال پیام تلگرام
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
# ارسال عکس + کپشن
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
        "========================================"
    )

    print(
        "Starting economic news bot..."
    )

    print(
        "========================================"
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


    # حداکثر 2 خبر در هر اجرای 10 دقیقه‌ای

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

        image_query = make_image_query(
            news
        )


        print(
            "Image search:",
            image_query
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


    print(
        "========================================"
    )

    print(
        "Bot finished."
    )

    print(
        "========================================"
    )


if __name__ == "__main__":

    main()