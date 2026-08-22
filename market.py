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
            "User-Agent":
                "Mozilla/5.0"
        },
        timeout=30
    )

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
            "User-Agent":
                "Mozilla/5.0"
        },
        timeout=30
    )

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
    ):

        return None

    return (
        (current - previous)
        / previous
    ) * 100


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

    r.raise_for_status()

    data = r.json()["bitcoin"]

    return (

        data["usd"],

        data["usd_24h_change"]
    )


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
# TIME
# =========================================================

now = datetime.now(
    TEHRAN
)

today_key = now.strftime(
    "%Y-%m-%d"
)

print(
    "Iran time:",
    now.strftime(
        "%Y-%m-%d %H:%M:%S"
    )
)


# =========================================================
# LOAD HISTORY
# =========================================================

history = load_history()


# =========================================================
# IMPORTANT:
# اگر بازار امروز قبلاً ارسال شده،
# اجرای پشتیبان هیچ پستی نمی‌فرستد.
# =========================================================

if history.get(
    "last_post_date"
) == today_key:

    print(
        "Today's market post has already been sent."
    )

    print(
        "Nothing to do."
    )

    raise SystemExit(0)


# =========================================================
# GET PRICES
# =========================================================

print(
    "Getting gold world..."
)

gold_world, gold_world_change = (
    get_tgju_price(
        "https://www.tgju.org/profile/ons"
    )
)


print(
    "Getting gold 18..."
)

gold18, gold18_change = (
    get_tgju_price(
        "https://www.tgju.org/profile/geram18"
    )
)


print(
    "Getting coin..."
)

coin, coin_change = (
    get_tgju_price(
        "https://www.tgju.org/profile/sekee"
    )
)


print(
    "Getting tether..."
)

tether = get_tether()


# =========================================================
# TETHER CHANGE
# =========================================================

previous_tether = history.get(
    "tether"
)

tether_change = calculate_change(
    tether,
    previous_tether
)


# =========================================================
# BITCOIN
# =========================================================

print(
    "Getting bitcoin..."
)

bitcoin, bitcoin_change = (
    get_bitcoin()
)


# =========================================================
# UPDATE HISTORY
# =========================================================

history["tether"] = tether


# =========================================================
# PEXELS IMAGE
# =========================================================

print(
    "Getting image..."
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
        "No financial photo found"
    )


photo = photos[
    now.date().toordinal()
    % len(photos)
]


image_url = photo[
    "src"
][
    "large2x"
]


# =========================================================
# MESSAGE
# =========================================================

message = (

    "📊 <b>گزارش بازار امروز</b>\n\n"

    f"🥇 <b>طلای جهانی</b>\n"
    f"💰 {price(gold_world, 2)} دلار\n"
    f"📈 تغییر: "
    f"{change(gold_world_change)}\n\n"

    f"🪙 <b>طلای ۱۸ عیار</b>\n"
    f"💰 {price(gold18)} ریال\n"
    f"📈 تغییر: "
    f"{change(gold18_change)}\n\n"

    f"🪙 <b>سکه امامی</b>\n"
    f"💰 {price(coin)} ریال\n"
    f"📈 تغییر: "
    f"{change(coin_change)}\n\n"

    f"₿ <b>بیت‌کوین</b>\n"
    f"💰 {price(bitcoin, 2)} دلار\n"
    f"📈 تغییر: "
    f"{change(bitcoin_change)}\n\n"

    f"💵 <b>تتر</b>\n"
    f"💰 {price(tether)} ریال\n"
    f"📈 تغییر: "
    f"{change(tether_change)}\n\n"

    "🆔 @Arvand_Aron_Steel\n"
    "☎️ 021-22122239"
)


# =========================================================
# SEND TO TELEGRAM
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
# ONLY AFTER SUCCESS:
# MARK TODAY AS POSTED
# =========================================================

history["last_post_date"] = today_key

history["last_post_time"] = (
    now.strftime(
        "%Y-%m-%d %H:%M:%S"
    )
)

save_history(
    history
)


print(
    "======================================"
)

print(
    "Market post sent successfully."
)

print(
    "Date saved:",
    today_key
)

print(
    "======================================"
)