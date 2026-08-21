import os
import re
import json
import hashlib
import requests
import feedparser
from bs4 import BeautifulSoup
from urllib.parse import quote
from datetime import datetime

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

HISTORY_FILE = "news_history.json"

# =========================================================
# منابع خبر
# =========================================================

RSS_FEEDS = [
    (
        "Reuters",
        "https://news.google.com/rss/search?q=site%3Areuters.com+steel+OR+%22iron+ore%22+OR+steel+market&hl=en-US&gl=US&ceid=US:en"
    ),
    (
        "Bloomberg",
        "https://news.google.com/rss/search?q=site%3Abloomberg.com+steel+OR+%22iron+ore%22+OR+steel+market&hl=en-US&gl=US&ceid=US:en"
    ),
    (
        "SteelOrbis",
        "https://www.steelorbis.com/steel-news/latest-news/"
    ),
]

# =========================================================
# کلمات مرتبط با بازار فولاد
# =========================================================

KEYWORDS = [
    "steel",
    "iron ore",
    "rebar",
    "billet",
    "scrap",
    "hot rolled",
    "cold rolled",
    "steel mill",
    "steel price",
    "iron ore price",
    "coking coal",
    "metallurgy",
    "steel demand",
    "steel production",
    "steel exports",
    "steel imports",
    "tariff",
    "sanction",
    "china steel",
    "china",
    "iran",
    "dollar",
    "oil",
    "inflation",
    "interest rate",
    "fed",
    "فولاد",
    "آهن",
    "میلگرد",
    "شمش",
    "سنگ آهن",
    "قراضه",
    "صادرات",
    "واردات",
    "تحریم",
    "دلار",
    "ارز",
    "بورس",
    "تورم",
]

# =========================================================
# ابزارها
# =========================================================

def clean(text):
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def load_history():
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except Exception:
        return set()


def save_history(history):
    try:
        data = list(history)[-500:]
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("History save error:", e)


def make_id(title, link):
    return hashlib.sha256(
        (title + link).encode("utf-8")
    ).hexdigest()


# =========================================================
# ترجمه تیتر
# =========================================================

def translate_to_persian(text):

    if not text:
        return ""

    try:
        url = "https://translate.googleapis.com/translate_a/single"

        params = {
            "client": "gtx",
            "sl": "auto",
            "tl": "fa",
            "dt": "t",
            "q": text
        }

        response = requests.get(
            url,
            params=params,
            timeout=15
        )

        if response.status_code == 200:
            data = response.json()

            result = ""

            for item in data[0]:
                if item and item[0]:
                    result += item[0]

            if result:
                return result.strip()

    except Exception as e:
        print("Translation error:", e)

    return text


# =========================================================
# تشخیص ارتباط خبر با فولاد
# =========================================================

def relevance(title, summary):

    text = (
        title + " " + summary
    ).lower()

    score = 0

    for keyword in KEYWORDS:

        if keyword.lower() in text:
            score += 1

    return score


# =========================================================
# تحلیل اثر خبر روی قیمت فولاد
# =========================================================

