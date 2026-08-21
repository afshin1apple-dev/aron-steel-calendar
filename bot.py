import os
import requests
import jdatetime
from datetime import datetime
from zoneinfo import ZoneInfo

TOKEN = os.environ["BOT_TOKEN"]
CHANNEL = os.environ["CHANNEL_ID"]

now = datetime.now(ZoneInfo("Asia/Tehran"))
g = now.date()

j = jdatetime.date.fromgregorian(
    year=g.year,
    month=g.month,
    day=g.day
)

weekdays = [
    "دوشنبه",
    "سه‌شنبه",
    "چهارشنبه",
    "پنجشنبه",
    "جمعه",
    "شنبه",
    "یکشنبه"
]

months = [
    "فروردین", "اردیبهشت", "خرداد", "تیر",
    "مرداد", "شهریور", "مهر", "آبان",
    "آذر", "دی", "بهمن", "اسفند"
]

weekday = weekdays[g.weekday()]

# تعطیلات رسمی ایران در سال ۱۴۰۵
holidays = {
    (1, 1): "آغاز نوروز",
    (1, 2): "عید نوروز",
    (1, 3): "عید نوروز",
    (1, 4): "عید نوروز",
    (1, 12): "روز جمهوری اسلامی ایران",
    (1, 13): "روز طبیعت",
    
    (1, 25): "شهادت امام جعفر صادق (ع)",
    
    (3, 3): "شهادت امام محمد باقر (ع)",
    (3, 6): "عید قربان",
    (3, 14): "رحلت امام خمینی و عید غدیر خم",
    (3, 15): "قیام ۱۵ خرداد",

    (4, 3): "تاسوعای حسینی",
    (4, 4): "عاشورای حسینی",

    (5, 13): "اربعین حسینی",
    (5, 21): "رحلت پیامبر اکرم (ص) و شهادت امام حسن مجتبی (ع)",
    (5, 22): "شهادت امام رضا (ع)",
    (5, 30): "شهادت امام حسن عسکری (ع)",

    (6, 8): "ولادت پیامبر اکرم (ص) و ولادت امام جعفر صادق (ع)",

    (8, 22): "شهادت حضرت فاطمه زهرا (س)",

    (10, 2): "ولادت امام علی (ع) و روز پدر",
    (10, 16): "مبعث پیامبر اکرم (ص)",

    (11, 4): "ولادت امام زمان (عج)",
    (11, 22): "پیروزی انقلاب اسلامی ایران",

    (12, 9): "شهادت امام علی (ع)",
    (12, 19): "عید سعید فطر",
    (12, 20): "تعطیل به مناسبت عید سعید فطر",
    (12, 29): "ملی شدن صنعت نفت ایران",
}

holiday = holidays.get((j.month, j.day))

message = (
    f"📅 <b>{weekday} {j.day} {months[j.month - 1]} {j.year}</b>\n"
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

response = requests.post(
    f"https://api.telegram.org/bot{TOKEN}/sendMessage",
    json={
        "chat_id": CHANNEL,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    },
    timeout=20
)

print(response.text)

if not response.ok:
    raise RuntimeError(response.text)

print("Message sent successfully.")