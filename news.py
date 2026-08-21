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

# حداکثر تعداد خبر در هر اجرای ربات
MAX_POSTS_PER_RUN = 2

# حداقل امتیاز لازم برای انتشار خبر
MIN_NEWS_SCORE = 10


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
# اولویت 1 — اقتصاد داخلی ایران
# =========================================================

IRAN_ECONOMY_KEYWORDS = [

    "iran",
    "iranian",
    "iran's",
    "tehran",
    "iran economy",
    "iranian economy",

    "ایران",
    "ایرانی",
    "تهران",
    "اقتصاد ایران",
    "اقتصاد داخلی",

    "central bank of iran",
    "central bank",
    "بانک مرکزی",

    "currency center",
    "exchange center",
    "مرکز مبادله",

    "interest rate",
    "نرخ بهره",

    "inflation",
    "تورم",

    "liquidity",
    "نقدینگی",

    "ministry of industry",
    "ministry of industry mine trade",
    "ministry of s-min",
    "وزارت صمت",
    "صمت",

    "customs",
    "گمرک",

    "import",
    "imports",
    "واردات",

    "export",
    "exports",
    "صادرات",

    "tax",
    "taxes",
    "مالیات",

    "commodity exchange",
    "iran commodity exchange",
    "بورس کالا",

    "tehran stock exchange",
    "stock exchange",
    "بورس",

    "electricity shortage",
    "power shortage",
    "gas shortage",
    "power restriction",
    "gas restriction",
    "industrial electricity",
    "industrial gas",

    "محدودیت برق",
    "قطعی برق",
    "برق صنایع",
    "محدودیت گاز",
    "گاز صنایع"
]


# =========================================================
# اولویت 2 — فولاد و بازار آهن
# =========================================================

STEEL_KEYWORDS = [

    "steel",
    "steel price",
    "steel prices",
    "steelmaker",
    "steel mill",
    "steelmaking",
    "steel production",
    "steel output",
    "steel exports",
    "steel imports",

    "iron ore",
    "iron ore price",
    "iron ore prices",

    "rebar",
    "billet",
    "slab",
    "scrap steel",
    "steel scrap",

    "coking coal",
    "coke",
    "hot rolled",
    "cold rolled",
    "stainless steel",

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
    "آهن اسفنجی"
]


# =========================================================
# اولویت 3 — دلار و ارز
# =========================================================

CURRENCY_KEYWORDS = [

    "dollar",
    "usd",
    "rial",
    "iranian rial",
    "exchange rate",
    "currency",

    "دلار",
    "نرخ دلار",
    "ارز",
    "نرخ ارز",
    "ریال"
]


# =========================================================
# اولویت 4 — تحریم و تجارت خارجی
# =========================================================

SANCTIONS_KEYWORDS = [

    "sanction",
    "sanctions",
    "iran sanctions",
    "sanctions on iran",

    "tariff",
    "tariffs",
    "trade war",
    "export ban",
    "import ban",
    "embargo",

    "تحریم",
    "تحریم‌ها",
    "تحریم ایران",
    "تعرفه",
    "محدودیت صادرات",
    "محدودیت واردات"
]


# =========================================================
# بازار جهانی — فقط در صورت ارتباط واقعی
# =========================================================

GLOBAL_KEYWORDS = [

    "china",
    "chinese",
    "beijing",
    "china steel",
    "china steel demand",

    "چین",
    "فولاد چین",

    "commodity",
    "commodities",
    "oil",
    "crude",
    "energy",
    "gold",
    "copper",

    "کامودیتی",
    "نفت",
    "انرژی",
    "طلا",
    "مس",

    "stimulus",
    "china stimulus",

    "تحریک اقتصادی",
    "محرک اقتصادی"
]


# =========================================================
# کلمات عمومی و ضعیف
#
# این کلمات به تنهایی هرگز نباید باعث انتشار شوند
# =========================================================

