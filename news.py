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
# =========================================================
# تنظیمات سخت‌گیرانه انتشار
# =========================================================
# فقط مهم‌ترین خبر در هر اجرا
MAX_POSTS_PER_RUN = 1
# حداقل امتیاز برای انتشار
MIN_NEWS_SCORE = 70
# حداکثر تعداد خبر بررسی‌شده از هر منبع
MAX_FEED_ITEMS = 30
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
        "name": "فولادبان",
        "url": "https://fouladban.com/feed/",
        "category": "steel",
        "priority": 15
    },
    {
        "name": "اقتصادنیوز",
        "url": "https://www.eghtesadnews.com/rss",
        "category": "iran_economy",
        "priority": 10
    },
    {
        "name": "تجارت‌نیوز",
        "url": "https://tejaratnews.com/feed/",
        "category": "iran_economy",
        "priority": 8
    },
    {
        "name": "اکوایران",
        "url": "https://ecoiran.com/rss",
        "category": "iran_economy",
        "priority": 8
    }
]
# =========================================================
# 🇮🇷 ایران
# =========================================================
IRAN_KEYWORDS = [
    "ایران",
    "ایرانی",
    "تهران",
    "iran",
    "iranian",
    "tehran",
    "ریال",
    "rial",
    "اقتصاد ایران",
    "بازار ایران",
    "بانک مرکزی ایران",
    "central bank of iran",
    "دولت ایران",
    "مجلس ایران"
]
# =========================================================
# 🏭 فولاد و بازار آهن
# =========================================================
STEEL_KEYWORDS = [
    "فولاد",
    "بازار فولاد",
    "قیمت فولاد",
    "فولاد ایران",
    "آهن",
    "بازار آهن",
    "قیمت آهن",
    "میلگرد",
    "قیمت میلگرد",
    "تیرآهن",
    "قیمت تیرآهن",
    "شمش",
    "شمش فولادی",
    "قیمت شمش",
    "سنگ آهن",
    "سنگ‌آهن",
    "آهن اسفنجی",
    "گندله",
    "کنسانتره",
    "ورق",
    "ورق فولادی",
    "ورق گرم",
    "ورق سرد",
    "نبشی",
    "ناودانی",
    "فولاد خام",
    "تولید فولاد",
    "صادرات فولاد",
    "واردات فولاد",
    "بورس کالا",
    "عرضه فولاد",
    "عرضه شمش",
    "عرضه میلگرد",
    "زنجیره فولاد",
    "فولادساز",
    "فولادسازان",
    "محدودیت برق فولاد",
    "محدودیت گاز فولاد",
    "برق صنایع فولادی",
    "گاز صنایع فولادی",
    "steel",
    "steel price",
    "steel prices",
    "steel production",
    "steel exports",
    "steel imports",
    "iron ore",
    "rebar",
    "billet",
    "slab"
]
# =========================================================
# 💵 دلار و ارز ایران
# =========================================================
CURRENCY_KEYWORDS = [
    "دلار",
    "قیمت دلار",
    "نرخ دلار",
    "دلار آزاد",
    "دلار تهران",
    "دلار ایران",
    "بازار ارز",
    "بازار ارز ایران",
    "نرخ ارز",
    "قیمت ارز",
    "مرکز مبادله",
    "مرکز مبادله ارز",
    "دلار مرکز مبادله",
    "حواله دلار",
    "اسکناس دلار",
    "ارزش ریال",
    "دلار گران شد",
    "دلار ارزان شد",
    "افزایش قیمت دلار",
    "کاهش قیمت دلار",
    "جهش دلار",
    "سقوط دلار",
    "افزایش نرخ ارز",
    "کاهش نرخ ارز"
]
# =========================================================
# ⛽ سوخت و انرژی
# =========================================================
FUEL_KEYWORDS = [
    "بنزین",
    "قیمت بنزین",
    "بنزین ایران",
    "سهمیه بنزین",
    "کارت سوخت",
    "سوخت ایران",
    "سوخت",
    "گازوئیل",
    "قیمت گازوئیل",
    "سهمیه سوخت",
    "افزایش قیمت بنزین",
    "کاهش قیمت بنزین",
    "بنزین چند نرخی",
    "بنزین چندنرخی",
    "پمپ بنزین",
    "جایگاه سوخت",
    "شرکت ملی پالایش و پخش"
]
# =========================================================
# ⚡ برق و گاز صنایع
# =========================================================
ENERGY_KEYWORDS = [
    "قطعی برق صنایع",
    "قطعی برق صنعت",
    "محدودیت برق صنایع",
    "محدودیت برق فولاد",
    "خاموشی صنایع",
    "محدودیت گاز صنایع",
    "محدودیت گاز فولاد",
    "قطع گاز صنایع",
    "قطع گاز فولاد",
    "برق صنایع فولادی",
    "گاز صنایع فولادی",
    "ناترازی برق",
    "ناترازی گاز",
    "تعرفه برق صنایع",
    "تعرفه گاز صنایع",
    "افزایش قیمت برق",
    "افزایش قیمت گاز"
]
# =========================================================
# 🪙 طلا
# =========================================================
GOLD_IRAN_KEYWORDS = [
    "طلا",
    "قیمت طلا",
    "طلای ۱۸ عیار",
    "طلای 18 عیار",
    "طلای آبشده",
    "آبشده",
    "سکه",
    "سکه امامی",
    "بازار طلا ایران",
    "بازار طلای ایران",
    "قیمت طلای ایران",
    "افزایش قیمت طلا",
    "کاهش قیمت طلا",
    "رشد قیمت طلا",
    "افت قیمت طلا"
]
# =========================================================
# 🌎 طلای جهانی
# =========================================================
GOLD_GLOBAL_KEYWORDS = [
    "اونس طلا",
    "اونس جهانی",
    "قیمت جهانی طلا",
    "طلای جهانی",
    "gold",
    "gold price",
    "gold prices",
    "spot gold",
    "gold futures"
]
# =========================================================
# ⚔️ اتفاقات مهم ایران و آمریکا
# =========================================================
WAR_KEYWORDS = [
    "ایران و آمریکا",
    "ایران آمریکا",
    "جنگ ایران و آمریکا",
    "درگیری ایران و آمریکا",
    "حمله آمریکا به ایران",
    "حمله ایران به آمریکا",
    "حملات آمریکا به ایران",
    "حملات ایران به آمریکا",
    "آمریکا به ایران حمله کرد",
    "ایران به آمریکا حمله کرد",
    "تنش ایران و آمریکا",
    "مذاکرات ایران و آمریکا",
    "تهدید آمریکا علیه ایران",
    "تهدید ایران علیه آمریکا",
    "تحریم ایران",
    "تحریم‌های آمریکا علیه ایران",
    "تحریم آمریکا علیه ایران",
    "تنگه هرمز",
    "خلیج فارس",
    "آتش بس ایران آمریکا",
    "آتش‌بس ایران آمریکا",
    "Iran US war",
    "Iran United States conflict",
    "Iran US conflict",
    "US attack on Iran",
    "Iran attack on US"
]
# =========================================================
# 🇮🇷 اقتصاد داخلی
# =========================================================
ECONOMY_KEYWORDS = [
    "بانک مرکزی",
    "مرکز مبادله",
    "وزارت صمت",
    "وزارت صنعت",
    "گمرک ایران",
    "صادرات ایران",
    "واردات ایران",
    "مالیات",
    "بودجه",
    "نقدینگی",
    "تورم",
    "نرخ بهره",
    "سیاست پولی",
    "دولت",
    "بورس کالا",
    "بورس تهران",
    "سامانه نیما",
    "محدودیت برق",
    "قطعی برق",
    "محدودیت گاز",
    "گاز صنایع",
    "انرژی ایران"
]
# =========================================================
# 🔥 کلمات نشان‌دهنده اتفاق مهم
# =========================================================
MAJOR_EVENT_KEYWORDS = [
    # افزایش / کاهش شدید
    "جهش",
    "سقوط",
    "شوک",
    "رکورد",
    "رکوردشکنی",
    "افزایش شدید",
    "کاهش شدید",
    "افزایش قابل توجه",
    "کاهش قابل توجه",
    "افزایش چشمگیر",
    "کاهش چشمگیر",
    "رشد شدید",
    "افت شدید",
    # تصمیم
    "تصمیم جدید",
    "تصمیم مهم",
    "تصمیم دولت",
    "ابلاغ شد",
    "ابلاغیه",
    "مصوبه جدید",
    "تصویب شد",
    "تصویب",
    "ممنوع شد",
    "ممنوعیت",
    "آزاد شد",
    "آزادسازی",
    "اعلام کرد",
    "اعلام شد",
    # تحریم
    "تحریم جدید",
    "تحریم‌های جدید",
    "تحریم جدید آمریکا",
    "تحریم شد",
    "تحریم شدند",
    # انرژی
    "قطع برق",
    "قطع گاز",
    "محدودیت شدید",
    # فولاد
    "کاهش تولید",
    "افزایش تولید",
    "کاهش عرضه",
    "افزایش عرضه",
    "کاهش صادرات",
    "افزایش صادرات",
    "محدودیت صادرات",
    "ممنوعیت صادرات",
    "محدودیت واردات",
    "ممنوعیت واردات"
]
# =========================================================
# 🚫 کلمات نشان‌دهنده خبر معمولی
# =========================================================
WEAK_NEWS_KEYWORDS = [
    "پیش بینی",
    "پیش‌بینی",
    "کارشناس گفت",
    "کارشناسان گفتند",
    "به گفته کارشناسان",
    "ممکن است",
    "احتمالا",
    "احتمالاً",
    "در روزهای آینده",
    "تحلیل بازار",
    "بررسی بازار",
    "آخرین قیمت",
    "قیمت امروز",
    "قیمت لحظه‌ای",
    "قیمت لحظه ای",
    "گزارش بازار",
    "معاملات امروز",
    "معاملات روزانه",
    "عرضه امروز",
    "عرضه فردا",
    "آمار معاملات"
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
            data = json.load(file)
            if isinstance(data, list):
                return data
            return []
    except Exception as e:
        print(
            "History load error:",
            e
        )
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
    text = clean_text(
        text
    ).lower()
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
# تشخیص کلمه
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
    if " " in keyword:
        return keyword in text
    return re.search(
        rf"(?<!\w){re.escape(keyword)}(?!\w)",
        text
    ) is not None
# =========================================================
# پیدا کردن کلمات
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
# تشخیص فارسی
# =========================================================
def is_persian_text(text):
    if not text:
        return False
    persian_chars = re.findall(
        r"[\u0600-\u06FF]",
        text
    )
    latin_chars = re.findall(
        r"[A-Za-z]",
        text
    )
    return len(
        persian_chars
    ) >= len(
        latin_chars
    )
# =========================================================
# تشخیص موضوع
# =========================================================
def detect_categories(
    title,
    description
):
    text = normalize_text(
        title +
        " " +
        description
    )
    steel_hits = find_hits(
        text,
        STEEL_KEYWORDS
    )
    currency_hits = find_hits(
        text,
        CURRENCY_KEYWORDS
    )
    fuel_hits = find_hits(
        text,
        FUEL_KEYWORDS
    )
    energy_hits = find_hits(
        text,
        ENERGY_KEYWORDS
    )
    gold_iran_hits = find_hits(
        text,
        GOLD_IRAN_KEYWORDS
    )
    gold_global_hits = find_hits(
        text,
        GOLD_GLOBAL_KEYWORDS
    )
    war_hits = find_hits(
        text,
        WAR_KEYWORDS
    )
    economy_hits = find_hits(
        text,
        ECONOMY_KEYWORDS
    )
    iran_hits = find_hits(
        text,
        IRAN_KEYWORDS
    )
    major_hits = find_hits(
        text,
        MAJOR_EVENT_KEYWORDS
    )
    weak_hits = find_hits(
        text,
        WEAK_NEWS_KEYWORDS
    )
    categories = []
    if steel_hits:
        categories.append("steel")
    if currency_hits:
        categories.append("currency")
    if fuel_hits:
        categories.append("fuel")
    if energy_hits:
        categories.append("energy")
    if gold_iran_hits or gold_global_hits:
        categories.append("gold")
    if war_hits:
        categories.append("war")
    if economy_hits:
        categories.append("iran_economy")
    return {
        "categories": categories,
        "steel_hits": steel_hits,
        "currency_hits": currency_hits,
        "fuel_hits": fuel_hits,
        "energy_hits": energy_hits,
        "gold_iran_hits": gold_iran_hits,
        "gold_global_hits": gold_global_hits,
        "war_hits": war_hits,
        "economy_hits": economy_hits,
        "iran_hits": iran_hits,
        "major_hits": major_hits,
        "weak_hits": weak_hits
    }
# =========================================================
# امتیازدهی سخت‌گیرانه
# =========================================================
def score_news(
    title,
    description,
    source
):
    analysis = detect_categories(
        title,
        description
    )
    text = normalize_text(
        title +
        " " +
        description
    )
    score = 0
    steel_hits = analysis["steel_hits"]
    currency_hits = analysis["currency_hits"]
    fuel_hits = analysis["fuel_hits"]
    energy_hits = analysis["energy_hits"]
    gold_iran_hits = analysis[
        "gold_iran_hits"
    ]
    gold_global_hits = analysis[
        "gold_global_hits"
    ]
    war_hits = analysis["war_hits"]
    economy_hits = analysis[
        "economy_hits"
    ]
    iran_hits = analysis["iran_hits"]
    major_hits = analysis[
        "major_hits"
    ]
    weak_hits = analysis[
        "weak_hits"
    ]
    # =====================================================
    # 🚫 خبرهای ضعیف
    # =====================================================
    if weak_hits:
        score -= 30
    # =====================================================
    # 🏭 فولاد
    # =====================================================
    if steel_hits:
        score += 35
    if steel_hits and iran_hits:
        score += 20
    if steel_hits and major_hits:
        score += 25
    if steel_hits and currency_hits:
        score += 25
    if steel_hits and energy_hits:
        score += 30
    # =====================================================
    # 💵 دلار
    # =====================================================
    if currency_hits:
        iran_currency_context = any(
            contains_keyword(
                text,
                word
            )
            for word in [
                "ایران",
                "تهران",
                "بازار آزاد",
                "مرکز مبادله",
                "ریال",
                "بانک مرکزی",
                "دلار ایران",
                "دلار تهران"
            ]
        )
        if iran_currency_context:
            score += 25
        else:
            return {
                "score": 0,
                **analysis
            }
    # دلار فقط وقتی مهم است که اتفاق مهمی رخ داده باشد
    if currency_hits and major_hits:
        score += 30
    # =====================================================
    # ⛽ سوخت
    # =====================================================
    if fuel_hits:
        score += 20
    if fuel_hits and major_hits:
        score += 30
    # =====================================================
    # ⚡ انرژی
    # =====================================================
    if energy_hits:
        score += 30
    if energy_hits and steel_hits:
        score += 35
    if energy_hits and major_hits:
        score += 25
    # =====================================================
    # 🪙 طلا
    # =====================================================
    if gold_iran_hits:
        score += 15
    if gold_global_hits:
        score += 15
    if (
        gold_iran_hits
        and currency_hits
    ):
        score += 25
    if (
        gold_iran_hits
        and major_hits
    ):
        score += 20
    # =====================================================
    # ⚔️ ایران و آمریکا
    # =====================================================
    if war_hits:
        score += 35
    if war_hits and major_hits:
        score += 30
    if war_hits and steel_hits:
        score += 30
    if war_hits and currency_hits:
        score += 25
    # =====================================================
    # 🇮🇷 اقتصاد داخلی
    # =====================================================
    if economy_hits:
        score += 15
    if economy_hits and steel_hits:
        score += 25
    if economy_hits and currency_hits:
        score += 20
    if economy_hits and major_hits:
        score += 20
    # =====================================================
    # 🔥 خبر خیلی مهم
    # =====================================================
    if len(major_hits) >= 2:
        score += 20
    # =====================================================
    # 🏭 اولویت منبع
    # =====================================================
    source_bonus = {
        "فولادبان": 15,
        "اقتصادنیوز": 10,
        "تجارت‌نیوز": 8,
        "اکوایران": 8
    }
    score += source_bonus.get(
        source,
        0
    )
    # =====================================================
    # 🚫 خبر بدون موضوع اصلی
    # =====================================================
    if not (
        steel_hits
        or currency_hits
        or fuel_hits
        or energy_hits
        or gold_iran_hits
        or gold_global_hits
        or war_hits
        or economy_hits
    ):
        score = 0
    # =====================================================
    # 🚫 خبر اقتصادی معمولی
    # =====================================================
    if (
        economy_hits
        and not steel_hits
        and not currency_hits
        and not energy_hits
        and not war_hits
        and not major_hits
    ):
        score = 0
    return {
        "score": score,
        **analysis
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
        normalize_text(
            title
        )
    )
# =========================================================
# تشخیص خبر تکراری
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
    for old_id in history[-300:]:
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
        if similarity >= 0.65:
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
            for item in feed.entries[
                :MAX_FEED_ITEMS
            ]:
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
                # =================================================
                # امتیاز کافی نیست
                # =================================================
                if (
                    analysis["score"]
                    < MIN_NEWS_SCORE
                ):
                    continue
                news_id = make_news_id(
                    title,
                    link
                )
                # =================================================
                # خبر قبلاً منتشر شده
                # =================================================
                if news_id in history:
                    print(
                        "DUPLICATE URL:",
                        title
                    )
                    continue
                # =================================================
                # تیتر بسیار مشابه
                # =================================================
                if is_duplicate_title(
                    title,
                    history
                ):
                    print(
                        "DUPLICATE TITLE:",
                        title
                    )
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
                    "category":
                        analysis["categories"]
                })
        except Exception as e:
            print(
                f"Feed error {feed_info['name']}: {e}"
            )
    # =========================================================
    # مهم‌ترین خبر اول
    # =========================================================
    results.sort(
        key=lambda x:
            x["score"],
        reverse=True
    )
    return results
