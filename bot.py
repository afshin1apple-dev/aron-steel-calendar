import os
import requests
import jdatetime
from datetime import datetime
from zoneinfo import ZoneInfo

TOKEN = os.environ["BOT_TOKEN"]
CHANNEL = os.environ["CHANNEL_ID"]

TEHRAN = ZoneInfo("Asia/Tehran")
now = datetime.now(TEHRAN)
g = now.date()
j = jdatetime.date.fromgregorian(date=g)

weekdays = {
    0: "دوشنبه",
    1: "سه‌شنبه",
    2: "چهارشنبه",
    3: "پنجشنبه",
    4: "جمعه",
    5: "شنبه",
    6: "یکشنبه"
}

months = [
    "فروردین", "اردیبهشت", "خرداد", "تیر",
    "مرداد", "شهریور", "مهر", "آبان",
    "آذر", "دی", "بهمن", "اسفند"
]

msg = (
    f"📅 <b>{weekdays[j.weekday()]} "
    f"{j.day} {months[j.month-1]} {j.year}</b>\n"
    f"🌍 {g.day:02d}/{g.month:02d}/{g.year}\n\n"
    f"🎉 <b>مناسبت‌های امروز:</b>\n"
    f"• در حال آماده‌سازی تقویم مناسبت‌ها..."
)

response = requests.post(
    f"https://api.telegram.org/bot{TOKEN}/sendMessage",
    json={
        "chat_id": CHANNEL,
        "text": msg,
        "parse_mode": "HTML"
    },
    timeout=20
)

response.raise_for_status()
print("Posted successfully.")