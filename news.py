import os
import re
import json
import html
import requests
import feedparser
from bs4 import BeautifulSoup

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

    # Reuters
    {
        "name": "Reuters",
        "url": "https://news.google.com/rss/search?q=site%3Areuters.com+steel+OR+iron+OR+iron+ore+OR+sanctions+OR+Iran+OR+dollar+when%3A1d&hl=en-US&gl=US&ceid=US%3Aen"
    },

    # Bloomberg
    {
        "name": "Bloomberg",
        "url": "https://news.google.com/rss/search?q=site%3Abloomberg.com+steel+OR+iron+ore+OR+commodities+OR+metals+OR+Iran+OR+dollar+when%3A1d&hl=en-US&gl=US&ceid=US%3Aen"
    },

    # Bloomberg Commodities
    {
        "name": "Bloomberg Commodities",
        "url": "https://news.google.com/rss/search?q=site%3Abloomberg.com+commodities+OR+metals+OR+iron+ore+OR+steel+OR+oil+OR+coal+when%3A1d&hl=en-US&gl=US&ceid=US%3Aen"
    },

    # فولادبان
    {
        "name": "فولادبان",
        "url": "https://news.google.com/rss/search?q=site%3Afouladban.com+فولاد+OR+آهن+OR+میلگرد+OR+شمش+OR+دلار+OR+تحریم+when%3A1d&hl=fa&gl=IR&ceid=IR%3Afa"
    },

    # اقتصادنیوز
    {
        "name": "اقتصادنیوز",
        "url": "https://news.google.com/rss/search?q=site%3Aeghtesadnews.com+فولاد+OR+آهن+OR+دلار+OR+تحریم+OR+کامودیتی+OR+اقتصاد+when%3A1d&hl=fa&gl=IR&ceid=IR%3Afa"
    },

    # Commodity
    {
        "name": "Commodity",
        "url": "https://news.google.com/rss/search?q=commodities+steel+iron+ore+coking+coal+scrap+copper+oil+when%3A1d&hl=en-US&gl=US&ceid=US%3Aen"
    }
]

# =========================================================
# کلمات مهم
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
    "coking coal",
    "steel price",
    "iron ore price",

    # فلزات
    "metal",
    "metals",
    "copper",
    "aluminum",
    "nickel",
    "zinc",

    # کامودیتی
    "commodity",
    "commodities",
    "oil",
    "crude",
    "energy",
    "coal",

    # چین
    "china",
    "chinese",
    "beijing",

    # تجارت
    "export",
    "exports",
    "import",
    "imports",
    "tariff",
    "trade",

    # ایران
    "iran",
    "iranian",

    # تحریم
    "sanction",
    "sanctions",

    # ارز
    "dollar",
    "usd",
    "currency",
    "exchange rate",
    "forex",

    # فارسی
    "فولاد",
    "آهن",
    "میلگرد",
    "شمش",
    "ورق",
    "سنگ آهن",
    "سنگ‌آهن",
    "قراضه",
    "کک",
    "زغال سنگ",
    "زغال‌سنگ",
    "مس",
    "آلومینیوم",
    "نیکل",
    "روی",
    "کامودیتی",
    "کامودیتی‌ها",
    "دلار",
    "ارز",
    "نرخ ارز",
    "تحریم",
    "تحریم‌ها",
    "تعرفه",
    "صادرات",
    "واردات",
    "چین",
    "نفت",
    "انرژی",
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

    text = html.unescape(text or "")

    text = BeautifulSoup(
        text,
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
        title + " " + description
    ).lower()

    for keyword in KEYWORDS:

        if keyword.lower() in text:
            return True

    return False


# =========================================================
# گرفتن اخبار
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

            print(
                "Entries:",
                len(feed.entries)
            )

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
                        item.get(
                            "description",
                            ""
                        )
                    )
                )

                link = item.get(
                    "link",
                    ""
                )

                if not title:
                    continue

                if not link:
                    continue

                if not is_relevant(
                    title,
                    description
                ):
                    continue

                news_id = (
                    title.lower().strip()
                )

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
                "Feed error:",
                feed_info["name"],
                str(e)
            )

    return results


# =========================================================
# ترجمه تیتر
# =========================================================

