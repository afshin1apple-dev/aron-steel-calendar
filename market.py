import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from zoneinfo import ZoneInfo

TOKEN = os.environ["BOT_TOKEN"]
CHANNEL = os.environ["CHANNEL_ID"]
PEXELS_KEY = os.environ["PEXELS_API_KEY"]

TEHRAN = ZoneInfo("Asia/Tehran")


def get_tgju(url):
    response = requests.get(
        url,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=30
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # پیدا کردن قیمت فعلی
    current = None
    previous = None

    # جدول اطلاعات صفحه
    rows = soup.find_all("tr")

    for row in rows:
        text = row.get_text(" ", strip=True)

        if "نرخ فعلی" in text or "قیمت" in text:
            cells = row.find_all(["td", "th"])

            numbers = []

            for cell in cells:
                value = cell.get_text(" ", strip=True)
                value = value.replace(",", "").replace("٬", "")

                try:
                    numbers.append(float(value))
                except:
                    pass

            if numbers:
                current = numbers[0]

        if "نرخ روز گذشته" in text:
            cells = row.find_all(["td", "th"])

            numbers = []

            for cell in cells:
                value = cell.get_text(" ", strip=True)
                value = value.replace(",", "").replace("٬", "")

                try:
                    numbers.append(float(value))
                except:
                    pass

            if numbers:
                previous = numbers[0]

    if current is None:
        raise RuntimeError(f"Could not find price: {url}")

    if previous is not None and previous != 0:
        change = ((current - previous) / previous) * 100
    else:
        change = None

    return current, change


def get_bitcoin():
    url = "https://api.coingecko.com/api/v3/simple/price"

    params = {
        "ids": "bitcoin",
        "vs_currencies": "usd",
        "include_24hr_change": "true"
    }

    response = requests.get(
        url,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()["bitcoin"]

    return data["usd"], data.get("usd_24h_change")


def format_price(value, decimals=0):
    if value is None:
        return "نامشخص"

    return f"{value:,.{decimals}f}"


def format_change(change):
    if change is None:
        return "⚪ اطلاعات تغییر موجود نیست"

    if change > 0:
        return f"🟢 +{change:.2f}%"

    if change < 0:
        return f"🔴 {change:.2f}%"

    return "⚪ 0.00%"


# -------------------------
# قیمت‌ها
# -------------------------

gold_world, gold_world_change = get_tgju(
    "https://www.tgju.org/profile/ons"
)

gold18, gold18_change = get_tgju(
    "https://www.tgju.org/profile/geram18"
)

coin, coin_change = get_tgju(
    "https://www.tgju.org/profile/sekee"
)

tether, tether_change = get_tgju(
    "https://www.tgju.org/profile/crypto-tether"
)

bitcoin, bitcoin_change = get_bitcoin()


# -------------------------
# عکس مالی
# -------------------------

now = datetime.now(TEHRAN)

photo_response = requests.get(
    "https://api.pexels.com/v1/search",
    headers={
        "Authorization": PEXELS_KEY
    },
    params={
        "query": "gold bitcoin finance trading stock market",
        "orientation": "landscape",
        "per_page": 30
    },
    timeout=30
)

photo_response.raise_for_status()

photos = photo_response.json().get("photos", [])

if not photos:
    raise RuntimeError("No financial photo found")

photo = photos[now.date().toordinal() % len(photos)]

image_url = photo["src"]["large2x"]


# -------------------------
# کپشن
# -------------------------

message = (
    "📊 <b>گزارش بازار امروز</b>\n\n"

    f"🥇 <b>طلای جهانی</b>\n"
    f"💰 {format_price(gold_world, 2)} دلار\n"
    f"📈 تغییر: {format_change(gold_world_change)}\n\n"

    f"🪙 <b>طلای ۱۸ عیار</b>\n"
    f"💰 {format_price(gold18)} ریال\n"
    f"📈 تغییر: {format_change(gold18_change)}\n\n"

    f"🪙 <b>سکه امامی</b>\n"
    f"💰 {format_price(coin)} ریال\n"
    f"📈 تغییر: {format_change(coin_change)}\n\n"

    f"₿ <b>بیت‌کوین</b>\n"
    f"💰 {format_price(bitcoin, 2)} دلار\n"
    f"📈 تغییر: {format_change(bitcoin_change)}\n\n"

    f"💵 <b>تتر</b>\n"
    f"💰 {format_price(tether)} ریال\n"
    f"📈 تغییر: {format_change(tether_change)}\n\n"

    "🆔 @Arvand_Aron_Steel\n"
    "☎️ 021-22122239"
)


# -------------------------
# ارسال تلگرام
# -------------------------

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

print(response.text)

if not response.ok:
    raise RuntimeError(response.text)

print("Market post sent successfully.")