WEAK_KEYWORDS = [

    "economy",
    "economic",
    "market",
    "markets",
    "metal",
    "metals",
    "industry",
    "industrial",
    "business",
    "finance",
    "financial",

    "اقتصاد",
    "بازار",
    "صنعت",
    "مالی"
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
# نرمال‌سازی متن
# =========================================================

def normalize_text(text):

    text = clean_text(
        text
    ).lower()

    text = text.replace(
        "‌",
        " "
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text


# =========================================================
# بررسی وجود کلمه
# =========================================================

def contains_keyword(
    text,
    keyword
):

    text = normalize_text(
        text
    )

    keyword = normalize_text(
        keyword
    )

    if not keyword:
        return False

    # عبارت چندکلمه‌ای
    if " " in keyword:

        return keyword in text

    # کلمه مستقل
    return re.search(
        rf"(?<!\w){re.escape(keyword)}(?!\w)",
        text
    ) is not None


# =========================================================
# پیدا کردن کلمات موجود
# =========================================================

def find_hits(
    text,
    keywords
):

    hits = []

    for keyword in keywords:

        if contains_keyword(
            text,
            keyword
        ):

            hits.append(
                keyword
            )

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

    score = 0

    iran_hits = find_hits(
        text,
        IRAN_ECONOMY_KEYWORDS
    )

    steel_hits = find_hits(
        text,
        STEEL_KEYWORDS
    )

    currency_hits = find_hits(
        text,
        CURRENCY_KEYWORDS
    )

    sanctions_hits = find_hits(
        text,
        SANCTIONS_KEYWORDS
    )

    global_hits = find_hits(
        text,
        GLOBAL_KEYWORDS
    )

    weak_hits = find_hits(
        text,
        WEAK_KEYWORDS
    )


    # =====================================================
    # اقتصاد داخلی ایران
    # =====================================================

    score += len(
        iran_hits
    ) * 5


    # =====================================================
    # فولاد
    # =====================================================

    score += len(
        steel_hits
    ) * 4


    # =====================================================
    # دلار
    # =====================================================

    score += len(
        currency_hits
    ) * 3


    # =====================================================
    # تحریم
    # =====================================================

    score += len(
        sanctions_hits
    ) * 3


    # =====================================================
    # بازار جهانی
    # =====================================================

    score += len(
        global_hits
    ) * 2


    # =====================================================
    # اگر ایران و فولاد با هم باشند
    # =====================================================

    if iran_hits and steel_hits:

        score += 10


    # =====================================================
    # اگر ایران و دلار با هم باشند
    # =====================================================

    if iran_hits and currency_hits:

        score += 8


    # =====================================================
    # اگر ایران و تحریم با هم باشند
    # =====================================================

    if iran_hits and sanctions_hits:

        score += 8


    # =====================================================
    # چین فقط در صورت ارتباط با فولاد
    # =====================================================

    if global_hits and steel_hits:

        score += 6


    # =====================================================
    # نفت / انرژی فقط در صورت ارتباط با ایران یا فولاد
    # =====================================================

    energy_hits = find_hits(
        text,
        [
            "oil",
            "crude",
            "energy",
            "نفت",
            "انرژی"
        ]
    )

    if energy_hits and (
        iran_hits or steel_hits
    ):

        score += 5


    # =====================================================
    # منابع تخصصی داخلی کمی اولویت داشته باشند
    # =====================================================

    if source in [
        "Fooladban",
        "Eghtesad News",
        "Commodity"
    ]:

        score += 2


    # =====================================================
    # جریمه خبر عمومی
    # =====================================================

    if (
        not iran_hits
        and not steel_hits
    ):

        score -= 12


    # =====================================================
    # فقط کلمات ضعیف = رد
    # =====================================================

    if (
        weak_hits
        and not iran_hits
        and not steel_hits
        and not currency_hits
        and not sanctions_hits
    ):

        score = 0


    return {

        "score":
            score,

        "iran_hits":
            iran_hits,

        "steel_hits":
            steel_hits,

        "currency_hits":
            currency_hits,

        "sanctions_hits":
            sanctions_hits,

        "global_hits":
            global_hits
    }


# =========================================================
# تشخیص ارتباط خبر
# =========================================================

def is_relevant(
    title,
    description,
    source
):

    analysis = score_news(
        title,
        description,
        source
    )

    return (
        analysis["score"]
        >= MIN_NEWS_SCORE
    )


# =========================================================
# ساخت شناسه خبر
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
        normalize_text(
            title
        )
    )


# =========================================================
# بررسی خبرهای مشابه
# =========================================================

def is_duplicate_title(
    title,
    history
):

    new_words = set(
        normalize_text(
            title
        ).split()
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
                        analysis["score"]
                })


        except Exception as e:

            print(
                f"Feed error {feed_info['name']}: {e}"
            )


    # =====================================================
    # مهم‌ترین اخبار اول
    # =====================================================

    results.sort(
        key=lambda x:
            x["score"],
        reverse=True
    )


    return results


# =========================================================
# ترجمه تیتر
# =========================================================

def translate_title(
    title
):

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
    title,
    description
):

    text = normalize_text(
        title +
        " " +
        description
    )


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
        "china stimulus",

        "tariff",
        "sanction",
        "sanctions",

        "oil rise",
        "oil prices rise",

        "dollar falls",
        "weaker dollar",
        "weak dollar",

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


    if (
        positive
        and not negative
    ):

        return (
            "🟢 اثر احتمالی بر بازار فولاد: افزایش\n"
            "این خبر می‌تواند از قیمت یا انتظارات بازار حمایت کند."
        )


    if (
        negative
        and not positive
    ):

        return (
            "🔴 اثر احتمالی بر بازار فولاد: کاهش\n"
            "این خبر می‌تواند بر قیمت یا تقاضای بازار فشار وارد کند."
        )


    return (
        "🟡 اثر احتمالی بر بازار فولاد: خنثی / نامشخص\n"
        "اثر مستقیم این خبر بر بازار فولاد فعلاً مشخص نیست."
    )


# =========================================================
# جستجوی عکس
# =========================================================

def make_image_query(
    news
):

    title = news["title"].lower()

    description = news["description"].lower()

    text = (
        title +
        " " +
        description
    )


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
        "china" in text
        or "چین" in text
    ):

        return (
            "China steel industry "
            "Chinese factory"
        )


    if (
        "iran" in text
        or "ایران" in text
        or "tehran" in text
        or "تهران" in text
    ):

        return (
            "Iran economy "
            "Tehran financial market"
        )


    return (
        "steel industry "
        "steel factory "
        "metal market"
    )


# =========================================================
# دریافت عکس Pexels
# =========================================================

def get_image(
    query
):

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


        selected_photo = random.choice(
            photos
        )


        return selected_photo.get(
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
# ارسال پیام تلگرام
# =========================================================

def send_message(
    text
):

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

def make_post(
    news
):

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
        "Starting Arvand Steel News Bot..."
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
            "No high-quality relevant news."
        )

        return


    # فقط مهم‌ترین 2 خبر
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


            # برای تشخیص تیتر مشابه
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