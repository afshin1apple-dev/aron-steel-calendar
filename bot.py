import os
import requests
import jdatetime
from datetime import datetime
from zoneinfo import ZoneInfo

TOKEN = os.environ["BOT_TOKEN"]
CHANNEL = os.environ["CHANNEL_ID"]
PEXELS_KEY = os.environ["PEXELS_API_KEY"]

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

# مکان‌های منتخب ایران
places = [
    ("ماسال", "Masal Iran"),
    ("رامسر", "Ramsar Iran"),
    ("جنگل‌های دوهزار", "Dohezar Forest Iran"),
    ("فیلبند", "Filband Iran"),
    ("اورامانات", "Hawraman Iran"),
    ("دریاچه گهر", "Gahar Lake Iran"),
    ("کویر مرنجاب", "Maranjab Desert Iran"),
    ("کویر لوت", "Lut Desert Iran"),
    ("ابیانه", "Abyaneh Iran"),
    ("کاشان", "Kashan Iran"),
    ("اصفهان", "Isfahan Iran"),
    ("شیراز", "Shiraz Iran"),
    ("یزد", "Yazd Iran"),
    ("قشم", "Qeshm Iran"),
    ("جزیره هرمز", "Hormuz Island Iran"),
    ("چابهار", "Chabahar Iran"),
]

# هر روز یک مکان متفاوت
index = g.toordinal() % len(places)
place_name, search_query = places[index]

# جست‌وجوی عکس در Pexels
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

# انتخاب عکس بر اساس تاریخ
photo = photos[g.toordinal() % len(photos)]

image_url = photo["src"]["large2x"]

# تعطیلات رسمی
holidays = {
    (1, 1): "آغاز نوروز",
    (1, 2): "عید نوروز",
    (1, 3): "عید نوروز",
    (1, 4): "عید نوروز",
    (1, 12): "روز جمهوری اسلامی ایران",
    (1, 13): "روز طبیعت",
    (2, 14): "رحلت امام خمینی",
    (2, 15): "قیام ۱۵ خرداد",
    (11, 22): "پیروزی انقلاب اسلامی ایران",
    (12, 29): "ملی شدن صنعت نفت ایران",
}

holiday = holidays.get((j.month, j.day))

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
    f"\n🆔 @Arvand_Aron_Steel\n"
    f"☎️ 021-22122239"
)

# ارسال عکس + کپشن به تلگرام
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

print("Photo and calendar sent successfully.")