def translate_title(title):

    replacements = {

        "iron ore":
            "سنگ‌آهن",

        "coking coal":
            "زغال‌سنگ کک‌شو",

        "steel":
            "فولاد",

        "iron":
            "آهن",

        "rebar":
            "میلگرد",

        "billet":
            "شمش",

        "slab":
            "اسلب",

        "scrap":
            "قراضه",

        "copper":
            "مس",

        "aluminum":
            "آلومینیوم",

        "nickel":
            "نیکل",

        "zinc":
            "روی",

        "commodities":
            "کامودیتی‌ها",

        "commodity":
            "کامودیتی",

        "oil":
            "نفت",

        "crude oil":
            "نفت خام",

        "coal":
            "زغال‌سنگ",

        "China":
            "چین",

        "Chinese":
            "چینی",

        "prices":
            "قیمت‌ها",

        "price":
            "قیمت",

        "market":
            "بازار",

        "markets":
            "بازارها",

        "demand":
            "تقاضا",

        "supply":
            "عرضه",

        "exports":
            "صادرات",

        "imports":
            "واردات",

        "tariffs":
            "تعرفه‌ها",

        "tariff":
            "تعرفه",

        "sanctions":
            "تحریم‌ها",

        "sanction":
            "تحریم",

        "dollar":
            "دلار",

        "currency":
            "ارز",

        "rise":
            "افزایش",

        "rises":
            "افزایش یافت",

        "increase":
            "افزایش",

        "increased":
            "افزایش یافت",

        "surge":
            "جهش",

        "higher":
            "بالاتر",

        "fall":
            "کاهش",

        "falls":
            "کاهش یافت",

        "decrease":
            "کاهش",

        "decreased":
            "کاهش یافت",

        "drop":
            "افت",

        "lower":
            "پایین‌تر",

        "strong":
            "قوی",

        "weak":
            "ضعیف",

        "production":
            "تولید",

        "production cut":
            "کاهش تولید",

        "demand rises":
            "تقاضا افزایش یافت",

        "demand falls":
            "تقاضا کاهش یافت"
    }

    result = title

    for en, fa in sorted(
        replacements.items(),
        key=lambda x: len(x[0]),
        reverse=True
    ):

        result = re.sub(
            re.escape(en),
            fa,
            result,
            flags=re.IGNORECASE
        )

    return result


# =========================================================
# تحلیل اثر خبر روی فولاد
# =========================================================

def impact_analysis(
    title,
    description
):

    text = (
        title + " " + description
    ).lower()

    positive_words = [

        "rise",
        "rises",
        "increase",
        "increased",
        "surge",
        "higher",
        "strong demand",
        "stimulus",
        "production cut",
        "supply cut",
        "tariff",
        "sanction",
        "sanctions",
        "dollar rises",
        "oil rises",

        "افزایش",
        "جهش",
        "رشد",
        "کاهش تولید",
        "تحریم",
        "افزایش دلار",
        "افزایش نرخ ارز"

    ]

    negative_words = [

        "fall",
        "falls",
        "drop",
        "decrease",
        "decreased",
        "lower",
        "weak demand",
        "oversupply",
        "recession",
        "production increase",
        "dollar falls",
        "oil falls",

        "کاهش",
        "افت",
        "تقاضای ضعیف",
        "مازاد عرضه",
        "افزایش تولید",
        "کاهش دلار",
        "کاهش نرخ ارز"
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
            "📈 اثر احتمالی روی فولاد: "
            "مثبت؛ احتمال حمایت از قیمت‌ها "
            "در صورت تداوم این عامل."
        )

    if negative and not positive:

        return (
            "📉 اثر احتمالی روی فولاد: "
            "منفی؛ احتمال فشار کاهشی "
            "بر قیمت‌ها."
        )

    return (
        "⚖️ اثر احتمالی روی فولاد: "
        "خنثی تا وابسته به واکنش عرضه، "
        "تقاضا و نرخ ارز."
    )


# =========================================================
# عکس Pexels
# =========================================================

def get_image():

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
                    "steel factory steel industry",
                "per_page":
                    10,
                "orientation":
                    "landscape"
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

        return photos[0]["src"]["large"]

    except Exception as e:

        print(
            "Pexels error:",
            str(e)
        )

        return None


# =========================================================
# ارسال متن
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
            response.status_code
        )

        print(
            response.text[:500]
        )

        return response.ok

    except Exception as e:

        print(
            "Telegram error:",
            str(e)
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
            response.status_code
        )

        print(
            response.text[:500]
        )

        return response.ok

    except Exception as e:

        print(
            "Telegram photo error:",
            str(e)
        )

        return False


# =========================================================
# ساخت پست
# =========================================================

def make_post(news):

    translated = translate_title(
        news["title"]
    )

    impact = impact_analysis(

        news["title"],

        news["description"]
    )

    post = f"""
📰 خبر اقتصادی و بازار فولاد

📰 منبع:
{news["source"]}

🔹 تیتر اصلی:
{news["title"]}

🇮🇷 ترجمه تیتر:
{translated}

{impact}

🔗 منبع:
{news["link"]}
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
        "STARTING ARVAND STEEL NEWS BOT"
    )

    print(
        "========================================"
    )

    news_items = get_news()

    print(
        "TOTAL NEW RELEVANT NEWS:",
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
            "Preparing:",
            news["title"]
        )

        post = make_post(
            news
        )

        image_url = get_image()

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
                "POSTED SUCCESSFULLY"
            )

        else:

            print(
                "POST FAILED"
            )

    print(
        "BOT FINISHED"
    )


if __name__ == "__main__":

    main()