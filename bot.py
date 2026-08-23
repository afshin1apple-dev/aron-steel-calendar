import os
import re
import json
import html
import random
import requests
import feedparser

from bs4 import BeautifulSoup


# =========================================================
# SETTINGS
# =========================================================

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHANNEL_ID = os.environ["CHANNEL_ID"]
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")

TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

HISTORY_FILE = "news_history.json"

# حداکثر خبر در هر اجرا
MAX_POSTS_PER_RUN = 2

# حداقل امتیاز خبر
MIN_SCORE = 35


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
        "name": "تجارت‌نیوز",
        "url": "https://tejaratnews.com/feed"
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
# IMPORTANT ECONOMIC KEYWORDS
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
    "فولاد ایران",
    "صادرات فولاد",
    "واردات فولاد",
    "تولید فولاد",
    "بازار فولاد",
    "قیمت فولاد",
    "قیمت آهن",
    "قیمت میلگرد",
    "بورس کالا",

    "steel",
    "steel price",
    "steel prices",
    "iron ore",
    "rebar",
    "billet",
    "slab"
]


DOLLAR = [
    "دلار",
    "دلار آزاد",
    "نرخ دلار",
    "قیمت دلار",
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
    "طلای ۱۸ عیار",
    "سکه",
    "اونس طلا",

    "gold",
    "gold price",
    "gold prices"
]


OIL = [
    "نفت",
    "قیمت نفت",
    "نفت برنت",
    "نفت خام",
    "بنزین",
    "گازوئیل",
    "سوخت",
    "انرژی",

    "oil",
    "oil price",
    "brent",
    "gasoline",
    "fuel",
    "energy"
]


SANCTIONS = [
    "تحریم",
    "تحریم‌ها",
    "تحریم ایران",
    "تحریم آمریکا",
    "تحریم جدید",
    "تحریم فولاد",
    "تحریم فلزات",
    "تحریم شرکت",
    "رفع تحریم",
    "لغو تحریم",

    "sanction",
    "sanctions",
    "iran sanctions"
]


TRADE = [
    "صادرات",
    "واردات",
    "تجارت",
    "گمرک",
    "تعرفه",
    "تعرفه واردات",
    "تعرفه صادرات",
    "ممنوعیت صادرات",
    "ممنوعیت واردات",

    "export",
    "exports",
    "import",
    "imports",
    "tariff"
]


ECONOMY = [
    "بانک مرکزی",
    "نرخ بهره",
    "تورم",
    "نقدینگی",
    "وزارت اقتصاد",
    "وزارت صمت",
    "بورس کالا",
    "بورس تهران",
    "اقتصاد ایران",
    "بازار ایران"
]


CHINA = [
    "چین",
    "فولاد چین",
    "تقاضای چین",
    "تولید فولاد چین",

    "china",
    "china steel",
    "chinese steel"
]


# =========================================================
# WORDS THAT SHOW REAL MARKET DIRECTION
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
    "جهش قیمت",
    "جهش کرد",
    "رکورد قیمت",
    "رکورد زد",

    "افزایش دلار",
    "افزایش نرخ دلار",
    "دلار گران شد",

    "افزایش نفت",
    "افزایش قیمت نفت",

    "افزایش طلا",

    "تحریم جدید",
    "تحریم شدیدتر",
    "تحریم‌های جدید",

    "افزایش تعرفه",
    "ممنوعیت صادرات",

    "production cut",
    "supply cut",
    "price rise",
    "price increase",
    "prices rise",
    "strong demand",
    "new sanctions",
    "higher tariffs"
]


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
    "ریزش قیمت",
    "ریزش کرد",

    "کاهش دلار",
    "کاهش نرخ دلار",
    "دلار ارزان شد",

    "کاهش نفت",
    "کاهش قیمت نفت",

    "کاهش طلا",

    "رفع تحریم",
    "لغو تحریم",
    "کاهش تحریم",

    "کاهش تعرفه",

    "production increase",
    "oversupply",
    "weak demand",
    "price fall",
    "price decrease",
    "sanctions lifted",
    "lower tariffs"
]


# =========================================================
# NON ECONOMIC / MILITARY
# =========================================================

MILITARY = [
    "حمله",
    "حملات",
    "موشک",
    "موشکی",
    "جنگنده",
    "پهپاد",
    "پدافند",
    "عملیات نظامی",
    "درگیری نظامی",
    "توانایی نظامی",
    "توان نظامی",

    "missile",
    "fighter jet",
    "drone",
    "military operation",
    "military capability"
]


