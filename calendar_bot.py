import os
import requests
from datetime import datetime
from zoneinfo import ZoneInfo


BOT_TOKEN = os.environ["BOT_TOKEN"]
CHANNEL_ID = os.environ["CHANNEL_ID"]

TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"


def main():

    iran_time = datetime.now(
        ZoneInfo("Asia/Tehran")
    )

    date_text = iran_time.strftime(
        "%Y/%m/%d"
    )

    weekday = iran_time.strftime(
        "%A"
    )

    weekdays = {
        "Saturday": "شنبه",
        "Sunday": "یکشنبه",
        "Monday": "دوشنبه",
        "Tuesday": "سه‌شنبه",
        "Wednesday": "چهارشنبه",
        "Thursday": "پنجشنبه",
        "Friday": "جمعه"
    }

    weekday_fa = weekdays.get(
        weekday,
        weekday
    )

    message = f"""
📅 <b>تقویم روز</b>

🗓 <b>{weekday_fa}</b>
📆 {date_text}

━━━━━━━━━━━━━━
🏭 آروند آرون استیل
👤 مدیریت: افشین آورزمانی
📞 021-22122239
🆔 @arvand_aron_steel
"""

    response = requests.post(
        TELEGRAM_URL,
        data={
            "chat_id": CHANNEL_ID,
            "text": message,
            "parse_mode": "HTML"
        },
        timeout=30
    )

    print(response.status_code)
    print(response.text)


if __name__ == "__main__":
    main()