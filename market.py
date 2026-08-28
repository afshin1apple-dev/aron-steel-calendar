import os
import json
import requests

from bs4 import BeautifulSoup
from datetime import datetime
from zoneinfo import ZoneInfo


# =========================================================
# SETTINGS
# =========================================================

TOKEN = os.environ["BOT_TOKEN"]
CHANNEL = os.environ["CHANNEL_ID"]
PEXELS_KEY = os.environ["PEXELS_API_KEY"]

TEHRAN = ZoneInfo("Asia/Tehran")

HISTORY_FILE = "market_history.json"

CHANGE_THRESHOLD = 5.0


# =========================================================
# CHANNEL FOOTER
# =========================================================

COMPANY_FOOTER = """
━━━━━━━━━━━━━━
🏭 آروند آرون استیل
👤 مدیریت: افشین آورزمانی
📞 021-22122239
🆔 @arvand_aron_steel
"""


# =========================================================
# NUMBER
# =========================================================

def number(text):

    text = (
        text
        .replace(",", "")
        .replace("٬", "")
        .strip()
    )

    try:
        return float(text)

    except:
        return None


# =========================================================
# TGJU PRICE
# =========================================================

def get_tgju_price(url):

    r = requests.get(
        url,
        headers={
            "User-Agent": "Mozilla/5.0"
        },
        timeout=30
    )

    print("TGJU URL:", url)
    print("TGJU HTTP:", r.status_code)

    r.raise_for_status()

    soup = BeautifulSoup(
        r.text,
        "html.parser"
    )

    current = None
    previous = None

    for row in soup.find_all("tr"):

        text = row.get_text(
            " ",
            strip=True
        )

        values = []

        for cell in row.find_all(
            ["td", "th"]
        ):

            n = number(
                cell.get_text(
                    " ",
                    strip=True
                )
            )

            if n is not None:
                values.append(n)

        if (
            "نرخ فعلی" in text
            and values
        ):

            current = values[0]

        if (
            "نرخ روز گذشته" in text
            and values
        ):

            previous = values[0]

    if current is None:

        raise RuntimeError(
            f"Price not found: {url}"
        )

    if (
        previous is not None
        and previous != 0
    ):

        change_value = (
            (current - previous)
            / previous
        ) * 100

    else:

        change_value = None

    return current, change_value


# =========================================================
# TETHER
# =========================================================

def get_tether():

    url = (
        "https://www.tgju.org/"
        "profile/crypto-tether/"
        "markets-local"
    )

    r = requests.get(
        url,
        headers={
            "User-Agent": "Mozilla/5.0"
        },
        timeout=30
    )

    print("Tether HTTP:", r.status_code)

    r.raise_for_status()

    soup = BeautifulSoup(
        r.text,
        "html.parser"
    )

    current = None

    for row in soup.find_all("tr"):

        text = row.get_text(
            " ",
            strip=True
        )

        if "نوبیتکس" not in text:
            continue

        values = []

        for cell in row.find_all(
            ["td", "th"]
        ):

            n = number(
                cell.get_text(
                    " ",
                    strip=True
                )
            )

            if n is not None:
                values.append(n)

        for value in values:

            if value > 1000000:

                current = value

                break

        if current is not None:
            break

    if current is None:

        raise RuntimeError(
            "Tether price not found"
        )

    return current


# =========================================================
# BITCOIN
# =========================================================

def get_bitcoin():

    r = requests.get(

        "https://api.coingecko.com/"
        "api/v3/simple/price",

        params={

            "ids":
                "bitcoin",

            "vs_currencies":
                "usd",

            "include_24hr_change":
                "true"
        },

        timeout=30
    )

    print(
        "CoinGecko HTTP:",
        r.status_code
    )

    r.raise_for_status()

    data = r.json()["bitcoin"]

    return (
        data["usd"],
        data["usd_24h_change"]
    )


# =========================================================
# HISTORY
# =========================================================

