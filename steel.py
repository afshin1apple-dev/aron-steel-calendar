import os
import json
import requests

from datetime import datetime
from zoneinfo import ZoneInfo

from price import get_prices


# =========================================================
# SETTINGS
# =========================================================

TOKEN = os.environ["BOT_TOKEN"]
CHANNEL = os.environ["CHANNEL_ID"]
PEXELS_KEY = os.environ["PEXELS_API_KEY"]

TEHRAN = ZoneInfo("Asia/Tehran")

STEEL_HISTORY_FILE = "steel_history.json"


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
# PRICE FORMAT
# =========================================================

def format_price(value):

    if value is None:
        return "نامشخص"

    return f"{value:,.0f}"


# =========================================================
# CHANGE FORMAT
# =========================================================

def format_change(value):

    if value is None:
        return "⚪ بدون سابقه"

    if value > 0:

        return f"🟢 +{value:.2f}%"

    if value < 0:

        return f"🔴 {value:.2f}%"

    return "⚪ 0.00%"


# =========================================================
# LOAD STEEL HISTORY
# =========================================================

def load_history():

    if not os.path.exists(
        STEEL_HISTORY_FILE
    ):

        return {}

    try:

        with open(
            STEEL_HISTORY_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

            if isinstance(data, dict):

                return data

            return {}

    except Exception as e:

        print(
            "Steel history load error:",
            e
        )

        return {}


# =========================================================
# SAVE STEEL HISTORY
# =========================================================

def save_history(history):

    with open(
        STEEL_HISTORY_FILE,
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
# CALCULATE CHANGE
# =========================================================

def calculate_change(
    current,
    previous
):

    if (
        current is None
        or previous is None
        or previous == 0
    ):

        return None

    return (
        (current - previous)
        / previous
    ) * 100


# =========================================================
# GET PREVIOUS PRICE
# =========================================================

def get_previous_price(
    previous_prices,
    size
):

    if not previous_prices:
        return None

    value = previous_prices.get(
        str(size)
    )

    if value is None:

        value = previous_prices.get(
            size
        )

    return value


# =========================================================
# TIME
# =========================================================

now = datetime.now(
    TEHRAN
)

today_key = now.strftime(
    "%Y-%m-%d"
)

weekday = now.weekday()


# =========================================================
# FRIDAY CHECK
# =========================================================
#
# Python:
# Monday    = 0
# Tuesday   = 1
# Wednesday = 2
# Thursday  = 3
# Friday    = 4
# Saturday  = 5
# Sunday    = 6
#
# =========================================================

if weekday == 4:

    print(
        "======================================"
    )

    print(
        "STEEL MARKET"
    )

    print(
        "Today is Friday."
    )

    print(
        "Steel post will NOT be sent."
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

    raise SystemExit(0)


# =========================================================
# START
# =========================================================

print(
    "======================================"
)

print(
    "STEEL MARKET"
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

previous_prices = history.get(
    "last_steel_prices"
)


# =========================================================
# GET STEEL PRICES
# =========================================================

print(
    "Getting steel prices from Pivan..."
)

steel_prices = get_prices()


print(
    "Steel products found:",
    len(steel_prices)
)


if not steel_prices:

    raise RuntimeError(
        "No steel prices found"
    )


# =========================================================
# CURRENT STEEL PRICES
# =========================================================

current_prices = {}


for steel in steel_prices:

    size = steel.get(
        "size"
    )

    steel_price = steel.get(
        "price"
    )

    if size is None:

        continue

    current_prices[
        str(size)
    ] = steel_price

    print(
        f"Steel size {size}: "
        f"{steel_price}"
    )


if not current_prices:

    raise RuntimeError(
        "No valid steel prices found"
    )


# =========================================================
# BUILD MESSAGE
# =========================================================

message_parts = [

    "🏗 <b>گزارش قیمت فولاد</b>",
    "",
    "📍 <b>میلگرد فولاد خراسان نیشابور</b>",
    "💰 قیمت‌ها به تومان",
    ""
]


# =========================================================
# ADD PRICES + COMPARISON
# =========================================================

for size, current in current_prices.items():

    previous = get_previous_price(
        previous_prices,
        size
    )

    change = calculate_change(
        current,
        previous
    )

    message_parts.append(
        f"🔩 <b>میلگرد {size}</b>"
    )

    message_parts.append(
        f"💰 {format_price(current)} تومان"
    )

    message_parts.append(
        f"📊 تغییر: {format_change(change)}"
    )

    message_parts.append("")


# =========================================================
# FOOTER
# =========================================================

message_parts.append(
    COMPANY_FOOTER
)


message = "\n".join(
    message_parts
)


# =========================================================
# PRINT MESSAGE
# =========================================================

print(
    "======================================"
)

print(
    "STEEL MESSAGE"
)

print(
    message
)

print(
    "======================================"
)


# =========================================================
# GET IMAGE
# =========================================================

print(
    "Getting steel image..."
)


r = requests.get(

    "https://api.pexels.com/v1/search",

    headers={
        "Authorization":
            PEXELS_KEY
    },

    params={

        "query":
            "steel rebar construction",

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
        "No steel image found"
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
# SEND TELEGRAM
# =========================================================

print(
    "Sending steel post..."
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
# SAVE HISTORY ONLY AFTER SUCCESS
# =========================================================

history[
    "last_steel_post_date"
] = today_key


history[
    "last_steel_post_time"
] = now.strftime(
    "%Y-%m-%d %H:%M:%S"
)


history[
    "last_steel_prices"
] = current_prices


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
    "STEEL POST SENT SUCCESSFULLY"
)

print(
    "Steel prices saved for comparison."
)

print(
    "======================================"
)