# =========================================================
# PURE ANNOUNCEMENTS
# =========================================================

BORING_ANNOUNCEMENTS = [

    "اطلاعیه عرضه",
    "اطلاعیه عرضه بورس کالا",
    "عرضه بورس کالا",
    "آگهی عرضه",
    "جدول عرضه",
    "برنامه عرضه",
    "جزئیات عرضه",
    "عرضه امروز",
    "عرضه فردا",
    "عرضه هفته",

    "auction announcement",
    "offer announcement"
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
                history[-1000:],
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
# TEXT CLEAN
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

    return re.sub(
        r"\s+",
        " ",
        text
    ).strip()


def contains(text, keyword):

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


def find_hits(text, keywords):

    return [
        keyword
        for keyword in keywords
        if contains(text, keyword)
    ]


# =========================================================
# MARKET IMPACT
# =========================================================

def detect_impact(text):

    positive = find_hits(
        text,
        POSITIVE
    )

    negative = find_hits(
        text,
        NEGATIVE
    )

    # فقط یکی از دو جهت باید مشخص باشد

    if positive and not negative:

        return "positive"

    if negative and not positive:

        return "negative"

    # اگر هر دو یا هیچکدام باشند:
    # خنثی
    return "neutral"


# =========================================================
# NEWS SCORE
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

    normalized_title = normalize(
        title
    )

    # -----------------------------------------
    # خبرهای صرفاً اطلاعیه‌ای حذف
    # -----------------------------------------

    for word in BORING_ANNOUNCEMENTS:

        if contains(
            normalized_title,
            word
        ):

            return {
                "score": 0,
                "impact": "neutral",
                "reason": "boring announcement"
            }


    # -----------------------------------------
    # اثر بازار
    # -----------------------------------------

    impact = detect_impact(
        text
    )

    # خنثی = حذف کامل
    if impact == "neutral":

        return {
            "score": 0,
            "impact": "neutral",
            "reason": "no clear market impact"
        }


    # -----------------------------------------
    # موضوعات اقتصادی
    # -----------------------------------------

    steel = find_hits(
        text,
        STEEL
    )

    dollar = find_hits(
        text,
        DOLLAR
    )

    gold = find_hits(
        text,
        GOLD
    )

    oil = find_hits(
        text,
        OIL
    )

    sanctions = find_hits(
        text,
        SANCTIONS
    )

    trade = find_hits(
        text,
        TRADE
    )

    economy = find_hits(
        text,
        ECONOMY
    )

    china = find_hits(
        text,
        CHINA
    )


    economic = (
        steel
        or dollar
        or gold
        or oil
        or sanctions
        or trade
        or economy
        or china
    )

    # بدون موضوع اقتصادی = حذف
    if not economic:

        return {
            "score": 0,
            "impact": "neutral",
            "reason": "not economic"
        }


    # -----------------------------------------
    # خبر نظامی بدون اثر اقتصادی = حذف
    # -----------------------------------------

    military = find_hits(
        text,
        MILITARY
    )

    if military:

        direct_effect = (
            steel
            or dollar
            or oil
            or sanctions
            or trade
        )

        if not direct_effect:

            return {
                "score": 0,
                "impact": "neutral",
                "reason": "military only"
            }


    # -----------------------------------------
    # SCORE
    # -----------------------------------------

    score = 0

    score += len(steel) * 8
    score += len(dollar) * 7
    score += len(gold) * 5
    score += len(oil) * 7
    score += len(sanctions) * 10
    score += len(trade) * 7
    score += len(economy) * 4
    score += len(china) * 5


    # اثر مشخص
    if impact == "positive":

        score += 20

    elif impact == "negative":

        score += 20


    # -----------------------------------------
    # ترکیب‌های مهم
    # -----------------------------------------

    if steel and dollar:
        score += 18

    if steel and sanctions:
        score += 20

    if steel and trade:
        score += 15

    if dollar and sanctions:
        score += 18

    if oil and sanctions:
        score += 15

    if steel and china:
        score += 15

    if dollar and economy:
        score += 12

    if source == "فولادبان":
        score += 10


    return {

        "score": score,

        "impact": impact,

        "steel": steel,

        "dollar": dollar,

        "gold": gold,

        "oil": oil,

        "sanctions": sanctions,

        "trade": trade,

        "economy": economy,

        "china": china
    }


# =========================================================
# NEWS ID
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
                    "SCORE:",
                    analysis["score"],
                    "|",
                    analysis["impact"],
                    "|",
                    title
                )


                # =========================================
                # خنثی هرگز وارد لیست نشود
                # =========================================

                if analysis["impact"] == "neutral":
                    continue


                # =========================================
                # خبر ضعیف حذف
                # =========================================

                if analysis["score"] < MIN_SCORE:
                    continue


                # =========================================
                # لینک الزامی
                # =========================================

                if not link:
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


    # مهم‌ترین‌ها اول
    results.sort(
        key=lambda item:
            item["score"],
        reverse=True
    )


    return results


