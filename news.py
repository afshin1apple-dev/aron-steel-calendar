import os
import json
import hashlib
import re
import requests
import feedparser
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from html import unescape

TOKEN = os.environ["BOT_TOKEN"]
CHANNEL = os.environ["CHANNEL_ID"]

HISTORY_FILE = "news_history.json"

TEHRAN = ZoneInfo("Asia/Tehran")

FEEDS = [
    "https://fouladban.com/feed/",
]

KEYWORDS = [
    "فولاد",
    "آهن",
    "میلگرد",
    "تیرآهن",
    "نبشی",
    "ناودانی",
    "شمش",
    "بورس کالا",
    "بورس",
    "دلار",
    "طلا",
    "سکه",
    "ارز",
    "بانک مرکزی",
    "وزارت صمت",
    "صادرات",
    "واردات",
    "نفت",
    "پتروشیمی",
    "اقتصاد",
    "سوخت",
    "بنزین",
]


def load_history():
    if not os.path.exists(HISTORY_FILE):
        return set()

    try:
        with open(
            HISTORY_FILE,
            "r",
            encoding="utf-8"
        ) as f:
            return set(json.load(f))
    except Exception:
        return set()


def save_history(history):
    with open(
        HISTORY_FILE,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            list(history)[-1000:],
            f,
            ensure_ascii=False,
            indent=2
        )


def make_id(title, link):
    return hashlib.sha256(
        (title + link).encode("utf-8")
    ).hexdigest()


def clean_text(text):
    if not text:
        return ""

    text = unescape(text)

    text = re.sub(
        r"<[^>]+>",
        " ",
        text
    )

    # حذف عبارت‌های تبلیغاتی انتهای RSS
    garbage_patterns = [
        r"اولین بار در فولادبان.*",
        r"پدیدار شد.*",
        r"این مطلب.*",
    ]

    for pattern in garbage_patterns:
        text = re.sub(
            pattern,
            "",
            text,
            flags=re.IGNORECASE
        )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def is_relevant(title, summary):
    text = (
        title + " " + summary
    ).lower()

    return any(
        keyword.lower() in text
        for keyword in KEYWORDS
    )


def get_item_date(item):

    # تاریخ انتشار RSS
    published = item.get(
        "published_parsed"
    )

    if not published:
        published = item.get(
            "updated_parsed"
        )

    if not published:
        return None

    try:
        dt = datetime(
            *published[:6],
            tzinfo=timezone.utc
        )

        return dt.astimezone(
            TEHRAN
        )

    except Exception:
        return None


def get_news():

    news = []

    today = datetime.now(
        TEHRAN
    ).date()

    for feed_url in FEEDS:

        try:

            response = requests.get(
                feed_url,
                headers={
                    "User-Agent":
                        "Mozilla/5.0"
                },
                timeout=20
            )

            response.raise_for_status()

            feed = feedparser.parse(
                response.content
            )

            for item in feed.entries[:30]:

                title = clean_text(
                    item.get(
                        "title",
                        ""
                    )
                )

                link = item.get(
                    "link",
                    ""
                ).strip()

                summary = clean_text(
                    item.get(
                        "summary",
                        ""
                    )
                )

                if not title or not link:
                    continue

                # -------------------------
                # فقط خبر امروز
                # -------------------------

                item_date = get_item_date(
                    item
                )

                if item_date is None:
                    print(
                        "Skipped: no date",
                        title
                    )
                    continue

                if item_date.date() != today:
                    print(
                        "Skipped old news:",
                        title,
                        item_date
                    )
                    continue

                # -------------------------
                # فیلتر موضوع
                # -------------------------

                if not is_relevant(
                    title,
                    summary
                ):
                    continue

                news_id = make_id(
                    title,
                    link
                )

                news.append({
                    "id": news_id,
                    "title": title,
                    "link": link,
                    "summary": summary,
                    "date": item_date
                })

        except Exception as e:

            print(
                "Feed error:",
                feed_url,
                e
            )

    # جدیدترین اول
    news.sort(
        key=lambda x: x["date"],
        reverse=True
    )

    return news


def send_news(news):

    title = clean_text(
        news["title"]
    )

    summary = clean_text(
        news["summary"]
    )

    # خلاصه کوتاه و تمیز
    if len(summary) > 450:
        summary = (
            summary[:450]
            + "..."
        )

    message = (
        "🚨 خبر فوری اقتصادی\n\n"
        f"📌 {title}\n\n"
    )

    if summary:
        message += (
            f"{summary}\n\n"
        )

    message += (
        "📰 منبع: فولادبان\n"
        f"🔗 {news['link']}\n\n"
        "🆔 @Arvand_Aron_Steel\n"
        "☎️ 021-22122239"
    )

    response = requests.post(
        f"https://api.telegram.org/"
        f"bot{TOKEN}/sendMessage",
        data={
            "chat_id": CHANNEL,
            "text": message,
            "disable_web_page_preview": False
        },
        timeout=30
    )

    if not response.ok:
        print(
            "Telegram error:",
            response.text
        )

    response.raise_for_status()

    print(
        "News sent:",
        title
    )


# =================================
# ساعت انتشار
# =================================

now = datetime.now(
    TEHRAN
)

start_time = now.replace(
    hour=8,
    minute=30,
    second=0,
    microsecond=0
)

end_time = now.replace(
    hour=17,
    minute=0,
    second=0,
    microsecond=0
)

if not (
    start_time
    <= now
    <= end_time
):

    print(
        "Outside news schedule."
    )

    exit()


# =================================
# اجرای ربات
# =================================

history = load_history()

news = get_news()

print(
    "Today's relevant news:",
    len(news)
)

sent = 0

for item in news:

    if item["id"] in history:
        continue

    send_news(item)

    history.add(
        item["id"]
    )

    sent += 1

    # حداکثر دو خبر در هر اجرا
    if sent >= 2:
        break


save_history(history)

print(
    f"News check finished. Sent: {sent}"
)