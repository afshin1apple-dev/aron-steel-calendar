import os
import re
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

TOKEN = os.environ["BOT_TOKEN"]
CHANNEL = os.environ["CHANNEL_ID"]
PEXELS_KEY = os.environ["PEXELS_API_KEY"]

TGJU_URL = "https://www.tgju.org/"
TEHRAN = ZoneInfo("Asia/Tehran")


def clean_number(text):
    text = text.replace(",", "").replace("٬", "").replace("٫", ".")
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    return float(match.group()) if match else None


def get_tgju_prices():
    response = requests.get(TGJU_URL, timeout=30)
    response.raise_for_status()
    html = response.text

    prices = {}

    patterns = {
        "gold_world": r"انس طلا.*?([\d,]+\.\d+)",
        "gold18": r"طلا ۱۸.*?([\d,]+)",
        "coin": r"سکه امامی.*?([\d,]+)",
        "tether": r"تتر.*?([\d,]+)",
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, html, re.S)
        if match:
            prices[key] = clean_number(match.group(1))

    return prices


def get_bitcoin():
    url = "https://api.coingecko.com/api/v3/simple/price"

    params = {
        "ids": "bitcoin",
        "vs_currencies": "usd",
        "include_24hr_change": "true"
    }

    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()

    data = response.json()["bitcoin"]

    return data["usd"], data.get("usd_24h_change", 0)


def format_price(value):
    if value is None:
        return "نامشخص"

    if value >= 100:
        return f"{value:,.0f}"

    return f"{value:,.2f}"


def change_text(change):
    if change is None:
        return "⚪ نامشخص"

    if change > 0:
        return f"🟢 +{change:.2f}%"

    if change < 0:
        return f"🔴 {change:.2f}%"

    return "⚪ 0.00%"


# دریافت قیمت‌های بازار ایران
prices = get_tgju_prices()

# بیت‌کوین
bitcoin_price, bitcoin_change = get_bitcoin()

# تاریخ ایران
now = datetime.now(TEHRAN)

# عکس مرتبط با بازار مالی
photo_response = requests.get(
    "https://api.pexels.com/v1/search",
    headers={"Authorization": PEXELS_KEY},
    params={
        "query": "gold bitcoin financial market trading",
        "orientation": "landscape",
        "per_page": 20
    },
    timeout=30
)

photo_response.raise_for_status()

photos = photo_response.json().get("photos", [])

if not photos:
    raise RuntimeError("No financial photo found.")

# هر روز یک عکس متفاوت
photo = photos[now.date().toordinal() % len(photos)]
image_url = photo["src"]["large2x"]


message = (
    "📊 <b>گزارش بازار امروز</b>\n\n"

    f"🥇 <b>طلای جهانی</b>\n"
    f"💰 {format_price(prices.get('gold_world'))} دلار\n"
    f"📈 تغییر: {change_text(None)}\n\n"

    f"🪙 <b>طلای ۱۸ عیار</b>\n"
    f"💰 {format_price(prices.get('gold18'))} ریال\n"
    f"📈 تغییر: {change_text(None)}\n\n"

    f"🪙 <b>سکه امامی</b>\n"
    f"💰 {format_price(prices.get('coin'))} ریال\n"
    f"📈 تغییر: {change_text(None)}\n\n"

    f"₿ <b>بیت‌کوین</b>\n"
    f"💰 {format_price(bitcoin_price)} دلار\n"
    f"📈 تغییر: {change_text(bitcoin_change)}\n\n"

    f"💵 <b>تتر</b>\n"
    f"💰 {format_price(prices.get('tether'))} ریال\n"
    f"📈 تغییر: {change_text(None)}\n\n"

    f"🆔 @Arvand_Aron_Steel\n"
    f"☎️ 021-22122239"
)


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

print("Market post sent successfully.")