# =========================================================
# IMAGE QUERY
# =========================================================

def make_image_query(news):

    analysis = news["analysis"]


    if analysis.get("steel"):

        return (
            "steel factory steel market"
        )


    if analysis.get("dollar"):

        return (
            "dollar currency financial market"
        )


    if analysis.get("gold"):

        return (
            "gold financial market"
        )


    if analysis.get("oil"):

        return (
            "oil energy market"
        )


    if analysis.get("sanctions"):

        return (
            "Iran steel industry economy"
        )


    return (
        "Iran economy financial market"
    )


# =========================================================
# GET IMAGE
# =========================================================

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
# TELEGRAM
# =========================================================

def send_message(
    text,
    news_url
):

    try:

        keyboard = {

            "inline_keyboard": [

                [

                    {
                        "text":
                            "🔗 ادامه خبر",

                        "url":
                            news_url
                    }

                ]

            ]

        }


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
                    True,

                "reply_markup":
                    json.dumps(
                        keyboard
                    )

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
# SEND PHOTO
# =========================================================

def send_photo(
    image_url,
    caption,
    news_url
):

    try:

        keyboard = {

            "inline_keyboard": [

                [

                    {
                        "text":
                            "🔗 ادامه خبر",

                        "url":
                            news_url
                    }

                ]

            ]

        }


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
                    "HTML",

                "reply_markup":
                    json.dumps(
                        keyboard
                    )

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
# MAKE POST
# =========================================================

def make_post(news):

    analysis = news["analysis"]


    # -----------------------------------------
    # هیچ خنثی‌ای نباید ساخته شود
    # -----------------------------------------

    if analysis["impact"] == "neutral":

        return None


    if analysis["impact"] == "positive":

        impact = "🟢 افزایشی"

    elif analysis["impact"] == "negative":

        impact = "🔴 کاهشی"

    else:

        return None


    title = news["title"]


    post = (

        "🚨 <b>خبر فوری اقتصادی</b>\n\n"

        f"📰 <b>{title}</b>\n\n"

        f"📊 <b>اثر بر بازار:</b> "
        f"{impact}\n\n"
    )


    # فولاد
    if analysis.get("steel"):

        post += (
            f"🏭 <b>فولاد:</b> "
            f"{impact}\n"
        )


    # دلار
    if analysis.get("dollar"):

        post += (
            f"💵 <b>دلار:</b> "
            f"{impact}\n"
        )


    # نفت
    if analysis.get("oil"):

        post += (
            f"🛢 <b>نفت و انرژی:</b> "
            f"{impact}\n"
        )


    # طلا
    if analysis.get("gold"):

        post += (
            f"🥇 <b>طلا:</b> "
            f"{impact}\n"
        )


    post += (

        "\n"

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
        "ARVAND ARON STEEL"
    )

    print(
        "IMPORTANT ECONOMIC NEWS BOT"
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
            "No important economic news."
        )

        return


    posted = 0


    for news in news_items:

        if posted >= MAX_POSTS_PER_RUN:

            break


        # دوباره کنترل خنثی
        if news["analysis"]["impact"] == "neutral":

            continue


        post = make_post(
            news
        )


        if not post:

            continue


        print(
            "POSTING:",
            news["score"],
            news["title"]
        )


        image_url = get_image(
            news
        )


        if image_url:

            success = send_photo(

                image_url,

                post,

                news["link"]

            )

        else:

            success = send_message(

                post,

                news["link"]

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
        "FINISHED"
    )

    print(
        "POSTED:",
        posted
    )

    print(
        "======================================"
    )


if __name__ == "__main__":

    main()