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

MAX_POSTS_PER_RUN = 2

MIN_NEWS_SCORE = 10


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
# منابع خبری
# =========================================================

FEEDS = [

    {
        "name": "فولادبان",
        "url": "https://fooladban.com/feed/"
    },

    {
        "name": "اخبار اقتصادی داخلی",
        "url": "https://www.eghtesadnews.com/rss"
    },

    {
        "name": "دلار و بازار ایران",
        "url": "https://www.tgju.org/rss"
    },

    {
        "name": "بنزین و انرژی ایران",
        "url": "https://www.irna.ir/rss"
    },

    {
        "name": "طلا و بازار جهانی",
        "url": "https://www.tgju.org/rss"
    },

    {
        "name": "اخبار جنگ ایران و آمریکا",
        "url": "https://www.irna.ir/rss"
    }
]


# =========================================================
# اقتصاد داخلی ایران
# =========================================================

IRAN_ECONOMY_KEYWORDS = [

    "ایران",
    "ایرانی",
    "تهران",
    "اقتصاد ایران",
    "اقتصاد داخلی",

    "بانک مرکزی",
    "مرکز مبادله",
    "نرخ بهره",
    "تورم",
    "نقدینگی",

    "وزارت صمت",
    "صمت",

    "گمرک",
    "واردات",
    "صادرات",

    "مالیات",
    "بورس کالا",
    "بورس تهران",
    "بورس",

    "دولت",
    "مجلس",
    "وزارت اقتصاد",

    "economic",
    "iran",
    "iranian",
    "tehran",

    "central bank",
    "inflation",
    "interest rate",

    "iran economy"
]


# =========================================================
# فولاد و آهن
# =========================================================

STEEL_KEYWORDS = [

    "فولاد",
    "بازار فولاد",
    "قیمت فولاد",
    "تولید فولاد",
    "صادرات فولاد",
    "واردات فولاد",

    "آهن",
    "بازار آهن",
    "قیمت آهن",

    "میلگرد",
    "شمش",
    "سنگ آهن",
    "سنگ‌آهن",
    "قراضه",
    "کک",
    "زغال سنگ",

    "ورق",
    "تیرآهن",
    "آهن اسفنجی",

    "steel",
    "steel price",
    "steel prices",
    "steel production",
    "steel exports",
    "steel imports",

    "iron ore",
    "iron ore price",

    "rebar",
    "billet",
    "slab",
    "scrap steel",
    "coking coal",
    "hot rolled",
    "cold rolled"
]


# =========================================================
# دلار و ارز ایران
# =========================================================

