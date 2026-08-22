import os
import requests
import jdatetime

from datetime import datetime
from zoneinfo import ZoneInfo


# =========================================================
# تنظیمات
# =========================================================

TOKEN = os.environ["BOT_TOKEN"]
CHANNEL = os.environ["CHANNEL_ID"]
PEXELS_KEY = os.environ["PEXELS_API_KEY"]

# توکن داخلی GitHub Actions
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

# نام Repository به صورت خودکار توسط GitHub
GITHUB_REPOSITORY = os.environ.get(
    "GITHUB_REPOSITORY",
    ""
)

# فایل وضعیت ارسال تقویم
STATE_FILE = "calendar_state.txt"


# =========================================================
# زمان ایران
# =========================================================

now = datetime.now(
    ZoneInfo("Asia/Tehran")
)

g = now.date()


# =========================================================
# تبدیل میلادی به شمسی
# =========================================================

j = jdatetime.date.fromgregorian(
    year=g.year,
    month=g.month,
    day=g.day
)


# =========================================================
# جلوگیری از ارسال دوباره
# =========================================================

today_key = (
    f"{j.year:04d}-"
    f"{j.month:02d}-"
    f"{j.day:02d}"
)


def get_saved_date():

    # اگر GitHub Token نداریم،
    # از فایل محلی استفاده می‌کنیم.

    if not GITHUB_TOKEN or not GITHUB_REPOSITORY:

        if not os.path.exists(
            STATE_FILE
        ):
            return ""

        try:

            with open(
                STATE_FILE,
                "r",
                encoding="utf-8"
            ) as f:

                return f.read().strip()

        except Exception:

            return ""


    # =====================================================
    # خواندن فایل وضعیت از GitHub
    # =====================================================

    try:

        url = (
            "https://api.github.com/repos/"
            f"{GITHUB_REPOSITORY}/contents/"
            f"{STATE_FILE}"
        )

        headers = {

            "Authorization":
                f"Bearer {GITHUB_TOKEN}",

            "Accept":
                "application/vnd.github+json"
        }

        response = requests.get(
            url,
            headers=headers,
            timeout=20
        )


        if response.status_code == 404:

            return ""


        if not response.ok:

            print(
                "GitHub state read error:",
                response.text
            )

            return ""


        data = response.json()


        import base64

        content = base64.b64decode(
            data["content"]
        ).decode(
            "utf-8"
        )


        return content.strip()


    except Exception as e:

        print(
            "State read error:",
            e
        )

        return ""


def save_date(date_value):

    # =====================================================
    # اگر GitHub Token نداریم
    # =====================================================

    if not GITHUB_TOKEN or not GITHUB_REPOSITORY:

        try:

            with open(
                STATE_FILE,
                "w",
                encoding="utf-8"
            ) as f:

                f.write(
                    date_value
                )

        except Exception as e:

            print(
                "Local state save error:",
                e
            )

        return


    # =====================================================
    # ذخیره وضعیت داخل GitHub
    # =====================================================

    try:

        import base64

        url = (
            "https://api.github.com/repos/"
            f"{GITHUB_REPOSITORY}/contents/"
            f"{STATE_FILE}"
        )

        headers = {

            "Authorization":
                f"Bearer {GITHUB_TOKEN}",

            "Accept":
                "application/vnd.github+json"
        }


        # بررسی اینکه فایل قبلاً وجود دارد یا نه

        get_response = requests.get(
            url,
            headers=headers,
            timeout=20
        )


        sha = None

        if get_response.status_code == 200:

            sha = get_response.json().get(
                "sha"
            )


        encoded_content = base64.b64encode(
            date_value.encode("utf-8")
        ).decode("utf-8")


        payload = {

            "message":
                f"Update calendar state {date_value}",

            "content":
                encoded_content
        }


        if sha:

            payload["sha"] = sha


        response = requests.put(

            url,

            headers=headers,

            json=payload,

            timeout=20
        )


        print(
            "GitHub state save:",
            response.status_code
        )

        print(
            response.text[:500]
        )


        if not response.ok:

            print(
                "WARNING: Could not save calendar state."
            )


    except Exception as e:

        print(
            "State save error:",
            e
        )


# =========================================================
# بررسی اینکه امروز قبلاً ارسال شده یا نه
# =========================================================

saved_date = get_saved_date()


print(
    "Iran time:",
    now.strftime(
        "%Y-%m-%d %H:%M:%S"
    )
)

print(
    "Today:",
    today_key
)

print(
    "Saved date:",
    saved_date
)


if saved_date == today_key:

    print(
        "Today's calendar has already been posted."
    )

    print(
        "Nothing to do."
    )

    raise SystemExit(0)


# =========================================================
# روزهای هفته
# =========================================================

weekdays = [

    "دوشنبه",
    "سه‌شنبه",
    "چهارشنبه",
    "پنجشنبه",
    "جمعه",
    "شنبه",
    "یکشنبه"
]


# =========================================================
# ماه‌های شمسی
# =========================================================

months = [

    "فروردین",
    "اردیبهشت",
    "خرداد",
    "تیر",
    "مرداد",
    "شهریور",
    "مهر",
    "آبان",
    "آذر",
    "دی",
    "بهمن",
    "اسفند"
]


# =========================================================
# مکان‌های ایران
# =========================================================

