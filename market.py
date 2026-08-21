import os
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from zoneinfo import ZoneInfo

TOKEN = os.environ["BOT_TOKEN"]
CHANNEL = os.environ["CHANNEL_ID"]
PEXELS_KEY = os.environ["PEXELS_API_KEY"]

TEHRAN = ZoneInfo("Asia/Tehran")
HISTORY_FILE = "market_history.json"


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
        raise RuntimeError(f"Price not found: {url}")

    if previous and previous != 0:
        change = ((current - previous) / previous) * 100
    else:
        change = None

    return current, change


def get_tether():

    url = "https://www.tgju.org/profile/crypto-tether/markets-local"

    r = requests.get(
        url,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=30
    )

    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")

    current = None

    for row in soup.find_all("tr"):

        text = row.get_text(" ", strip=True)

        if "نوبیتکس" not in text:
            continue

        values = []

        for cell in row.find_all(["td", "th"]):

            n = number(cell.get_text(" ", strip=True))

            if n is not None:
                values.append(n)

        for value in values:

            if value > 1000000:
                current = value
                break

        if current is not None:
            break

    if current is None:
        raise RuntimeError("Tether price not found")

    return current


def load_history():

    if not os.path.exists(HISTORY_FILE):
        return {}

    try:

        with open(
            HISTORY_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except:

        return {}


def save_history(history):

    with open(
        HISTORY_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            history,
            f,
            ensure_ascii=False,
            indent=2
        )


def calculate_change(current, previous):

    if previous is None or previous == 0:
        return None

    return (
        (current - previous)
        / previous
    ) * 100


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


def price(value, decimals=0):

    if value is None:
        return "نامشخص"

    return f"{value:,.{decimals}f}"


def change(value):

    if value is None:
        return "⚪ نامشخص"

    if value > 0:
        return f"🟢 +{value:.2f}%"

    if value < 0:
        return f"🔴 {value:.2f}%"

    return "⚪ 0.00%"


gold_world, gold_world_change = get_tgju_price(
    "https://www.tgju.org/profile/ons"
)

gold18, gold18_change = get_tgju_price(
    "https://www.tgju.org/profile/geram18"
)

coin, coin_change = get_tgju_price(
    "https://www.tgju.org/profile/sekee"
)

tether = get_tether()

bitcoin, bitcoin_change = get_bitcoin()


history = load_history()

previous_tether = history.get("tether")

tether_change = calculate_change(
    tether,
    previous_tether
)

history["tether"] = tether

save_history(history)


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
    raise RuntimeError("No financial photo found")

photo = photos[
    now.date().toordinal() % len(photos)
]

image_url = photo["src"]["large2x"]


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

print("Market post sent successfully.")