def analyze_impact(title, summary):

    text = (
        title + " " + summary
    ).lower()

    bullish = [
        "steel prices rise",
        "steel price rises",
        "iron ore rises",
        "iron ore price rises",
        "demand rises",
        "demand increases",
        "production cuts",
        "production cut",
        "supply cut",
        "shortage",
        "tariff",
        "sanction",
        "export restriction",
        "stimulus",
        "construction rises",
        "dollar rises",
        "oil rises",
        "inflation rises",
        "فولاد افزایش",
        "افزایش قیمت",
        "افزایش تقاضا",
        "کاهش عرضه",
        "تحریم",
        "محدودیت صادرات",
        "افزایش دلار",
        "افزایش تورم",
        "افزایش هزینه",
    ]

    bearish = [
        "steel prices fall",
        "steel price falls",
        "iron ore falls",
        "iron ore price falls",
        "demand falls",
        "demand decreases",
        "oversupply",
        "production increases",
        "steel production rises",
        "recession",
        "construction falls",
        "dollar falls",
        "oil falls",
        "interest rate hike",
        "کاهش قیمت",
        "کاهش تقاضا",
        "افزایش عرضه",
        "رکود",
        "کاهش تولید",
        "کاهش دلار",
        "کاهش تورم",
    ]

    bullish_score = 0
    bearish_score = 0

    for word in bullish:
        if word.lower() in text:
            bullish_score += 1

    for word in bearish:
        if word.lower() in text:
            bearish_score += 1

    if bullish_score > bearish_score:

        if bullish_score >= 3:
            strength = "زیاد"
        else:
            strength = "متوسط"

        return (
            "🟢 صعودی",
            strength,
            "این خبر می‌تواند از افزایش قیمت آهن و فولاد حمایت کند."
        )

    if bearish_score > bullish_score:

        if bearish_score >= 3:
            strength = "زیاد"
        else:
            strength = "متوسط"

        return (
            "🔴 نزولی",
            strength,
            "این خبر می‌تواند روی قیمت آهن و فولاد فشار کاهشی ایجاد کند."
        )

    return (
        "🟡 خنثی",
        "کم",
        "فعلاً اثر مستقیم و مشخصی روی قیمت آهن و فولاد دیده نمی‌شود."
    )


# =========================================================
# عکس مرتبط از Pexels
# =========================================================

def get_pexels_image(title):

    if not PEXELS_API_KEY:
        return None

    try:

        search_terms = [
            "steel factory",
            "steel industry",
            "iron ore",
            "steel mill"
        ]

        query = "steel industry"

        text = title.lower()

        if "iron ore" in text or "سنگ آهن" in text:
            query = "iron ore"

        elif "rebar" in text or "میلگرد" in text:
            query = "steel construction"

        elif "steel mill" in text:
            query = "steel mill"

        url = "https://api.pexels.com/v1/search"

        headers = {
            "Authorization": PEXELS_API_KEY
        }

        params = {
            "query": query,
            "per_page": 10,
            "orientation": "landscape"
        }

        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=20
        )

        if response.status_code != 200:
            print("Pexels error:", response.text)
            return None

        data = response.json()

        photos = data.get("photos", [])

        if not photos:
            return None

        photo = photos[0]

        return photo["src"]["large2x"]

    except Exception as e:

        print("Pexels error:", e)
        return None


# =========================================================
# ارسال متن به تلگرام
# =========================================================

def telegram_message(text):

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    response = requests.post(
        url,
        data={
            "chat_id": CHANNEL_ID,
            "text": text,
            "disable_web_page_preview": False
        },
        timeout=30
    )

    print(
        "Telegram message:",
        response.status_code
    )

    return response.status_code == 200


# =========================================================
# ارسال عکس + کپشن
# =========================================================

def telegram_photo(photo_url, caption):

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

    response = requests.post(
        url,
        data={
            "chat_id": CHANNEL_ID,
            "photo": photo_url,
            "caption": caption
        },
        timeout=40
    )

    print(
        "Telegram photo:",
        response.status_code
    )

    if response.status_code != 200:
        print(response.text)

    return response.status_code == 200


# =========================================================
# دریافت خبر از SteelOrbis
# =========================================================

def get_steelorbis():

    results = []

    try:

        url = "https://www.steelorbis.com/steel-news/latest-news/"

        headers = {
            "User-Agent":
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)"
        }

        response = requests.get(
            url,
            headers=headers,
            timeout=30
        )

        if response.status_code != 200:
            print("SteelOrbis status:", response.status_code)
            return results

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        for a in soup.find_all("a", href=True):

            title = clean(a.get_text(" ", strip=True))

            href = a.get("href")

            if not title or not href:
                continue

            if len(title) < 25:
                continue

            score = relevance(
                title,
                ""
            )

            if score <= 0:
                continue

            if href.startswith("/"):
                href = "https://www.steelorbis.com" + href

            results.append({
                "source": "SteelOrbis",
                "title": title,
                "summary": "",
                "link": href,
                "score": score
            })

    except Exception as e:

        print("SteelOrbis error:", e)

    return results


