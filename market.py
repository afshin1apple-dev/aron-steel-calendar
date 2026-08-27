import os
import json
import requests

from bs4 import BeautifulSoup
from datetime import datetime
from zoneinfo import ZoneInfo

# =========================================================
# PIVAN PRICE
# =========================================================

from price import get_prices


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

    if text is None:
        return None

    text = str(text)

    text = (
        text
        .replace(",", "")
        .replace("٬", "")
        .replace(" ", "")
        .strip()
    )

    try:
        return float(text)

    except Exception:
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
# COMPARE PRICES
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
    "Iran time:",
    now.strftime(
        "%Y-%m-%d %H:%M:%S"
    )
)

print(
    "======================================"
)


# =========================================================
# LOAD HISTORY
# =========================================================

history = load_history()

last_post_date = history.get(
    "last_post_date"
)

last_post_prices = history.get(
    "last_post_prices"
)


# =========================================================
# GET GOLD WORLD
# =========================================================

print(
    "Getting gold world..."
)

gold_world, gold_world_change = (
    get_tgju_price(
        "https://www.tgju.org/profile/ons"
    )
)


# =========================================================
# GET GOLD 18
# =========================================================

print(
    "Getting gold 18..."
)

gold18, gold18_change = (
    get_tgju_price(
        "https://www.tgju.org/profile/geram18"
    )
)


# =========================================================
# GET COIN
# =========================================================

print(
    "Getting coin..."
)

coin, coin_change = (
    get_tgju_price(
        "https://www.tgju.org/profile/sekee"
    )
)


# =========================================================
# GET TETHER
# =========================================================

print(
    "Getting tether..."
)

tether = get_tether()


# =========================================================
# GET BITCOIN
# =========================================================

print(
    "Getting bitcoin..."
)

bitcoin, bitcoin_change = (
    get_bitcoin()
)


# =========================================================
# GET STEEL FROM PIVAN
# =========================================================

print(
    "Getting steel prices..."
)

steel_prices = get_prices()

print(
    "Steel products found:",
    len(steel_prices)
)

for steel in steel_prices:

    steel_price = steel.get(
        "price"
    )

    if steel_price is not None:

        print(
            f"Steel size {steel['size']}: "
            f"{steel_price:,} تومان"
        )

    else:

        print(
            f"Steel size {steel['size']}: "
            f"PRICE NOT AVAILABLE"
        )


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
# STEEL PRICE DICTIONARY
# =========================================================

steel_current_prices = {}

for steel in steel_prices:

    size = steel.get(
        "size"
    )

    steel_price = steel.get(
        "price"
    )

    if (
        size is not None
        and steel_price is not None
    ):

        key = f"steel_{size}"

        steel_current_prices[key] = (
            steel_price
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
        tether,

    **steel_current_prices
}


print(
    "======================================"
)

print(
    "Current prices:"
)

for name, value in current_prices.items():

    print(
        f"{name}: {value}"
    )

print(
    "======================================"
)


# =========================================================
# DECIDE WHETHER TO POST
# =========================================================

should_post = False


# ---------------------------------------------------------
# FIRST POST OF TODAY
# ---------------------------------------------------------

if last_post_date != today_key:

    print(
        "This is the first market post of today."
    )

    print(
        "Post will be sent."
    )

    should_post = True


# ---------------------------------------------------------
# SAME DAY
# ---------------------------------------------------------

else:

    print(
        "A market post was already sent today."
    )

    if not last_post_prices:

        print(
            "No saved prices from the previous post."
        )

        print(
            "Post will be sent now."
        )

        should_post = True

    else:

        price_changes = compare_prices(
            current_prices,
            last_post_prices
        )

        print(
            "Changes since last market post:"
        )

        if price_changes:

            for name, value in price_changes.items():

                print(
                    f"{name}: {value:+.2f}%"
                )

        else:

            print(
                "No comparable prices found."
            )

        if has_significant_change(
            price_changes
        ):

            print(
                "At least one price changed "
                "more than 5%."
            )

            print(
                "New market post will be sent."
            )

            should_post = True

        else:

            print(
                "No price changed more than 5%."
            )

            print(
                "Nothing to do."
            )

            should_post = False


# =========================================================
# IF NO POST NEEDED
# =========================================================

if not should_post:

    print(
        "======================================"
    )

    print(
        "Market post skipped."
    )

    print(
        "Reason: No price movement above 5%."
    )

    print(
        "======================================"
    )

    raise SystemExit(0)


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
            "gold bitcoin steel finance trading",

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
# STEEL MESSAGE
# =========================================================

steel_message = ""

if steel_prices:

    steel_message += (
        "🏭 <b>میلگرد فولاد خراسان نیشابور</b>\n"
    )

    steel_message += (
        "📍 محل تحویل: کارخانه\n\n"
    )

    for steel in steel_prices:

        steel_price = steel.get(
            "price"
        )

        if steel_price is None:
            continue

        size = steel.get(
            "size"
        )

        fluctuation = steel.get(
            "fluctuation_percent"
        )

        steel_message += (
            f"📏 سایز {size}: "
            f"<b>{price(steel_price)}</b> تومان"
        )

        if fluctuation is not None:

            steel_message += (
                f"  ({change(fluctuation)})"
            )

        steel_message += "\n"

    steel_message += "\n"


# =========================================================
# MESSAGE
# =========================================================

message = (

    "📊 <b>گزارش بازار امروز</b>\n\n"

    "━━━━━━━━━━━━━━\n"

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

    "━━━━━━━━━━━━━━\n\n"

    f"{steel_message}"

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

history["last_post_date"] = (
    today_key
)

history["last_post_time"] = (
    now.strftime(
        "%Y-%m-%d %H:%M:%S"
    )
)

history["last_post_prices"] = (
    current_prices
)

history["tether"] = tether


save_history(
    history
)


# =========================================================
# SUCCESS
# =========================================================

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
    "Saved prices for 5% comparison."
)

print(
    "Steel prices included:",
    len(steel_prices)
)

print(
    "======================================"
)