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
# SETTINGS
# =========================================================

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHANNEL_ID = os.environ["CHANNEL_ID"]
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")

TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

HISTORY_FILE = "news_history.json"

# فقط خبرهای واقعاً مهم
MIN_SCORE = 22

# حداکثر خبر در هر اجرای ربات
MAX_POSTS_PER_RUN = 3


# =========================================================
# COMPANY
# =========================================================

COMPANY_FOOTER = """
━━━━━━━━━━━━━━
🏭 آروند آرون استیل
👤 مدیریت: افشین آورزمانی
📞 021-22122239
🆔 @arvand_aron_steel
"""


# =========================================================
# NEWS SOURCES
# =========================================================

FEEDS = [

    {
        "name": "فولادبان",
        "url": "https://fooladban.com/feed/"
    },

    {
        "name": "اقتصادنیوز",
        "url": "https://www.eghtesadnews.com/rss"
    },

    {
        "name": "TGJU",
        "url": "https://www.tgju.org/rss"
    },

    {
        "name": "ایرنا",
        "url": "https://www.irna.ir/rss"
    }
]


# =========================================================
# IMPORTANT KEYWORDS
# =========================================================

STEEL = [
    "فولاد",
    "آهن",
    "میلگرد",
    "شمش",
    "سنگ آهن",
    "سنگ‌آهن",
    "آهن اسفنجی",
    "ورق",
    "تیرآهن",
    "قراضه",
    "کک",
    "زغال سنگ",
    "صادرات فولاد",
    "واردات فولاد",
    "تولید فولاد",
    "steel",
    "steel price",
    "steel prices",
    "iron ore",
    "rebar",
    "billet",
    "slab",
    "scrap",
    "coking coal"
]


CURRENCY = [
    "دلار",
    "دلار آزاد",
    "نرخ دلار",
    "ارز",
    "نرخ ارز",
    "ریال",
    "تتر",
    "مرکز مبادله",
    "دلار توافقی",
    "usd",
    "dollar",
    "iranian rial",
    "exchange rate",
    "currency",
    "tether"
]


GOLD = [
    "طلا",
    "طلای جهانی",
    "طلای ۱۸",
    "سکه",
    "اونس طلا",
    "gold",
    "gold price",
    "gold prices",
    "gold ounce"
]


ENERGY = [
    "بنزین",
    "گازوئیل",
    "سوخت",
    "نفت",
    "انرژی",
    "قیمت نفت",
    "gasoline",
    "fuel",
    "oil",
    "energy"
]


SANCTIONS = [
    "تحریم",
    "تحریم‌ها",
    "تحریم ایران",
    "تحریم آمریکا",
    "رفع تحریم",
    "sanction",
    "sanctions",
    "iran sanctions"
]


WAR = [
    "جنگ",
    "درگیری",
    "حمله",
    "حملات",
    "موشک",
    "تنش نظامی",
    "تنش منطقه‌ای",
    "ایران و آمریکا",
    "ایران آمریکا",
    "ایران و اسرائیل",
    "ایران اسرائیل",
    "پنتاگون",
    "واشنگتن",
    "iran war",
    "iran conflict",
    "iran israel",
    "us iran",
    "attack",
    "missile",
    "pentagon",
    "military conflict"
]


ECONOMY = [
    "بانک مرکزی",
    "مرکز مبادله",
    "نرخ بهره",
    "تورم",
    "نقدینگی",
    "وزارت صمت",
    "وزارت اقتصاد",
    "گمرک",
    "صادرات",
    "واردات",
    "بورس کالا",
    "بورس تهران",
    "دولت",
    "مجلس",
    "central bank",
    "interest rate",
    "inflation"
]


CHINA = [
    "چین",
    "فولاد چین",
    "اقتصاد چین",
    "تقاضای چین",
    "china",
    "chinese",
    "china steel"
]


# =========================================================
# STRONG IMPACT WORDS
# =========================================================

POSITIVE = [
    "افزایش قیمت",
    "رشد قیمت",
    "افزایش نرخ",
    "افزایش تقاضا",
    "کاهش تولید",
    "کاهش عرضه",
    "صعود",
    "صعود کرد",
    "افزایش یافت",
    "گران شد",
    "افزایش دلار",
    "افزایش طلا",
    "production cut",
    "supply cut",
    "price rise",
    "prices rise",
    "strong demand"
]


