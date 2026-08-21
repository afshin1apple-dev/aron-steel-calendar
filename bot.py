import os
import requests
import jdatetime
from datetime import datetime
from zoneinfo import ZoneInfo

TOKEN = os.environ["BOT_TOKEN"]
CHANNEL = os.environ["CHANNEL_ID"]

# Tehran time
now = datetime.now(ZoneInfo("Asia/Tehran"))
g = now.date()

# Gregorian -> Jalali
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

# Correct weekday
weekday = weekdays[g.weekday()]

# Get today's events
events = []

try:
    url = f"https://holidayapi.ir/jalali/{j.year}/{j.month:02d}/{j.day:02d}"
    result = requests.get(url, timeout=20)
    data = result.json()

    for event in data.get("events", []):
        description = event.get("description", "")
        is_religious = event.get("is_religious", False)

        # Only non-religious events
        if description and not is_religious:
            events.append(description)

except Exception as e:
    print("Calendar API error:", e)

# Remove duplicates
events = list(dict.fromkeys(events))

if not events:
    events_text = "• مناسبت عمومی برای امروز ثبت نشده است."
else:
    events_text = "\n".join(f"• {event}" for event in events)

message = (
    f"📅 <b>{weekday} {j.day} {months[j.month - 1]} {j.year}</b>\n"
    f"🌍 {g.day:02d}/{g.month:02d}/{g.year}\n\n"
    f"🎉 <b>مناسبت‌های امروز:</b>\n"
    f"{events_text}"
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

print("Telegram response:")
print(response.text)

if not response.ok:
    raise RuntimeError(response.text)

print("Message sent successfully.")