# =========================================================
# ترجمه تیتر انگلیسی
# =========================================================
def translate_title(title):
    title = clean_text(
        title
    )
    if is_persian_text(
        title
    ):
        return title
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
# تحلیل اثر بر بازار فولاد
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
        "افزایش قیمت",
        "افزایش تقاضا",
        "کاهش تولید",
        "کاهش عرضه",
        "رشد قیمت",
        "دلار گران شد",
        "جهش دلار",
        "افزایش قیمت طلا",
        "رشد قیمت طلا",
        "افزایش قیمت بنزین",
        "تشدید تنش",
        "حمله",
        "جنگ",
        "تحریم",
        "قطع برق",
        "محدودیت برق",
        "قطع گاز",
        "محدودیت گاز",
        "price rise",
        "price increase",
        "strong demand",
        "production cut",
        "supply cut",
        "gold rises",
        "gold increase",
        "dollar rises",
        "attack",
        "war",
        "sanctions"
    ]
    negative_words = [
        "کاهش قیمت",
        "کاهش تقاضا",
        "افزایش تولید",
        "مازاد عرضه",
        "افت قیمت",
        "دلار ارزان شد",
        "سقوط دلار",
        "کاهش قیمت طلا",
        "افت قیمت طلا",
        "کاهش قیمت بنزین",
        "آتش بس",
        "آتش‌بس",
        "price fall",
        "price decrease",
        "weak demand",
        "oversupply",
        "production increase",
        "gold falls",
        "gold decrease",
        "dollar falls",
        "ceasefire"
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
    if positive and not negative:
        return (
            "🟢 اثر احتمالی بر بازار فولاد: افزایش\n"
            "احتمالاً باعث افزایش قیمت فولاد می‌شود."
        )
    if negative and not positive:
        return (
            "🔴 اثر احتمالی بر بازار فولاد: کاهش\n"
            "احتمالاً باعث کاهش قیمت فولاد می‌شود."
        )
    return (
        "🟡 اثر احتمالی بر بازار فولاد: نامشخص\n"
        "اثر مشخص و مستقیمی بر بازار فولاد ندارد."
    )
# =========================================================
# جستجوی عکس
# =========================================================
def make_image_query(
    news
):
    title = news["title"].lower()
    description = news[
        "description"
    ].lower()
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
        return "iron ore mining"
    if (
        "rebar" in text
        or "میلگرد" in text
    ):
        return "steel rebar construction"
    if (
        "billet" in text
        or "شمش" in text
    ):
        return "steel billet factory"
    if (
        "steel" in text
        or "فولاد" in text
        or "آهن" in text
    ):
        return "steel factory steel industry"
    if (
        "dollar" in text
        or "دلار" in text
        or "ارز" in text
    ):
        return "US dollar currency market"
    if (
        "gold" in text
        or "طلا" in text
        or "سکه" in text
    ):
        return "gold bars gold market"
    if (
        "بنزین" in text
        or "سوخت" in text
        or "گازوئیل" in text
    ):
        return "gas station fuel"
    if (
        "برق" in text
        or "گاز صنایع" in text
        or "انرژی" in text
    ):
        return "industrial electricity power plant"
    if (
        "آمریکا" in text
        or "ایران" in text
        or "war" in text
        or "attack" in text
    ):
        return "Iran United States conflict"
    return "Iran economy financial market"
# =========================================================
# دریافت عکس
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
# ارسال پیام
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
                    True
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
    if is_persian_text(
        original_title
    ):
        post = f"""
📰 خبر اقتصادی و بازار
📰 منبع:
{source}
🔹 خبر:
{original_title}
{impact}
"""
    else:
        post = f"""
📰 خبر اقتصادی و بازار
📰 منبع:
{source}
🔹 تیتر اصلی:
{original_title}
🇮🇷 ترجمه:
{translated}
{impact}
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
        "STRICT IMPORTANT NEWS MODE"
    )
    print(
        "Maximum posts per run:",
        MAX_POSTS_PER_RUN
    )
    print(
        "Minimum score:",
        MIN_NEWS_SCORE
    )
    print(
        "========================================"
    )
    news_items = get_news()
    print(
        "Qualified important news:",
        len(news_items)
    )
    # =====================================================
    # هیچ خبر واقعاً مهمی نیست
    # =====================================================
    if not news_items:
        print(
            "No sufficiently important news."
        )
        print(
            "Nothing will be posted."
        )
        return
    # =====================================================
    # فقط مهم‌ترین خبر
    # =====================================================
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
# =========================================================
# شروع
# =========================================================
if __name__ == "__main__":
    main()