NEGATIVE = [
    "کاهش قیمت",
    "افت قیمت",
    "کاهش نرخ",
    "کاهش تقاضا",
    "افزایش تولید",
    "افزایش عرضه",
    "افت",
    "افت کرد",
    "کاهش یافت",
    "ارزان شد",
    "کاهش دلار",
    "کاهش طلا",
    "oversupply",
    "production increase",
    "price fall",
    "prices fall",
    "weak demand"
]


# =========================================================
# HISTORY
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

    try:

        with open(
            HISTORY_FILE,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                history[-1000:],
                f,
                ensure_ascii=False,
                indent=2
            )

    except Exception as e:

        print("History error:", e)


history = load_history()


# =========================================================
# TEXT
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


def normalize(text):

    text = clean_text(text).lower()

    text = text.replace("‌", " ")
    text = text.replace("ي", "ی")
    text = text.replace("ك", "ک")

    return re.sub(
        r"\s+",
        " ",
        text
    ).strip()


def has_keyword(text, keyword):

    text = normalize(text)
    keyword = normalize(keyword)

    if " " in keyword:

        return keyword in text

    return re.search(
        rf"(?<!\w){re.escape(keyword)}(?!\w)",
        text
    ) is not None


def hits(text, keywords):

    return [
        word
        for word in keywords
        if has_keyword(text, word)
    ]


# =========================================================
# SCORE
# =========================================================

def score_news(title, description, source):

    text = title + " " + description

    steel = hits(text, STEEL)
    currency = hits(text, CURRENCY)
    gold = hits(text, GOLD)
    energy = hits(text, ENERGY)
    sanctions = hits(text, SANCTIONS)
    war = hits(text, WAR)
    economy = hits(text, ECONOMY)
    china = hits(text, CHINA)

    positive = hits(text, POSITIVE)
    negative = hits(text, NEGATIVE)

    score = 0

    # موضوعات اصلی
    score += len(steel) * 6
    score += len(currency) * 5
    score += len(gold) * 4
    score += len(energy) * 5
    score += len(sanctions) * 8
    score += len(war) * 9
    score += len(economy) * 4
    score += len(china) * 4

    # اثر قابل تشخیص
    score += len(positive) * 7
    score += len(negative) * 7

    # ترکیب‌های خیلی مهم
    if steel and currency:
        score += 12

    if steel and sanctions:
        score += 15

    if steel and war:
        score += 15

    if currency and sanctions:
        score += 12

    if currency and war:
        score += 15

    if steel and china:
        score += 10

    if energy and war:
        score += 12

    if economy and currency:
        score += 8

    # منابع تخصصی
    if source == "فولادبان":
        score += 8

    # اگر اثر مثبت یا منفی اصلاً پیدا نشده باشد
    # خبر خنثی محسوب می‌شود
    if not positive and not negative:

        score = 0

    return {
        "score": score,
        "steel": steel,
        "currency": currency,
        "gold": gold,
        "energy": energy,
        "sanctions": sanctions,
        "war": war,
        "economy": economy,
        "china": china,
        "positive": positive,
        "negative": negative
    }


# =========================================================
# DUPLICATE
# =========================================================

def make_id(title, link):

    if link:

        return "url:" + link.strip().lower()

    return "title:" + normalize(title)


def duplicate(news_id):

    return news_id in history


# =========================================================
# GET NEWS
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

            for item in feed.entries[:30]:

                title = clean_text(
                    item.get("title", "")
                )

                description = clean_text(
                    item.get("summary", "")
                )

                link = item.get(
                    "link",
                    ""
                )

                if not title:
                    continue

                analysis = score_news(
                    title,
                    description,
                    feed_info["name"]
                )

                print(
                    "SCORE:",
                    analysis["score"],
                    "|",
                    title
                )

                if analysis["score"] < MIN_SCORE:
                    continue

                news_id = make_id(
                    title,
                    link
                )

                if duplicate(news_id):
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
                        news_id,

                    "score":
                        analysis["score"],

                    "analysis":
                        analysis
                })

        except Exception as e:

            print(
                "Feed error:",
                feed_info["name"],
                e
            )

    results.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return results


# =========================================================
# TRANSLATION
# =========================================================