def load_history():

    if not os.path.exists(
        HISTORY_FILE
    ):
        return {}

    try:

        with open(
            HISTORY_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

            if isinstance(data, dict):
                return data

            return {}

    except Exception as e:

        print(
            "History load error:",
            e
        )

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


# =========================================================
# CHANGE
# =========================================================

def calculate_change(
    current,
    previous
):

    if (
        previous is None
        or previous == 0
        or current is None
    ):

        return None

    return (
        (current - previous)
        / previous
    ) * 100


# =========================================================
# FORMAT PRICE
# =========================================================

def price(
    value,
    decimals=0
):

    if value is None:
        return "نامشخص"

    return (
        f"{value:,.{decimals}f}"
    )


# =========================================================
# FORMAT CHANGE
# =========================================================

def change(value):

    if value is None:
        return "⚪ نامشخص"

    if value > 0:

        return (
            f"🟢 +{value:.2f}%"
        )

    if value < 0:

        return (
            f"🔴 {value:.2f}%"
        )

    return "⚪ 0.00%"


# =========================================================
# COMPARE
# =========================================================

def compare_prices(
    current_prices,
    previous_prices
):

    changes = {}

    if not previous_prices:
        return changes

    for name, current in current_prices.items():

        previous = previous_prices.get(
            name
        )

        if (
            previous is None
            or previous == 0
            or current is None
        ):
            continue

        changes[name] = (
            (current - previous)
            / previous
        ) * 100

    return changes


# =========================================================
# SIGNIFICANT CHANGE
# =========================================================

def has_significant_change(
    changes
):

    for name, value in changes.items():

        if abs(value) > CHANGE_THRESHOLD:

            print(
                f"PRICE CHANGE > 5%: "
                f"{name} = {value:+.2f}%"
            )

            return True

    return False


# =========================================================
# TIME
# =========================================================

now = datetime.now(
    TEHRAN
)

today_key = now.strftime(
    "%Y-%m-%d"
)

print(
    "======================================"
)

print(
    "DAILY MARKET"
)

print(
    "Iran time:",
    now.strftime(
        "%Y-%m-%d %H:%M:%S"
    )
)

print(
    "======================================"
)


# =========================================================
# HISTORY
# =========================================================

history = load_history()

last_post_date = history.get(
    "last_market_post_date"
)

last_post_prices = history.get(
    "last_market_post_prices"
)


# =========================================================
# GET PRICES
# =========================================================

print("Getting gold world...")

gold_world, gold_world_change = (
    get_tgju_price(
        "https://www.tgju.org/profile/ons"
    )
)


print("Getting gold 18...")

gold18, gold18_change = (
    get_tgju_price(
        "https://www.tgju.org/profile/geram18"
    )
)


print("Getting coin...")

coin, coin_change = (
    get_tgju_price(
        "https://www.tgju.org/profile/sekee"
    )
)


print("Getting tether...")

tether = get_tether()


# =========================================================
# TETHER CHANGE
# =========================================================

tether_previous = None

if last_post_prices:

    tether_previous = last_post_prices.get(
        "tether"
    )

tether_change = calculate_change(
    tether,
    tether_previous
)


print(
    "Tether current:",
    tether
)

print(
    "Tether previous:",
    tether_previous
)

print(
    "Tether change:",
    tether_change
)


print("Getting bitcoin...")

bitcoin, bitcoin_change = (
    get_bitcoin()
)


# =========================================================
# CURRENT PRICES
# =========================================================

current_prices = {

    "gold_world":
        gold_world,

    "gold18":
        gold18,

    "coin":
        coin,

    "bitcoin":
        bitcoin,

    "tether":
        tether
}


print(
    "======================================"
)

print(
    "Current market prices:"
)

for name, value in current_prices.items():

    print(
        f"{name}: {value}"
    )

print(
    "======================================"
)


# =========================================================
# DECIDE POST
# =========================================================

should_post = False


if last_post_date != today_key:

    print(
        "First market post of today."
    )

    should_post = True


else:

    print(
        "Market post already sent today."
    )

    if not last_post_prices:

        print(
            "No previous market prices."
        )

        should_post = True

    else:

        price_changes = compare_prices(
            current_prices,
            last_post_prices
        )

        for name, value in price_changes.items():

            print(
                f"{name}: {value:+.2f}%"
            )

        if has_significant_change(
            price_changes
        ):

            print(
                "Movement above 5% detected."
            )

            should_post = True

        else:

            print(
                "No movement above 5%."
            )

            should_post = False


# =========================================================
# NO POST
# =========================================================

if not should_post:

    print(
        "======================================"
    )

    print(
        "MARKET POST SKIPPED"
    )

    print(
        "======================================"
    )

    raise SystemExit(0)


# =========================================================
# PEXELS
# =========================================================

print(
    "Getting market image..."
)

r = requests.get(

    "https://api.pexels.com/v1/search",

    headers={
        "Authorization":
            PEXELS_KEY
    },

    params={

        "query":
            "gold bitcoin finance trading",

        "orientation":
            "landscape",

        "per_page":
            30
    },

    timeout=30
)

r.raise_for_status()

photos = r.json().get(
    "photos",
    []
)


if not photos:

    raise RuntimeError(
        "No market image found"
    )


photo = photos[
    now.date().toordinal()
    % len(photos)
]


image_url = photo[
    "src"
]["large2x"]


# =========================================================
# MESSAGE
# =========================================================

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

    f"{COMPANY_FOOTER}"
)


# =========================================================
# SEND TELEGRAM
# =========================================================

print(
    "Sending market post..."
)

r = requests.post(

    f"https://api.telegram.org/"
    f"bot{TOKEN}/sendPhoto",

    data={

        "chat_id":
            CHANNEL,

        "photo":
            image_url,

        "caption":
            message,

        "parse_mode":
            "HTML"
    },

    timeout=30
)


print(
    "Telegram response:"
)

print(
    r.text
)


if not r.ok:

    raise RuntimeError(
        r.text
    )


# =========================================================
# SAVE HISTORY
# =========================================================

history[
    "last_market_post_date"
] = today_key

history[
    "last_market_post_time"
] = now.strftime(
    "%Y-%m-%d %H:%M:%S"
)

history[
    "last_market_post_prices"
] = current_prices

history[
    "market_tether"
] = tether


save_history(
    history
)


print(
    "======================================"
)

print(
    "MARKET POST SENT SUCCESSFULLY"
)

print(
    "======================================"
)