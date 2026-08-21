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

# ---------------------------------------------------------
# منابع خبری
# ---------------------------------------------------------

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
        "name": "Steel.com",
        "url": "https://www.steel.com/feed/"
    }
]

# ---------------------------------------------------------
# کلمات مرتبط با فولاد و بازار
# ---------------------------------------------------------

KEYWORDS = [
    "steel",
    "iron",
    "rebar",
    "billet",
    "slab",
    "scrap",
    "iron ore",
    "coking coal",
    "metals",
    "commodity",
    "construction",
    "china",
    "tariff",
    "sanction",
    "steel price",
    "iron ore price",
    "فولاد",
    "آهن",
    "میلگرد",
    "شمش",
    "سنگ آهن",
    "قراضه",
    "بازار",
    "تعرفه",
    "تحریم",
    "چین"
]

# ---------------------------------------------------------
# خواندن تاریخچه
# ---------------------------------------------------------

def load_history():

    if not os.path.exists(HISTORY_FILE):
        return []

    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    except Exception:
        return []


def save_history(history):

    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(
            history[-500:],
            f,
            ensure_ascii=False,
            indent=2
        )


history = load_history()

# ---------------------------------------------------------
# تمیز کردن متن
# ---------------------------------------------------------

def clean_text(text):

    text = BeautifulSoup(
        html.unescape(text or ""),
        "html.parser"
    ).get_text(" ", strip=True)

    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ---------------------------------------------------------
# بررسی ارتباط خبر با فولاد
# ---------------------------------------------------------

def is_relevant(title, description):

    text = (
        title + " " + description
    ).lower()

    for keyword in KEYWORDS:

        if keyword.lower() in text:
            return True

    return False


# ---------------------------------------------------------
# گرفتن اخبار
# ---------------------------------------------------------

def get_news():

    results = []

    for feed_info in FEEDS:

        try:

            feed = feedparser.parse(
                feed_info["url"]
            )

            for item in feed.entries[:20]:

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
                    "source": feed_info["name"],
                    "title": title,
                    "description": description,
                    "link": link,
                    "id": news_id
                })

        except Exception as e:

            print(
                f"Feed error {feed_info['name']}: {e}"
            )

    return results


# ---------------------------------------------------------
# ترجمه ساده تیتر
# ---------------------------------------------------------

def translate_title(title):

    # ترجمه برای تیترهای رایج اقتصادی
    replacements = {

        "steel": "فولاد",
        "iron ore": "سنگ‌آهن",
        "iron": "آهن",
        "rebar": "میلگرد",
        "billet": "شمش",
        "scrap": "قراضه",
        "China": "چین",
        "Chinese": "چینی",
        "prices": "قیمت‌ها",
        "price": "قیمت",
        "market": "بازار",
        "markets": "بازارها",
        "demand": "تقاضا",
        "supply": "عرضه",
        "exports": "صادرات",
        "imports": "واردات",
        "tariff": "تعرفه",
        "sanctions": "تحریم‌ها",
        "sanction": "تحریم",
        "rise": "افزایش",
        "rises": "افزایش یافت",
        "fall": "کاهش",
        "falls": "کاهش یافت",
        "higher": "بالاتر",
        "lower": "پایین‌تر",
        "surge": "جهش",
        "drop": "افت",
        "increase": "افزایش",
        "decrease": "کاهش",
        "demand rises": "تقاضا افزایش یافت",
        "demand falls": "تقاضا کاهش یافت"
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


# ---------------------------------------------------------
# تحلیل اثر خبر روی فولاد
# ---------------------------------------------------------

def impact_analysis(title, description):

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
        "tariff"
    ]

    negative_words = [
        "fall",
        "falls",
        "drop",
        "decrease",
        "lower",
        "weak demand",
        "oversupply",
        "recession",
        "production increase"
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
            "📈 اثر احتمالی بر بازار فولاد: "
            "مثبت و متمایل به افزایش قیمت‌ها."
        )

    if negative and not positive:

        return (
            "📉 اثر احتمالی بر بازار فولاد: "
            "منفی و متمایل به کاهش قیمت‌ها."
        )

    return (
        "⚖️ اثر احتمالی بر بازار فولاد: "
        "خنثی تا وابسته به واکنش عرضه و تقاضا."
    )


# ---------------------------------------------------------
# دریافت عکس مرتبط از Pexels
# ---------------------------------------------------------

def get_image(query):

    if not PEXELS_API_KEY:
        return None

    try:

        headers = {
            "Authorization": PEXELS_API_KEY
        }

        response = requests.get(
            "https://api.pexels.com/v1/search",
            headers=headers,
            params={
                "query": query,
                "per_page": 5,
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


# ---------------------------------------------------------
# ارسال متن به تلگرام
# ---------------------------------------------------------

def send_message(text):

    try:

        response = requests.post(
            f"{TELEGRAM_URL}/sendMessage",
            data={
                "chat_id": CHANNEL_ID,
                "text": text,
                "disable_web_page_preview": False
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


# ---------------------------------------------------------
# ارسال عکس + متن
# ---------------------------------------------------------

def send_photo(image_url, caption):

    try:

        response = requests.post(
            f"{TELEGRAM_URL}/sendPhoto",
            data={
                "chat_id": CHANNEL_ID,
                "photo": image_url,
                "caption": caption
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


# ---------------------------------------------------------
# ساخت پست
# ---------------------------------------------------------

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
📰 خبر اقتصادی

🇬🇧 منبع: {source}

🔹 تیتر اصلی:
{original_title}

🇮🇷 ترجمه تیتر:
{translated}

{impact}

🔗 منبع خبر:
{news['link']}
"""

    post += COMPANY_FOOTER

    return post.strip()


# ---------------------------------------------------------
# اجرای اصلی
# ---------------------------------------------------------

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

        post = make_post(news)

        # عکس مرتبط
        image_query = (
            "steel industry "
            "steel factory iron"
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