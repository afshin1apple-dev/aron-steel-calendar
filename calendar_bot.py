import os
import random
import requests
from datetime import datetime
from zoneinfo import ZoneInfo


# =========================================================
# تنظیمات
# =========================================================

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHANNEL_ID = os.environ["CHANNEL_ID"]
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")

TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"


# =========================================================
# تبدیل تاریخ میلادی به شمسی
# =========================================================

def gregorian_to_jalali(gy, gm, gd):

    g_days_in_month = [
        31, 28, 31, 30, 31, 30,
        31, 31, 30, 31, 30, 31
    ]

    j_days_in_month = [
        31, 31, 31, 31, 31, 31,
        30, 30, 30, 30, 30, 29
    ]

    gy2 = gy - 1600
    gm2 = gm - 1
    gd2 = gd - 1

    g_day_no = (
        365 * gy2
        + (gy2 + 3) // 4
        - (gy2 + 99) // 100
        + (gy2 + 399) // 400
    )

    for i in range(gm2):
        g_day_no += g_days_in_month[i]

    if gm2 > 1 and (
        gy % 4 == 0
        and (gy % 100 != 0 or gy % 400 == 0)
    ):
        g_day_no += 1

    g_day_no += gd2

    j_day_no = g_day_no - 79

    j_np = j_day_no // 12053
    j_day_no %= 12053

    jy = 979 + 33 * j_np + 4 * (j_day_no // 1461)

    j_day_no %= 1461

    if j_day_no >= 366:
        jy += (j_day_no - 1) // 365
        j_day_no = (j_day_no - 1) % 365

    i = 0

    while (
        i < 11
        and j_day_no >= j_days_in_month[i]
    ):
        j_day_no -= j_days_in_month[i]
        i += 1

    jm = i + 1
    jd = j_day_no + 1

    return jy, jm, jd


# =========================================================
# جملات انگیزشی
# =========================================================

MOTIVATIONAL_QUOTES = [

    "هر روز یک فرصت تازه برای بهتر شدن است. 🌱",

    "آرام قدم بردار، اما هیچ‌وقت متوقف نشو. 💪",

    "موفقیت نتیجه قدم‌های کوچک اما مداوم است. 🚀",

    "به خودت اعتماد کن؛ مسیرهای بزرگ از قدم‌های کوچک شروع می‌شوند. ✨",

    "امروز را بساز؛ فردا نتیجه انتخاب‌های امروز توست. 🌟",

    "سختی‌ها موقتی‌اند، اما قدرتی که از آن‌ها می‌سازی ماندگار است. 💙",

    "گاهی فقط باید ادامه بدهی؛ حتی وقتی مسیر سخت است. 🏆",

    "هر صبح یعنی یک شروع دوباره. از امروزت بهترین استفاده را ببر. ☀️",

    "هیچ تلاشی که با امید و پشتکار انجام شود، بی‌نتیجه نمی‌ماند. 💪",

    "قدم بعدی را بردار؛ لازم نیست تمام مسیر را از همین حالا ببینی. 🌱"
]


# =========================================================
# نام روزهای هفته
# =========================================================

WEEKDAYS = {

    "Saturday": "شنبه",
    "Sunday": "یکشنبه",
    "Monday": "دوشنبه",
    "Tuesday": "سه‌شنبه",
    "Wednesday": "چهارشنبه",
    "Thursday": "پنجشنبه",
    "Friday": "جمعه"

}


# =========================================================
# دریافت عکس از Pexels
# =========================================================

def get_image():

    if not PEXELS_API_KEY:
        print("PEXELS_API_KEY not found")
        return None

    try:

        headers = {
            "Authorization": PEXELS_API_KEY
        }

        response = requests.get(

            "https://api.pexels.com/v1/search",

            headers=headers,

            params={
                "query": "business success motivation",
                "per_page": 20,
                "orientation": "landscape"
            },

            timeout=30
        )

        if response.status_code != 200:

            print(
                "Pexels error:",
                response.status_code
            )

            return None

        photos = response.json().get(
            "photos",
            []
        )

        if not photos:
            return None

        photo = random.choice(photos)

        return photo.get(
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
# ارسال پیام همراه عکس
# =========================================================

def send_calendar(
    image_url,
    message
):

    try:

        if image_url:

            response = requests.post(

                f"{TELEGRAM_URL}/sendPhoto",

                data={

                    "chat_id":
                        CHANNEL_ID,

                    "photo":
                        image_url,

                    "caption":
                        message,

                    "parse_mode":
                        "HTML"

                },

                timeout=40
            )

        else:

            response = requests.post(

                f"{TELEGRAM_URL}/sendMessage",

                data={

                    "chat_id":
                        CHANNEL_ID,

                    "text":
                        message,

                    "parse_mode":
                        "HTML"

                },

                timeout=30
            )

        print(
            "Telegram:",
            response.status_code
        )

        print(
            response.text
        )

        return response.ok

    except Exception as e:

        print(
            "Telegram error:",
            e
        )

        return False


# =========================================================
# اجرای اصلی
# =========================================================

def main():

    print(
        "======================================"
    )

    print(
        "Starting Daily Calendar"
    )

    print(
        "======================================"
    )


    iran_time = datetime.now(
        ZoneInfo("Asia/Tehran")
    )


    # تاریخ شمسی

    jy, jm, jd = gregorian_to_jalali(

        iran_time.year,
        iran_time.month,
        iran_time.day

    )


    jalali_date = (
        f"{jy:04d}/{jm:02d}/{jd:02d}"
    )


    # روز هفته

    weekday = iran_time.strftime(
        "%A"
    )

    weekday_fa = WEEKDAYS.get(
        weekday,
        weekday
    )


    # جمله انگیزشی

    quote = random.choice(
        MOTIVATIONAL_QUOTES
    )


    # متن پست

    message = f"""

📅 <b>تقویم روز</b>

🗓 <b>{weekday_fa}</b>
📆 <b>{jalali_date}</b>

💬 <b>جمله امروز:</b>

«{quote}»

━━━━━━━━━━━━━━
🏭 آروند آرون استیل
👤 مدیریت: افشین آورزمانی
📞 021-22122239
🆔 @arvand_aron_steel

""".strip()


    print(
        "Iran date:",
        jalali_date
    )

    print(
        "Weekday:",
        weekday_fa
    )

    print(
        "Getting image..."
    )


    image_url = get_image()


    if image_url:

        print(
            "Image found."
        )

    else:

        print(
            "No image found. Sending text."
        )


    send_calendar(
        image_url,
        message
    )


    print(
        "======================================"
    )

    print(
        "Calendar job finished"
    )

    print(
        "======================================"
    )


if __name__ == "__main__":

    main()