places = [

    ("ماسال", "Masal Iran"),

    ("رامسر", "Ramsar Iran"),

    ("فیلبند", "Filband Iran"),

    ("جنگل دوهزار", "Dohezar Forest Iran"),

    ("اورامانات", "Hawraman Iran"),

    ("دریاچه گهر", "Gahar Lake Iran"),

    ("کویر مرنجاب", "Maranjab Desert Iran"),

    ("کویر لوت", "Lut Desert Iran"),

    ("ابیانه", "Abyaneh Iran"),

    ("اصفهان", "Isfahan Iran"),

    ("شیراز", "Shiraz Iran"),

    ("یزد", "Yazd Iran"),

    ("قشم", "Qeshm Iran"),

    ("جزیره هرمز", "Hormuz Island Iran"),

    ("چابهار", "Chabahar Iran")
]


index = (
    g.toordinal()
    %
    len(places)
)


place_name, search_query = places[index]


# =========================================================
# جمله‌های انگیزشی
# =========================================================

quotes = [

    "هر روز یک قدم کوچک، تو را به یک هدف بزرگ نزدیک‌تر می‌کند.",

    "موفقیت نتیجه استمرار است، نه عجله.",

    "امروز فرصت تازه‌ای برای بهتر شدن است.",

    "به خودت اعتماد کن و ادامه بده.",

    "کارهای بزرگ از قدم‌های کوچک شروع می‌شوند.",

    "اگر شروع کنی، نصف مسیر را رفته‌ای.",

    "امروز را بهتر از دیروز بساز.",

    "هیچ تلاشی بی‌نتیجه نمی‌ماند.",

    "آرام و پیوسته جلو برو؛ مسیر ساخته می‌شود.",

    "به آینده‌ای که می‌خواهی بسازی فکر کن و از امروز شروع کن."
]


quote = quotes[
    g.toordinal() % len(quotes)
]


# =========================================================
# تعطیلات رسمی ایران در سال ۱۴۰۵
# =========================================================

holidays = {

    # فروردین
    (1, 1):
        "نوروز و عید فطر",

    (1, 2):
        "نوروز و عید فطر",

    (1, 3):
        "نوروز",

    (1, 4):
        "نوروز",

    (1, 12):
        "روز جمهوری اسلامی ایران",

    (1, 13):
        "روز طبیعت",

    (1, 24):
        "شهادت امام جعفر صادق (ع)",

    # خرداد
    (3, 6):
        "عید سعید قربان",

    (3, 14):
        "رحلت امام خمینی (ره) و عید غدیر خم",

    (3, 15):
        "قیام ۱۵ خرداد",

    # تیر
    (4, 3):
        "تاسوعای حسینی",

    (4, 4):
        "عاشورای حسینی",

    # مرداد
    (5, 13):
        "اربعین حسینی",

    (5, 21):
        "رحلت پیامبر اکرم (ص) و شهادت امام حسن مجتبی (ع)",

    (5, 22):
        "شهادت امام رضا (ع)",

    (5, 30):
        "شهادت امام حسن عسکری (ع)",

    # شهریور
    (6, 8):
        "ولادت پیامبر اکرم (ص) و ولادت امام جعفر صادق (ع)",

    # آبان
    (8, 22):
        "شهادت حضرت فاطمه زهرا (س)",

    # دی
    (10, 2):
        "ولادت امام علی (ع) و روز پدر",

    (10, 16):
        "مبعث پیامبر اکرم (ص)",

    # بهمن
    (11, 4):
        "ولادت حضرت قائم (عج)",

    (11, 22):
        "پیروزی انقلاب اسلامی ایران",

    # اسفند
    (12, 9):
        "شهادت حضرت علی (ع)",

    (12, 19):
        "عید سعید فطر",

    (12, 20):
        "تعطیل به مناسبت عید سعید فطر",

    (12, 29):
        "روز ملی شدن صنعت نفت ایران"
}


holiday = holidays.get(
    (j.month, j.day)
)


# =========================================================
# جستجوی عکس
# =========================================================

headers = {

    "Authorization":
        PEXELS_KEY
}


params = {

    "query":
        search_query,

    "orientation":
        "landscape",

    "per_page":
        10
}


photo_response = requests.get(

    "https://api.pexels.com/v1/search",

    headers=headers,

    params=params,

    timeout=20
)


photo_response.raise_for_status()


photos = photo_response.json().get(
    "photos",
    []
)


if not photos:

    raise RuntimeError(
        f"No photo found for {place_name}"
    )


photo = photos[
    g.toordinal() % len(photos)
]


image_url = photo["src"]["large2x"]


# =========================================================
# ساخت متن
# =========================================================

message = (

    f"📍 <b>{place_name}</b>\n\n"

    f"📅 <b>"
    f"{weekdays[g.weekday()]} "
    f"{j.day} "
    f"{months[j.month - 1]} "
    f"{j.year}"
    f"</b>\n"

    f"🌍 "
    f"{g.day:02d}/"
    f"{g.month:02d}/"
    f"{g.year}\n"
)


if holiday:

    message += (

        f"\n🔴 <b>تعطیل رسمی</b>\n"

        f"📌 {holiday}\n"
    )


message += (

    f"\n💡 <b>{quote}</b>\n\n"

    f"🆔 @Arvand_Aron_Steel\n"

    f"☎️ 021-22122239"
)


# =========================================================
# ارسال به کانال
# =========================================================

response = requests.post(

    f"https://api.telegram.org/bot{TOKEN}/sendPhoto",

    data={

        "chat_id":
            CHANNEL,

        "photo":
            image_url,

        "caption":
            message,

        "parse_mode":
            "HTML"

    },

    timeout=30
)


print(
    "Telegram response:"
)

print(
    response.text
)


if not response.ok:

    raise RuntimeError(
        response.text
    )


# =========================================================
# فقط بعد از ارسال موفق، روز را ثبت کن
# =========================================================

save_date(
    today_key
)


print(
    "Posted successfully."
)

print(
    "Calendar date saved:",
    today_key
)