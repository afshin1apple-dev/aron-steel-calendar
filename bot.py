import os
import re
import json
import html
import random
import requests
import feedparser

from bs4 import BeautifulSoup


# =========================================================
# تنظیمات
# =========================================================

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHANNEL_ID = os.environ["CHANNEL_ID"]
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")

TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

HISTORY_FILE = "news_history.json"

# حداقل امتیاز برای خبر
MIN_SCORE = 30

# حداکثر خبر در هر اجرا
MAX_POSTS_PER_RUN = 2


# =========================================================
# اطلاعات شرکت
# =========================================================

COMPANY_FOOTER = """
━━━━━━━━━━━━━━
🏭 آروند آرون استیل
👤 مدیریت: افشین آورزمانی
📞 021-22122239
🆔 @arvand_aron_steel
"""


# =========================================================
# منابع
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
# کلمات مهم
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
    "steel production"
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
    "currency"
]


GOLD = [
    "طلا",
    "طلای جهانی",
    "طلای ۱۸",
    "سکه",
    "اونس طلا",

    "gold",
    "gold price",
    "gold prices"
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
    "تحریم جدید",
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
    "تنش منطقه",

    "ایران و آمریکا",
    "ایران آمریکا",
    "حمله آمریکا",
    "حمله ایران",

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
    "تصمیم دولت",
    "تصمیم مجلس",

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
# کلمات اثر افزایشی
# =========================================================

POSITIVE = [

    "افزایش قیمت",
    "رشد قیمت",
    "افزایش نرخ",
    "افزایش تقاضا",
    "کاهش تولید",
    "کاهش عرضه",
    "کاهش موجودی",
    "کمبود عرضه",
    "صعود قیمت",
    "صعود کرد",
    "افزایش یافت",
    "گران شد",
    "رشد کرد",

    "افزایش دلار",
    "افزایش نرخ دلار",

    "افزایش نفت",
    "افزایش طلا",

    "تحریم جدید",
    "تحریم شدیدتر",
    "تحریم‌های جدید",

    "حمله",
    "حملات",
    "درگیری",
    "جنگ",
    "تنش",

    "production cut",
    "supply cut",
    "price rise",
    "prices rise",
    "strong demand",
    "price increase"
]


# =========================================================
# کلمات اثر کاهشی
# =========================================================

NEGATIVE = [

    "کاهش قیمت",
    "افت قیمت",
    "کاهش نرخ",
    "کاهش تقاضا",
    "افزایش تولید",
    "افزایش عرضه",
    "مازاد عرضه",
    "افت کرد",
    "کاهش یافت",
    "ارزان شد",
    "افت قیمت",

    "کاهش دلار",
    "کاهش نرخ دلار",

    "کاهش نفت",
    "کاهش طلا",

    "رفع تحریم",
    "لغو تحریم",
    "کاهش تحریم",

    "production increase",
    "oversupply",
    "weak demand",
    "price fall",
    "prices fall",
    "price decrease"
]


# =========================================================
# کلمات خنثی
# =========================================================

NEUTRAL = [

    "بررسی شد",
    "اعلام شد",
    "نشست برگزار شد",
    "جلسه برگزار شد",
    "گفتگو کرد",
    "دیدار کرد",
    "اظهار داشت",
    "توضیح داد",
    "تاکید کرد",
    "تاکید بر",
    "مطرح شد",
    "برنامه دارد",
    "خبر داد",

    "meeting",
    "discussed",
    "said",
    "announced",
    "talks",
    "statement"
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

    if not keyword:
        return False

    if " " in keyword:
        return keyword in text

    return re.search(
        rf"(?<!\w){re.escape(keyword)}(?!\w)",
        text
    ) is not None


def get_hits(text, keywords):

    return [
        word
        for word in keywords
        if has_keyword(text, word)
    ]


# =========================================================
# تشخیص اثر
# =========================================================

def detect_impact(text):

    positive = get_hits(
        text,
        POSITIVE
    )

    negative = get_hits(
        text,
        NEGATIVE
    )

    # اگر هر دو طرف وجود داشته باشند
    # خبر را خنثی می‌کنیم تا ریسک انتشار پایین بیاید
    if positive and negative:

        return "neutral", positive, negative

    if positive:

        return "positive", positive, negative

    if negative:

        return "negative", positive, negative

    return "neutral", positive, negative


# =========================================================
# امتیاز خبر
# =========================================================

def score_news(
    title,
    description,
    source
):

    text = title + " " + description

    steel = get_hits(
        text,
        STEEL
    )

    currency = get_hits(
        text,
        CURRENCY
    )

    gold = get_hits(
        text,
        GOLD
    )

    energy = get_hits(
        text,
        ENERGY
    )

    sanctions = get_hits(
        text,
        SANCTIONS
    )

    war = get_hits(
        text,
        WAR
    )

    economy = get_hits(
        text,
        ECONOMY
    )

    china = get_hits(
        text,
        CHINA
    )

    impact, positive, negative = detect_impact(
        text
    )

    # =====================================================
    # اگر اثر مشخص نیست → صفر
    # =====================================================

    if impact == "neutral":

        return {
            "score": 0,
            "impact": "neutral",
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

    score = 0

    # =====================================================
    # موضوعات
    # =====================================================

    score += len(steel) * 7
    score += len(currency) * 6
    score += len(gold) * 5
    score += len(energy) * 6
    score += len(sanctions) * 9
    score += len(war) * 10
    score += len(economy) * 5
    score += len(china) * 5

    # =====================================================
    # اثر
    # =====================================================

    score += len(positive) * 10
    score += len(negative) * 10

    # =====================================================
    # ترکیب‌های مهم
    # =====================================================

    if steel and currency:
        score += 15

    if steel and sanctions:
        score += 18

    if steel and war:
        score += 18

    if currency and sanctions:
        score += 15

    if currency and war:
        score += 18

    if steel and china:
        score += 12

    if energy and war:
        score += 15

    if economy and currency:
        score += 10

    # =====================================================
    # منابع تخصصی
    # =====================================================

    if source == "فولادبان":
        score += 10

    # =====================================================
    # خبرهای خیلی عمومی
    # =====================================================

    if (
        not steel
        and not currency
        and not gold
        and not energy
        and not sanctions
        and not war
        and not economy
        and not china
    ):

        score = 0

    return {
        "score": score,
        "impact": impact,
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
# شناسه خبر
# =========================================================

def make_news_id(
    title,
    link
):

    if link:

        return (
            "url:" +
            link.strip().lower()
        )

    return (
        "title:" +
        normalize(title)
    )


# =========================================================
# دریافت خبرها
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

                continue

            for item in feed.entries[:40]:

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

                analysis = score_news(
                    title,
                    description,
                    feed_info["name"]
                )

                print(
                    "NEWS:",
                    analysis["score"],
                    analysis["impact"],
                    "|",
                    title
                )

                # =================================================
                # فقط خبر با اثر واقعی
                # =================================================

                if analysis["impact"] == "neutral":
                    continue

                # =================================================
                # حداقل اهمیت
                # =================================================

                if analysis["score"] < MIN_SCORE:
                    continue

                news_id = make_news_id(
                    title,
                    link
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
# ترجمه
# =========================================================

def translate_title(title):

    # اگر فارسی است ترجمه نکن
    if re.search(
        r"[\u0600-\u06FF]",
        title
    ):

        return title

    try:

        response = requests.get(

            "https://translate.googleapis.com/"
            "translate_a/single",

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

        translated = ""

        for part in data[0]:

            if part and part[0]:

                translated += part[0]

        return clean_text(
            translated
        ) or title

    except Exception as e:

        print(
            "Translation error:",
            e
        )

        return title


# =========================================================
# تحلیل بازار
# =========================================================

def make_impact_text(news):

    analysis = news["analysis"]

    if analysis["impact"] == "positive":

        main = "🟢 افزایشی"

    elif analysis["impact"] == "negative":

        main = "🔴 کاهشی"

    else:

        return None

    steel = "🟡 خنثی"
    dollar = "🟡 خنثی"
    energy = "🟡 خنثی"

    if (
        analysis["steel"]
        or analysis["sanctions"]
        or analysis["china"]
    ):

        steel = main

    if (
        analysis["currency"]
        or analysis["sanctions"]
        or analysis["war"]
    ):

        dollar = main

    if (
        analysis["energy"]
        or analysis["war"]
    ):

        energy = main

    return (
        "📊 <b>اثر خبر بر بازار</b>\n\n"
        f"🏭 فولاد: {steel}\n"
        f"💵 دلار: {dollar}\n"
        f"🛢 انرژی: {energy}"
    )


# =========================================================
# عکس
# =========================================================

def make_image_query(news):

    analysis = news["analysis"]

    if analysis["steel"]:
        return "steel factory steel industry"

    if analysis["currency"]:
        return "dollar financial market"

    if analysis["gold"]:
        return "gold financial market"

    if analysis["energy"]:
        return "oil energy market"

    if analysis["war"]:
        return "Middle East military news"

    return "Iran financial market"


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
                    make_image_query(news),

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
            "Pexels error:",
            e
        )

        return None


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
                    caption,

                "parse_mode":
                    "HTML"

            },

            timeout=40
        )

        print(
            "Telegram photo:",
            response.status_code
        )

        return response.ok

    except Exception as e:

        print(
            "Photo error:",
            e
        )

        return False


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

                "parse_mode":
                    "HTML",

                "disable_web_page_preview":
                    True

            },

            timeout=30
        )

        print(
            "Telegram message:",
            response.status_code
        )

        return response.ok

    except Exception as e:

        print(
            "Telegram error:",
            e
        )

        return False


# =========================================================
# ساخت پست
# =========================================================

def make_post(news):

    title = news["title"]

    translated = translate_title(
        title
    )

    impact_text = make_impact_text(
        news
    )

    # هرگز خبر خنثی ساخته نشود
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
        "ARVAND ARON STEEL - URGENT NEWS BOT"
    )

    print(
        "======================================"
    )

    news_items = get_news()

    print(
        "QUALIFIED NEWS:",
        len(news_items)
    )

    if not news_items:

        print(
            "No important non-neutral news found."
        )

        return

    posted = 0

    for news in news_items:

        if posted >= MAX_POSTS_PER_RUN:
            break

        post = make_post(
            news
        )

        if not post:
            continue

        print(
            "PROCESSING:",
            news["score"],
            news["title"]
        )

        image_url = get_image(
            news
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
        "======================================"
    )

    print(
        "FINISHED - POSTED:",
        posted
    )

    print(
        "======================================"
    )


if __name__ == "__main__":
    main()