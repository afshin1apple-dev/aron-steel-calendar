import os
import requests
import jdatetime
from datetime import datetime
from zoneinfo import ZoneInfo

TOKEN = os.environ["BOT_TOKEN"]
CHANNEL = os.environ["CHANNEL_ID"]

# ساعت ایران
now = datetime.now(ZoneInfo("Asia/Tehran"))
g = now.date()

# تاریخ شمسی
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

weekday = weekdays[g.weekday()]

# مناسبت‌های امروز
events = []

try:
    url = f"https://holidayapi.ir/jalali/{j.year}/{j.month:02d}/{j.day:02d}"
    response = requests.get(url, timeout=20)
    data = response.json()

    for event in data.get("events", []):
        title = (
            event.get("description")
            or event.get("title")
            or event.get("name")
            or ""
        )

        if title:
            events.append(title)

except Exception as e:
    print("Calendar API error:", e)

# حذف موارد تکراری
events = list(dict.fromkeys(events))

# حذف مناسبت‌های مذهبی رایج
religious_words = [
    "شهادت",
    "ولادت",
    "عزاداری",
    "عاشورا",
    "تاسوعا",
    "اربعین",
    "محرم",
    "صفر",
    "رمضان",
    "فطر",
    "غدیر",
    "مبعث",
    "فاطمیه",
    "امام",
    "پیامبر",
    "حضرت"
]

filtered_events = []

for event in events:
    if not any(word in event for word in religious_words):
        filtered_events.append(event)

events = filtered_events

# اگر منبع مناسبت‌ها را نداد، مناسبت‌های ثابت ایرانی را بررسی کن
# ۳۰ مرداد = شهریورگان
if j.month == 5 and j.day == 30:
    if not any("شهریورگان" in e for e in events):
        events.append("جشن شهریورگان؛ از جشن‌های باستانی ایران")

if events:
    events_text = "\n".join(f"• {event}" for event in events)
else:
    events_text = "• مناسبت عمومی ثبت نشده است."

message = (
    f"📅 <b>{weekday} {j.day} {months[j.month - 1]} {j.year}</b>\n"
    f"🌍 {g.day:02d}/{g.month:02d}/{g.year}\n\n"
    f"🎉 <b>مناسبت‌های امروز:</b>\n"
    f"{events_text}\n\n"
    f"🆔 @Arvand_Aron_Steel\n"
    f"☎️ 021-22122239"
)

telegram = requests.post(
    f"https://api.telegram.org/bot{TOKEN}/sendMessage",
    json={
        "chat_id": CHANNEL,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    },
    timeout=20
)

print("Telegram response:")
print(telegram.text)

if not telegram.ok:
    raise RuntimeError(telegram.text)

print("Message sent successfully.")