# =========================================================
# دریافت اخبار Reuters و Bloomberg
# =========================================================

def get_rss_news():

    results = []

    for source, rss_url in RSS_FEEDS[:2]:

        try:

            print(
                "Reading:",
                source
            )

            feed = feedparser.parse(
                rss_url
            )

            for entry in feed.entries[:20]:

                title = clean(
                    entry.get("title", "")
                )

                summary = clean(
                    entry.get("summary", "")
                )

                link = entry.get(
                    "link",
                    ""
                )

                if not title or not link:
                    continue

                # Google News گاهی نام منبع را به تیتر اضافه می‌کند
                title = re.sub(
                    r"\s+-\s+(Reuters|Bloomberg)$",
                    "",
                    title,
                    flags=re.IGNORECASE
                )

                score = relevance(
                    title,
                    summary
                )

                if score <= 0:
                    continue

                results.append({
                    "source": source,
                    "title": title,
                    "summary": summary,
                    "link": link,
                    "score": score
                })

        except Exception as e:

            print(
                source,
                "error:",
                e
            )

    return results


# =========================================================
# ساخت پست
# =========================================================

def create_post(item):

    original_title = item["title"]

    persian_title = translate_to_persian(
        original_title
    )

    direction, strength, explanation = analyze_impact(
        original_title,
        item["summary"]
    )

    now = datetime.now().strftime(
        "%Y/%m/%d - %H:%M"
    )

    caption = (
        "🏭 خبر بازار فولاد\n\n"

        f"📰 {persian_title}\n\n"

        f"🌐 منبع: {item['source']}\n"

        "━━━━━━━━━━━━━━\n"

        "📊 اثر احتمالی بر بازار آهن و فولاد ایران\n\n"

        f"جهت اثر: {direction}\n"
        f"شدت اثر: {strength}\n\n"

        f"💡 تحلیل: {explanation}\n\n"

        "━━━━━━━━━━━━━━\n"

        f"🕐 {now}\n\n"

        f"🔗 منبع اصلی:\n{item['link']}\n\n"

        "⚠️ تحلیل فوق برآورد احتمالی اثر خبر بر بازار است و توصیه خرید یا فروش نیست."
    )

    return caption


# =========================================================
# اجرای اصلی
# =========================================================

def main():

    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN is missing"
        )

    if not CHANNEL_ID:
        raise RuntimeError(
            "CHANNEL_ID is missing"
        )

    history = load_history()

    all_news = []

    # Reuters + Bloomberg
    all_news.extend(
        get_rss_news()
    )

    # SteelOrbis
    all_news.extend(
        get_steelorbis()
    )

    print(
        "TOTAL CANDIDATES:",
        len(all_news)
    )

    unique = {}

    for item in all_news:

        news_id = make_id(
            item["title"],
            item["link"]
        )

        if news_id in history:
            continue

        unique[news_id] = {
            **item,
            "id": news_id
        }

    news = list(
        unique.values()
    )

    news.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    if not news:

        print(
            "No new news."
        )

        save_history(history)

        return

    # فقط یک خبر در هر اجرا
    selected = news[0]

    print(
        "SELECTED:",
        selected["source"],
        selected["title"]
    )

    caption = create_post(
        selected
    )

    photo = get_pexels_image(
        selected["title"]
    )

    sent = False

    if photo:

        sent = telegram_photo(
            photo,
            caption
        )

    if not sent:

        sent = telegram_message(
            caption
        )

    if sent:

        history.add(
            selected["id"]
        )

        save_history(
            history
        )

        print(
            "✅ NEWS SENT"
        )

    else:

        print(
            "❌ NEWS NOT SENT"
        )


if __name__ == "__main__":
    main()