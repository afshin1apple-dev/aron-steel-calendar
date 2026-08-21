import os
import requests
import jdatetime
from datetime import datetime
from zoneinfo import ZoneInfo

TOKEN = os.environ["BOT_TOKEN"]
CHANNEL = os.environ["CHANNEL_ID"]
PEXELS_KEY = os.environ["PEXELS_API_KEY"]

# ساعت ایران
now = datetime.now(ZoneInfo("Asia/Tehran"))
g = now.date()

j = jdatetime.date.fromgregorian(
    year=g.year,
    month=g.month,
    day=g.day
)

weekdays = [
    "دوشنبه", "سه‌شنبه", "چهارشنبه",
    "پنجشنبه", "جمعه", "شنبه", "یکشنبه"
]

months = [
    "فروردین", "اردیبهشت", "خرداد", "تیر",
    "مرداد", "شهریور", "مهر", "آبان",
    "آذر", "دی", "بهمن", "اسفند"
]

# مکان‌های ایران
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
    ("چابهار", "Chabahar Iran"),
]

index = g.toordinal() % len(places)
place_name, search_query = places[index]

# جمله‌های انگیزشی
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

quote = quotes[g.toordinal() % len(quotes)]

# تعطیلات رسمی ایران در سال ۱۴۰۵
holidays = {
    # فروردین
    (1, 1): "نوروز و عید فطر",
    (1, 2): "نوروز و عید فطر",
    (1, 3): "نوروز",
    (1, 4): "نوروز",
    (1, 12): "روز جمهوری اسلامی ایران",
    (1, 13): "روز طبیعت",
    (1, 24): "شهادت امام جعفر صادق (ع)",

    # خرداد
    (3, 6): "عید سعید قربان",
    (3, 14): "رحلت امام خمینی (ره) و عید غدیر خم",
    (3, 15): "قیام ۱۵ خرداد",

    # تیر
    (4, 3): "تاسوعای حسینی",
    (4, 4): "عاشورای حسینی",

    # مرداد
    (5, 13): "اربعین حسینی",
    (5, 21): "رحلت پیامبر اکرم (ص) و شهادت امام حسن مجتبی (ع)",
    (5, 22): "شهادت امام رضا (ع)",
    (5, 30): "شهادت امام حسن عسکری (ع)",

    # شهریور
    (6, 8): "ولادت پیامبر اکرم (ص) و ولادت امام جعفر صادق (ع)",

    # آبان
    (8, 22): "شهادت حضرت فاطمه زهرا (س)",

    # دی
    (10, 2): "ولادت امام علی (ع) و روز پدر",
    (10, 16): "مبعث پیامبر اکرم (ص)",

    # بهمن
    (11, 4): "ولادت حضرت قائم (عج)",
    (11, 22): "پیروزی انقلاب اسلامی ایران",

    # اسفند
    (12, 9): "شهادت حضرت علی (ع)",
    (12, 19): "عید سعید فطر",
    (12, 20): "تعطیل به مناسبت عید سعید فطر",
    (12, 29): "روز ملی شدن صنعت نفت ایران"
}

holiday = holidays.get((j.month, j.day))

# جست‌وجوی عکس
headers = {
    "Authorization": PEXELS_KEY
}

params = {
    "query": search_query,
    "orientation": "landscape",
    "per_page": 10
}

photo_response = requests.get(
    "https://api.pexels.com/v1/search",
    headers=headers,
    params=params,
    timeout=20
)

photo_response.raise_for_status()

photos = photo_response.json().get("photos", [])

if not photos:
    raise RuntimeError(f"No photo found for {place_name}")

photo = photos[g.toordinal() % len(photos)]
image_url = photo["src"]["large2x"]

# ساخت متن
message = (
    f"📍 <b>{place_name}</b>\n\n"
    f"📅 <b>{weekdays[g.weekday()]} "
    f"{j.day} {months[j.month - 1]} {j.year}</b>\n"
    f"🌍 {g.day:02d}/{g.month:02d}/{g.year}\n"
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

# ارسال به کانال
response = requests.post(
    f"https://api.telegram.org/bot{TOKEN}/sendPhoto",
    data={
        "chat_id": CHANNEL,
        "photo": image_url,
        "caption": message,
        "parse_mode": "HTML"
    },
    timeout=30
)

print("Telegram response:")
print(response.text)

if not response.ok:
    raise RuntimeError(response.text)

print("Posted successfully.")