CURRENCY_KEYWORDS = [

    "دلار",
    "نرخ دلار",
    "دلار آزاد",
    "دلار بازار آزاد",
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


# =========================================================
# بنزین و انرژی ایران
# =========================================================

FUEL_KEYWORDS = [

    "بنزین",
    "قیمت بنزین",
    "سهمیه بنزین",
    "کارت سوخت",
    "سوخت",
    "گازوئیل",
    "نفت",
    "پمپ بنزین",
    "جایگاه سوخت",

    "بنزین ایران",
    "سوخت ایران",

    "gasoline",
    "fuel",
    "iran fuel",
    "iran gasoline",
    "petrol"
]


# =========================================================
# طلا ایران و جهان
# =========================================================

GOLD_KEYWORDS = [

    "طلا",
    "طلای جهانی",
    "طلای ۱۸ عیار",
    "طلای آبشده",
    "سکه",
    "سکه امامی",
    "اونس طلا",

    "gold",
    "gold price",
    "gold prices",
    "gold ounce",
    "xau"
]


# =========================================================
# جنگ ایران و آمریکا
# =========================================================

WAR_KEYWORDS = [

    "ایران و آمریکا",
    "ایران آمریکا",
    "جنگ ایران و آمریکا",
    "درگیری ایران و آمریکا",
    "حمله آمریکا به ایران",
    "حمله ایران به آمریکا",

    "ایران و اسرائیل",
    "ایران اسرائیل",
    "جنگ ایران و اسرائیل",
    "درگیری ایران و اسرائیل",

    "آمریکا",
    "واشنگتن",
    "پنتاگون",
    "حمله",
    "حملات",
    "موشک",
    "موشکی",
    "درگیری نظامی",
    "تنش نظامی",
    "تنش منطقه‌ای",

    "iran usa",
    "iran us",
    "iran united states",
    "iran war",
    "iran conflict",
    "iran israel",
    "israel iran",
    "us iran",
    "military conflict",
    "attack",
    "missile",
    "pentagon"
]


# =========================================================
# تحریم
# =========================================================

SANCTIONS_KEYWORDS = [

    "تحریم",
    "تحریم‌ها",
    "تحریم ایران",
    "تحریم آمریکا",
    "رفع تحریم",

    "sanction",
    "sanctions",
    "iran sanctions",
    "us sanctions"
]


# =========================================================
# بازار جهانی
# =========================================================

GLOBAL_KEYWORDS = [

    "چین",
    "فولاد چین",
    "اقتصاد چین",
    "تقاضای چین",

    "china",
    "chinese",
    "china steel",

    "نفت",
    "انرژی",
    "کامودیتی",
    "مس",

    "oil",
    "energy",
    "commodity",
    "commodities",
    "copper"
]


# =========================================================
# کلمات ضعیف
# =========================================================

WEAK_KEYWORDS = [

    "economy",
    "economic",
    "market",
    "markets",
    "industry",
    "industrial",
    "business",
    "finance",

    "اقتصاد",
    "بازار",
    "صنعت",
    "مالی"
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
# نرمال‌سازی
# =========================================================

def normalize_text(text):

    text = clean_text(text).lower()

    text = text.replace(
        "‌",
        " "
    )

    text = text.replace(
        "ي",
        "ی"
    )

    text = text.replace(
        "ك",
        "ک"
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# =========================================================
# بررسی کلمه
# =========================================================

def contains_keyword(text, keyword):

    text = normalize_text(text)

    keyword = normalize_text(keyword)

    if not keyword:
        return False

    if " " in keyword:

        return keyword in text

    return re.search(
        rf"(?<!\w){re.escape(keyword)}(?!\w)",
        text
    ) is not None


# =========================================================
# پیدا کردن کلمات
# =========================================================

def find_hits(text, keywords):

    hits = []

    for keyword in keywords:

        if contains_keyword(
            text,
            keyword
        ):

            hits.append(keyword)

    return hits


# =========================================================
# امتیازدهی خبر
# =========================================================

def score_news(
    title,
    description,
    source
):

    text = (
        title +
        " " +
        description
    )

    iran = find_hits(
        text,
        IRAN_ECONOMY_KEYWORDS
    )

    steel = find_hits(
        text,
        STEEL_KEYWORDS
    )

    currency = find_hits(
        text,
        CURRENCY_KEYWORDS
    )

    fuel = find_hits(
        text,
        FUEL_KEYWORDS
    )

    gold = find_hits(
        text,
        GOLD_KEYWORDS
    )

    war = find_hits(
        text,
        WAR_KEYWORDS
    )

    sanctions = find_hits(
        text,
        SANCTIONS_KEYWORDS
    )

    global_hits = find_hits(
        text,
        GLOBAL_KEYWORDS
    )

    weak = find_hits(
        text,
        WEAK_KEYWORDS
    )

    score = 0


    # فولاد
    score += len(steel) * 6


    # اقتصاد ایران
    score += len(iran) * 5


    # دلار
    score += len(currency) * 5


    # بنزین
    score += len(fuel) * 5


    # طلا
    score += len(gold) * 5


    # جنگ
    score += len(war) * 6


    # تحریم
    score += len(sanctions) * 4


    # بازار جهانی
    score += len(global_hits) * 2


    # -----------------------------------------------------
    # ترکیب‌های مهم
    # -----------------------------------------------------

    if iran and steel:
        score += 12

    if iran and currency:
        score += 10

    if iran and fuel:
        score += 10

    if iran and gold:
        score += 8

    if iran and war:
        score += 15

    if iran and sanctions:
        score += 10

    if steel and currency:
        score += 8

    if steel and fuel:
        score += 6

    if steel and gold:
        score += 5

    if global_hits and steel:
        score += 7

    if war and sanctions:
        score += 8


    # -----------------------------------------------------
    # منابع تخصصی
    # -----------------------------------------------------

    if source == "فولادبان":
        score += 5

    if source in [
        "دلار و بازار ایران",
        "طلا و بازار جهانی"
    ]:
        score += 4


    # -----------------------------------------------------
    # خبرهای کاملاً عمومی حذف شوند
    # -----------------------------------------------------

    if (
        not iran
        and not steel
        and not currency
        and not fuel
        and not gold
        and not war
        and not sanctions
    ):

        score -= 20


    if (
        weak
        and not iran
        and not steel
        and not currency
        and not fuel
        and not gold
        and not war
        and not sanctions
    ):

        score = 0


    return {
        "score": score,
        "iran": iran,
        "steel": steel,
        "currency": currency,
        "fuel": fuel,
        "gold": gold,
        "war": war,
        "sanctions": sanctions,
        "global": global_hits
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
        normalize_text(title)
    )


# =========================================================
# تشخیص خبر مشابه
# =========================================================

def is_duplicate_title(
    title,
    history
):

    new_words = set(
        normalize_text(title).split()
    )

    if len(new_words) < 5:
        return False


    for old_id in history[-200:]:

        if not isinstance(
            old_id,
            str
        ):

            continue

        if not old_id.startswith(
            "title:"
        ):

            continue

        old_title = old_id[6:]

        old_words = set(
            old_title.split()
        )

        if not old_words:
            continue

        common = len(
            new_words &
            old_words
        )

        similarity = (
            common /
            max(
                len(new_words),
                len(old_words)
            )
        )

        if similarity >= 0.70:

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
                    "NEWS SCORE:",
                    analysis["score"],
                    "|",
                    feed_info["name"],
                    "|",
                    title
                )


                if (
                    analysis["score"]
                    < MIN_NEWS_SCORE
                ):

                    continue


                news_id = make_news_id(
                    title,
                    link
                )


                if news_id in history:
                    continue


                if is_duplicate_title(
                    title,
                    history
                ):

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
                f"Feed error {feed_info['name']}: {e}"
            )


    results.sort(
        key=lambda x:
            x["score"],
        reverse=True
    )


    return results


# =========================================================
# تشخیص ایرانی بودن خبر
# =========================================================

def is_iranian_news(news):

    text = (
        news["title"] +
        " " +
        news["description"]
    )

    analysis = news["analysis"]

    if (
        analysis["iran"]
        or analysis["fuel"]
        or analysis["currency"]
        or analysis["war"]
    ):

        return True


    iran_words = [

        "ایران",
        "ایرانی",
        "تهران",
        "دولت",
        "وزارت",
        "مجلس",

        "iran",
        "iranian",
        "tehran"
    ]

    return any(
        contains_keyword(
            text,
            word
        )
        for word in iran_words
    )


# =========================================================
# ترجمه فقط برای اخبار خارجی
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

            if (
                part
                and part[0]
            ):

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
# تحلیل اثر خبر
# =========================================================

def impact_analysis(
    news
):

    title = news["title"]

    description = news["description"]

    text = normalize_text(
        title +
        " " +
        description
    )

    analysis = news["analysis"]


    positive_words = [

        "افزایش قیمت",
        "افزایش تقاضا",
        "کاهش تولید",
        "کاهش عرضه",
        "رشد قیمت",
        "افزایش نرخ",
        "افزایش دلار",
        "افزایش طلا",

        "قیمت صعود کرد",
        "رشد کرد",
        "صعود",

        "stimulus",
        "strong demand",
        "production cut",
        "supply cut",
        "price rise",
        "prices rise"
    ]


    negative_words = [

        "کاهش قیمت",
        "کاهش تقاضا",
        "افزایش تولید",
        "مازاد عرضه",
        "افت قیمت",
        "کاهش نرخ",
        "کاهش دلار",
        "افت طلا",

        "قیمت کاهش یافت",
        "افت کرد",

        "weak demand",
        "oversupply",
        "production increase",
        "price fall",
        "prices fall"
    ]


    positive = any(
        contains_keyword(
            text,
            word
        )
        for word in positive_words
    )


    negative = any(
        contains_keyword(
            text,
            word
        )
        for word in negative_words
    )


    # جنگ و بنزین و اقتصاد
    if (
        analysis["war"]
        or analysis["fuel"]
        or analysis["iran"]
    ):

        if positive and not negative:

            return (
                "🟢 اثر احتمالی بر بازار: افزایشی\n"
                "این خبر می‌تواند بر انتظارات بازار اثر افزایشی داشته باشد."
            )

        if negative and not positive:

            return (
                "🔴 اثر احتمالی بر بازار: کاهشی\n"
                "این خبر می‌تواند بر انتظارات بازار اثر کاهشی داشته باشد."
            )


    if positive and not negative:

        return (
            "🟢 اثر احتمالی بر بازار فولاد: افزایش\n"
            "این خبر می‌تواند از قیمت یا انتظارات بازار حمایت کند."
        )


    if negative and not positive:

        return (
            "🔴 اثر احتمالی بر بازار فولاد: کاهش\n"
            "این خبر می‌تواند بر قیمت یا تقاضای بازار فشار وارد کند."
        )


    return (
        "🟡 اثر احتمالی بر بازار: خنثی / نامشخص\n"
        "اثر مستقیم این خبر بر بازار فعلاً مشخص نیست."
    )


# =========================================================
# ساخت جستجوی عکس
# =========================================================

def make_image_query(news):

    text = normalize_text(
        news["title"] +
        " " +
        news["description"]
    )


    if (
        "بنزین" in text
        or "gasoline" in text
        or "fuel" in text
    ):

        return (
            "Iran gasoline fuel station"
        )


    if (
        "طلا" in text
        or "gold" in text
        or "سکه" in text
    ):

        return (
            "gold financial market"
        )


    if (
        "دلار" in text
        or "usd" in text
        or "تتر" in text
    ):

        return (
            "US dollar currency market"
        )


    if (
        "جنگ" in text
        or "حمله" in text
        or "موشک" in text
        or "war" in text
        or "missile" in text
    ):

        return (
            "Iran military conflict Middle East"
        )


    if (
        "سنگ آهن" in text
        or "iron ore" in text
    ):

        return (
            "iron ore mining steel industry"
        )


    if (
        "میلگرد" in text
        or "rebar" in text
    ):

        return (
            "steel rebar construction"
        )


    if (
        "شمش" in text
        or "billet" in text
    ):

        return (
            "steel billet factory"
        )


    if (
        "فولاد" in text
        or "steel" in text
    ):

        return (
            "steel factory steel industry"
        )


    return (
        "Iran economy financial market"
    )


# =========================================================
# دریافت عکس
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

            return None


        photos = response.json().get(
            "photos",
            []
        )


        if not photos:
            return None


        return random.choice(
            photos
        ).get(
            "src",
            {}
        ).get(
            "large"
        )


    except Exception as e:

        print(
            "Pexels error:",
            e
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
                    True

            },

            timeout=30
        )


        print(
            "Telegram:",
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


    # خبر ایرانی ترجمه نشود
    if is_iranian_news(news):

        title_text = original_title

    else:

        title_text = translate_title(
            original_title
        )


    impact = impact_analysis(
        news
    )


    post = (
        "📰 <b>خبر اقتصادی و بازار</b>\n\n"

        f"📰 <b>منبع:</b>\n"
        f"{source}\n\n"

        f"🔹 <b>خبر:</b>\n"
        f"{title_text}\n\n"

        f"{impact}\n\n"

        + COMPANY_FOOTER
    )


    return post.strip()


# =========================================================
# اجرای اصلی
# =========================================================

def main():

    print(
        "========================================"
    )

    print(
        "Starting Arvand Aron Steel News Bot..."
    )

    print(
        "========================================"
    )


    news_items = get_news()


    print(
        "Qualified news:",
        len(news_items)
    )


    if not news_items:

        print(
            "No relevant news found."
        )

        return


    news_items = news_items[
        :MAX_POSTS_PER_RUN
    ]


    for news in news_items:

        print(
            "Processing:",
            news["score"],
            news["title"]
        )


        post = make_post(
            news
        )


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


            history.append(
                "title:" +
                normalize_text(
                    news["title"]
                )
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