def translate_title(title):

    try:

        url = (
            "https://translate.googleapis.com/"
            "translate_a/single"
        )

        response = requests.get(

            url,

            params={
                "client": "gtx",
                "sl": "auto",
                "tl": "fa",
                "dt": "t",
                "q": title
            },

            timeout=20
        )

        if response.status_code != 200:
            return title

        data = response.json()

        result = ""

        for part in data[0]:

            if part and part[0]:
                result += part[0]

        return clean_text(result) or title

    except Exception as e:

        print(
            "Translation error:",
            e
        )

        return title


# =========================================================
# IMPACT
# =========================================================

def impact(news):

    analysis = news["analysis"]

    positive = analysis["positive"]
    negative = analysis["negative"]

    if positive and not negative:

        main = "🟢 افزایشی"

    elif negative and not positive:

        main = "🔴 کاهشی"

    else:

        return None

    steel = "🟡"
    dollar = "🟡"
    energy = "🟡"

    if analysis["steel"]:
        steel = main

    if analysis["currency"] or analysis["sanctions"] or analysis["war"]:
        dollar = "🟢" if positive else "🔴"

    if analysis["energy"] or analysis["war"]:
        energy = "🟢" if positive else "🔴"

    return (
        f"📊 <b>تأثیر کلی بازار:</b> {main}\n\n"
        f"🏭 فولاد: {steel}\n"
        f"💵 دلار: {dollar}\n"
        f"🛢 انرژی: {energy}"
    )


# =========================================================
# IMAGE
# =========================================================

def image_query(news):

    analysis = news["analysis"]

    if analysis["steel"]:
        return "steel factory steel market"

    if analysis["currency"]:
        return "US dollar financial market"

    if analysis["gold"]:
        return "gold financial market"

    if analysis["energy"]:
        return "oil energy market"

    if analysis["war"]:
        return "Middle East military conflict"

    return "Iran economy financial market"


def get_image(news):

    if not PEXELS_API_KEY:
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
                    image_query(news),

                "per_page":
                    15,

                "orientation":
                    "landscape"
            },

            timeout=20
        )

        if response.status_code != 200:
            return None

        photos = response.json().get(
            "photos",
            []
        )

        if not photos:
            return None

        return random.choice(
            photos
        )["src"]["large"]

    except Exception as e:

        print(
            "Image error:",
            e
        )

        return None


# =========================================================
# TELEGRAM
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
                    caption,

                "parse_mode":
                    "HTML"

            },

            timeout=40
        )

        return response.ok

    except Exception as e:

        print(
            "Photo error:",
            e
        )

        return False


def send_message(text):

    try:

        response = requests.post(

            f"{TELEGRAM_URL}/sendMessage",

            data={

                "chat_id":
                    CHANNEL_ID,

                "text":
                    text,

                "parse_mode":
                    "HTML",

                "disable_web_page_preview":
                    True

            },

            timeout=30
        )

        return response.ok

    except Exception as e:

        print(
            "Message error:",
            e
        )

        return False


# =========================================================
# POST
# =========================================================

def make_post(news):

    title = news["title"]

    # اگر تیتر فارسی باشد ترجمه نمی‌کنیم
    if re.search(
        r"[\u0600-\u06FF]",
        title
    ):

        translated = title

    else:

        translated = translate_title(
            title
        )

    impact_text = impact(news)

    if not impact_text:
        return None

    post = (
        "🚨 <b>خبر فوری و مهم بازار</b>\n\n"

        f"📰 <b>تیتر:</b>\n"
        f"{title}\n\n"

        f"🇮🇷 <b>ترجمه:</b>\n"
        f"{translated}\n\n"

        f"{impact_text}\n\n"

        f"📌 <b>منبع:</b> "
        f"{news['source']}\n\n"

        f"{COMPANY_FOOTER}"
    )

    return post.strip()


# =========================================================
# MAIN
# =========================================================

def main():

    print(
        "======================================"
    )

    print(
        "URGENT MARKET NEWS BOT"
    )

    print(
        "======================================"
    )

    news_items = get_news()

    print(
        "Important news:",
        len(news_items)
    )

    if not news_items:

        print(
            "No important news."
        )

        return

    posted = 0

    for news in news_items:

        if posted >= MAX_POSTS_PER_RUN:
            break

        post = make_post(news)

        if not post:
            continue

        print(
            "POSTING:",
            news["score"],
            news["title"]
        )

        image = get_image(news)

        if image:

            success = send_photo(
                image,
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

            save_history(history)

            posted += 1

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
        "Finished. Posted:",
        posted
    )


if __name__ == "__main__":
    main()
    