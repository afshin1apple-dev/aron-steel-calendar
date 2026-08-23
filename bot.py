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

# فقط خبرهای قوی
MIN_SCORE = 35

# در هر اجرا حداکثر 2 خبر
MAX_POSTS_PER_RUN = 2


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
# SOURCES
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
# ECONOMIC TOPICS
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
    "کارخانه فولاد",
    "بورس کالا",

    "steel",
    "steel price",
    "steel prices",
    "iron ore",
    "rebar",
    "billet",
    "slab",
    "steel production"
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
    "قیمت",
    "بازار",
    "اقتصاد ایران",

    "central bank",
    "interest rate",
    "inflation",
    "iran economy"
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
# DIRECT ECONOMIC IMPACT
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
    "lower tariffs",
    "sanctions lifted"
]


# =========================================================
# EXCLUDE NON-ECONOMIC NEWS
# =========================================================

PURE_MILITARY = [
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

    if not keyword:
        return False

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
# IMPACT
# =========================================================

def detect_impact(text):

    positive = hits(
        text,
        POSITIVE
    )

    negative = hits(
        text,
        NEGATIVE
    )

    if positive and not negative:

        return "positive", positive, negative

    if negative and not positive:

        return "negative", positive, negative

    # اگر هر دو یا هیچ‌کدام باشند
    # خنثی = حذف
    return "neutral", positive, negative


# =========================================================
# SCORE
# =========================================================

def score_news(
    title,
    description,
    source
):

    text = title + " " + description

    steel = hits(text, STEEL)
    dollar = hits(text, DOLLAR)
    gold = hits(text, GOLD)
    oil = hits(text, OIL)
    sanctions = hits(text, SANCTIONS)
    trade = hits(text, TRADE)
    economy = hits(text, ECONOMY)
    china = hits(text, CHINA)

    impact, positive, negative = detect_impact(text)

    # =====================================================
    # اول: خنثی ممنوع
    # =====================================================

    if impact == "neutral":

        return {
            "score": 0,
            "impact": "neutral"
        }

    # =====================================================
    # حداقل یک موضوع اقتصادی باید وجود داشته باشد
    # =====================================================

    economic_topics = (
        steel
        or dollar
        or gold
        or oil
        or sanctions
        or trade
        or economy
        or china
    )

    if not economic_topics:

        return {
            "score": 0,
            "impact": "neutral"
        }

    # =====================================================
    # خبر نظامی بدون اثر اقتصادی = حذف
    # =====================================================

    military = hits(
        text,
        PURE_MILITARY
    )

    if military:

        direct_economic_effect = (
            steel
            or dollar
            or oil
            or sanctions
            or trade
        )

        if not direct_economic_effect:

            return {
                "score": 0,
                "impact": "neutral"
            }

    score = 0

    # =====================================================
    # امتیاز موضوع
    # =====================================================

    score += len(steel) * 8
    score += len(dollar) * 7
    score += len(gold) * 5
    score += len(oil) * 7
    score += len(sanctions) * 10
    score += len(trade) * 7
    score += len(economy) * 4
    score += len(china) * 5

    # =====================================================
    # امتیاز اثر
    # =====================================================

    score += len(positive) * 12
    score += len(negative) * 12

    # =====================================================
    # ترکیب‌های بسیار مهم
    # =====================================================

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

    if oil and military:
        score += 15

    if steel and china:
        score += 15

    if dollar and economy:
        score += 12

    # =====================================================
    # منبع تخصصی فولاد
    # =====================================================

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
        "china": china,
        "positive": positive,
        "negative": negative
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

                # فقط خبر اثرگذار
                if analysis["impact"] == "neutral":
                    continue

                # حداقل اهمیت
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
# TELEGRAM LINK BUTTON
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
                        "text": "🔗 ادامه خبر",
                        "url": news_url
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
            "Photo error:",
            e
        )

        return False


def send_message(
    text,
    news_url
):

    try:

        keyboard = {
            "inline_keyboard": [
                [
                    {
                        "text": "🔗 ادامه خبر",
                        "url": news_url
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
            "Telegram message:",
            response.status_code
        )

        return response.ok

    except Exception as e:

        print(
            "Message error:",
            e
        )

        return False


# =========================================================
# IMAGE
# =========================================================

def image_query(news):

    a = news["analysis"]

    if a.get("steel"):
        return "steel factory steel market"

    if a.get("dollar"):
        return "dollar currency financial market"

    if a.get("gold"):
        return "gold financial market"

    if a.get("oil"):
        return "oil energy market"

    if a.get("sanctions"):
        return "Iran steel industry economy"

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
            "Pexels error:",
            e
        )

        return None


# =========================================================
# POST
# =========================================================

def make_post(news):

    analysis = news["analysis"]

    if analysis["impact"] == "positive":

        impact_text = "🟢 افزایشی"

    elif analysis["impact"] == "negative":

        impact_text = "🔴 کاهشی"

    else:

        return None

    title = news["title"]

    post = (
        "🚨 <b>خبر فوری اقتصادی</b>\n\n"

        f"📰 <b>{title}</b>\n\n"

        f"📊 <b>اثر بر بازار:</b> "
        f"{impact_text}\n\n"
    )

    # فقط بازارهایی که واقعاً مرتبط‌اند
    if analysis.get("steel"):
        post += f"🏭 <b>فولاد:</b> {impact_text}\n"

    if analysis.get("dollar"):
        post += f"💵 <b>دلار:</b> {impact_text}\n"

    if analysis.get("oil"):
        post += f"🛢 <b>نفت و انرژی:</b> {impact_text}\n"

    if analysis.get("gold"):
        post += f"🥇 <b>طلا:</b> {impact_text}\n"

    post += (
        "\n"
        f"📌 <b>منبع:</b> {news['source']}\n\n"
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
        "URGENT ECONOMIC NEWS BOT"
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

        # لینک باید وجود داشته باشد
        if not news["link"]:
            continue

        post = make_post(news)

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
        "FINISHED - POSTED:",
        posted
    )

    print(
        "======================================" 
    )


if __name__ == "__main__":
    main()