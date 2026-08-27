import os
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

def price(value):

    if value is None:
        return "نامشخص"

    return f"{value:,.0f}"


# =========================================================
# TIME
# =========================================================

now = datetime.now(
    TEHRAN
)


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
# GET STEEL
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


for steel in steel_prices:

    size = steel.get(
        "size"
    )

    steel_price = steel.get(
        "price"
    )

    print(
        f"Size {size}: "
        f"{steel_price}"
    )


# =========================================================
# BUILD STEEL MESSAGE
# =========================================================

message_parts = [

    "🏗 <b>گزارش قیمت فولاد</b>",

    "",

    "📍 <b>میلگرد فولاد خراسان نیشابور</b>",

    "💰 قیمت‌ها به تومان"
]


for steel in steel_prices:

    size = steel.get(
        "size"
    )

    steel_price = steel.get(
        "price"
    )

    if steel_price is None:

        message_parts.append(
            f"🔩 میلگرد {size}: "
            f"نامشخص"
        )

    else:

        message_parts.append(
            f"🔩 میلگرد {size}: "
            f"<b>{price(steel_price)}</b> تومان"
        )


message_parts.extend([

    "",

    "🌐 منبع: پیوان",

    "",

    COMPANY_FOOTER

])


message = "\n".join(
    message_parts
)


print(
    "======================================"
)

print(
    "Steel message:"
)

print(
    message
)

print(
    "======================================"
)


# =========================================================
# GET STEEL IMAGE
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
]["large2x"]


# =========================================================
# SEND TO TELEGRAM
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
# SUCCESS
# =========================================================

print(
    "======================================"
)

print(
    "STEEL POST SENT SUCCESSFULLY"
)

print(
    "======================================"
)