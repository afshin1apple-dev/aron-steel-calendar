import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from zoneinfo import ZoneInfo

TOKEN = os.environ["BOT_TOKEN"]
CHANNEL = os.environ["CHANNEL_ID"]
PEXELS_KEY = os.environ["PEXELS_API_KEY"]

TEHRAN = ZoneInfo("Asia/Tehran")


def number(text):
    text = text.replace(",", "").replace("٬", "").strip()

    try:
        return float(text)
    except:
        return None


def get_tgju_price(url):
    r = requests.get(
        url,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=30
    )

    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")

    current = None
    previous = None

    for row in soup.find_all("tr"):

        text = row.get_text(" ", strip=True)

        values = []

        for cell in row.find_all(["td", "th"]):

            n = number(cell.get_text(" ", strip=True))

            if n is not None:
                values.append(n)

        if "نرخ فعلی" in text and values:
            current = values[0]

        if "نرخ روز گذشته" in text and values:
            previous = values[0]

    if current is None:
        raise RuntimeError(f"TGJU price not found: {url}")

    change = None

    if previous and previous != 0:
        change = ((current - previous) / previous) * 100

    return current, change


# --------------------------------------------------
# تتر
# --------------------------------------------------

def get_tether():

    url = "https://www.tgju.org/profile/crypto-tether/markets-local"

    r = requests.get(
        url,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=30
    )

    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")

    for row in soup.find_all("tr"):

        text = row.get_text(" ", strip=True)

        if "نوبیتکس" not in text:
            continue

        cells = row.find_all(["td", "th"])

        values = []

        for cell in cells:

            n = number(
                cell.get_text(" ", strip=True)
            )

            if n is not None:
                values.append(n)

        if not values:
            continue

        # پیدا کردن قیمت واقعی تتر
        current = None

        for value in values:

            if value > 1000000:

                current = value

                break

        if current is None:
            continue

        # پیدا کردن درصد تغییر واقعی
        change = None

        for value in values:

            if -100 <= value <= 100:

                change = value

                break

        return current, change

    raise RuntimeError(
        "Nobitex USDT/IRR price not found"
    )


# --------------------------------------------------
# بیت کوین
# --------------------------------------------------

def get_bitcoin():

    r = requests.get(
        "https://api.coingecko.com/api/v3/simple/price",
        params={
            "ids": "bitcoin",
            "vs_currencies": "usd",
            "include_24hr_change": "true"
        },
        timeout=30
    )

    r.raise_for_status()

    data = r.json()["bitcoin"]

    return (
        data["usd"],
        data["usd_24h_change"]
    )


# --------------------------------------------------
# فرمت قیمت
# --------------------------------------------------

def price(value, decimals=0):

    if value is None:
        return "نامشخص"

    return f"{value:,.{decimals}f}"


# --------------------------------------------------
# فرمت درصد
# --------------------------------------------------

def change(value):

    if value is None:
        return "⚪ نامشخص"

    if value > 0:

        return f"🟢 +{value:.2f}%"

    if value < 0:

        return f"🔴 {value:.2f}%"

    return "⚪ 0.00%"


# --------------------------------------------------
# دریافت قیمت‌ها
# --------------------------------------------------

gold_world, gold_world_change = get_tgju_price(
    "https://www.tgju.org/profile/ons"
)

gold18, gold18_change = get_tgju_price(
    "https://www.tgju.org/profile/geram18"
)

coin, coin_change = get_tgju_price(
    "https://www.tgju.org/profile/sekee"
)

tether, tether_change = get_tether()

bitcoin, bitcoin_change = get_bitcoin()


# --------------------------------------------------
# عکس مالی
# --------------------------------------------------

now = datetime.now(TEHRAN)

r = requests.get(
    "https://api.pexels.com/v1/search",

    headers={
        "Authorization": PEXELS_KEY
    },

    params={
        "query": "gold bitcoin finance trading",
        "orientation": "landscape",
        "per_page": 30
    },

    timeout=30
)

r.raise_for_status()

photos = r.json().get("photos", [])

if not photos:

    raise RuntimeError(
        "No financial photo found"
    )

photo = photos[
    now.date().toordinal() % len(photos)
]

image_url = photo["src"]["large2x"]


# --------------------------------------------------
# متن پست
# --------------------------------------------------

message = (

    "📊 <b>گزارش بازار امروز</b>\n\n"

    f"🥇 <b>طلای جهانی</b>\n"
    f"💰 {price(gold_world, 2)} دلار\n"
    f"📈 تغییر: {change(gold_world_change)}\n\n"

    f"🪙 <b>طلای ۱۸ عیار</b>\n"
    f"💰 {price(gold18)} ریال\n"
    f"📈 تغییر: {change(gold18_change)}\n\n"

    f"🪙 <b>سکه امامی</b>\n"
    f"💰 {price(coin)} ریال\n"
    f"📈 تغییر: {change(coin_change)}\n\n"

    f"₿ <b>بیت‌کوین</b>\n"
    f"💰 {price(bitcoin, 2)} دلار\n"
    f"📈 تغییر: {change(bitcoin_change)}\n\n"

    f"💵 <b>تتر</b>\n"
    f"💰 {price(tether)} ریال\n"
    f"📈 تغییر: {change(tether_change)}\n\n"

    "🆔 @Arvand_Aron_Steel\n"
    "☎️ 021-22122239"
)


# --------------------------------------------------
# ارسال به تلگرام
# --------------------------------------------------

r = requests.post(

    f"https://api.telegram.org/bot{TOKEN}/sendPhoto",

    data={
        "chat_id": CHANNEL,
        "photo": image_url,
        "caption": message,
        "parse_mode": "HTML"
    },

    timeout=30
)

print(r.text)

if not r.ok:

    raise RuntimeError(r.text)

print(
    "Market post sent successfully."
)