import os
import json
import requests

from datetime import datetime
from zoneinfo import ZoneInfo

from price import get_all_prices


# =========================================================
# SETTINGS
# =========================================================

TOKEN = os.environ["BOT_TOKEN"]

CHANNEL = os.environ["CHANNEL_ID"]

# Telegram numeric Chat ID of Afshin
PRIVATE_CHAT_ID = os.environ.get(
    "PRIVATE_CHAT_ID"
)

TEHRAN = ZoneInfo(
    "Asia/Tehran"
)

STEEL_HISTORY_FILE = (
    "steel_history.json"
)


# =========================================================
# MAIN FACTORIES
# =========================================================
#
# فقط این سه کارخانه در کانال منتشر می‌شوند.
#
# سایر کارخانه‌ها فقط برای مدیریت ارسال می‌شوند.
#

MAIN_FACTORIES = [
    "نیشابور",
    "هیربد",
    "امیرکبیر"
]


# =========================================================
# COMPANY FOOTER
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

    return f"{float(value):,.0f}"


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
# LOAD HISTORY
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
# SAVE HISTORY
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
# OVERALL FACTORY COMPARISON
# =========================================================

def calculate_overall_change(
    current_prices,
    previous_prices
):

    if (
        not current_prices
        or not previous_prices
    ):

        return None

    changes = []

    previous_map = {}

    for item in previous_prices:

        if item.get("price") is None:
            continue

        try:

            previous_map[
                int(item["size"])
            ] = float(
                item["price"]
            )

        except Exception:

            continue

    for item in current_prices:

        current_price = item.get(
            "price"
        )

        if current_price is None:
            continue

        try:

            size = int(
                item["size"]
            )

            current_price = float(
                current_price
            )

        except Exception:

            continue

        previous_price = previous_map.get(
            size
        )

        if (
            previous_price is None
            or previous_price == 0
        ):

            continue

        change = (
            (
                current_price
                - previous_price
            )
            / previous_price
        ) * 100

        changes.append(
            change
        )

    if not changes:

        return None

    return (
        sum(changes)
        / len(changes)
    )


# =========================================================
# BUILD OVERALL COMPARISON
# =========================================================

def build_comparison(
    current_prices,
    previous_prices
):

    result = calculate_overall_change(
        current_prices,
        previous_prices
    )

    if result is None:

        return (
            "📊 <b>مقایسه با آخرین قیمت:</b>\n"
            "⚪ اطلاعات کافی برای مقایسه وجود ندارد."
        )

    if result > 0.01:

        return (
            "📊 <b>مقایسه با آخرین قیمت:</b>\n"
            f"🟢 قیمت میلگرد در مجموع "
            f"<b>افزایش</b> داشته است "
            f"({result:+.2f}٪)"
        )

    if result < -0.01:

        return (
            "📊 <b>مقایسه با آخرین قیمت:</b>\n"
            f"🔴 قیمت میلگرد در مجموع "
            f"<b>کاهش</b> داشته است "
            f"({result:+.2f}٪)"
        )

    return (
        "📊 <b>مقایسه با آخرین قیمت:</b>\n"
        "⚪ قیمت میلگرد در مجموع "
        "<b>بدون تغییر</b> بوده است."
    )


# =========================================================
# BUILD PRICE TABLE
# =========================================================

def build_price_table(
    prices
):

    if not prices:

        return (
            "اطلاعات قیمت در دسترس نیست."
        )

    lines = []

    for item in prices:

        size = item.get(
            "size"
        )

        value = item.get(
            "price"
        )

        if size is None:
            continue

        lines.append(
            f"🔩 <b>میلگرد {size}</b>\n"
            f"💰 {format_price(value)} تومان"
        )

    return "\n\n".join(
        lines
    )


# =========================================================
# BUILD CHANNEL POST
# =========================================================

def build_channel_post(
    factory_name,
    prices,
    previous
):

    message = (
        f"🏗 <b>{factory_name}</b>\n"
        f"📌 <b>قیمت روز میلگرد</b>\n"
        f"💰 واحد قیمت: تومان\n\n"
    )

    message += build_price_table(
        prices
    )

    message += "\n\n"

    message += build_comparison(
        prices,
        previous
    )

    message += (
        "\n\n"
        "📞 جهت اطلاع از قیمت سایر کارخانه‌ها "
        "با واحد فروش تماس حاصل نمایید."
    )

    message += (
        "\n\n"
        + COMPANY_FOOTER
    )

    return message


# =========================================================
# SEND TELEGRAM MESSAGE
# =========================================================

def send_message(
    chat_id,
    message
):

    if not chat_id:

        print(
            "❌ Chat ID not configured."
        )

        return False

    try:

        response = requests.post(

            f"https://api.telegram.org/"
            f"bot{TOKEN}/sendMessage",

            data={

                "chat_id":
                    chat_id,

                "text":
                    message,

                "parse_mode":
                    "HTML",

                "disable_web_page_preview":
                    True
            },

            timeout=30
        )

        print(
            "Telegram response:",
            response.text
        )

        return response.ok

    except Exception as e:

        print(
            "Telegram send error:",
            e
        )

        return False


# =========================================================
# BUILD PRIVATE FACTORY MESSAGE
# =========================================================

def build_private_factory_message(
    factory_name,
    prices
):

    message = (
        f"🏭 <b>{factory_name}</b>\n"
        f"📌 <b>قیمت روز میلگرد</b>\n"
        f"💰 واحد قیمت: تومان\n\n"
    )

    message += build_price_table(
        prices
    )

    return message


# =========================================================
# SEND OTHER FACTORIES PRIVATELY
# =========================================================

def send_private_other_factories(
    all_prices
):

    print(
        "======================================"
    )

    print(
        "PRIVATE FACTORY REPORT"
    )

    print(
        "Private Chat ID:",
        PRIVATE_CHAT_ID
    )

    print(
        "======================================"
    )

    if not PRIVATE_CHAT_ID:

        print(
            "❌ PRIVATE_CHAT_ID is empty."
        )

        print(
            "Private report will NOT be sent."
        )

        return False

    # -----------------------------------------------------
    # Find all factories except the 3 main factories
    # -----------------------------------------------------

    other_factories = []

    for factory_key, factory_data in all_prices.items():

        if factory_key in MAIN_FACTORIES:

            continue

        if not isinstance(
            factory_data,
            dict
        ):

            continue

        prices = factory_data.get(
            "prices",
            []
        )

        if not prices:

            continue

        factory_name = factory_data.get(
            "name",
            factory_key
        )

        other_factories.append(
            (
                factory_key,
                factory_name,
                prices
            )
        )

    # -----------------------------------------------------
    # Nothing found
    # -----------------------------------------------------

    if not other_factories:

        print(
            "⚠️ No other factory prices found."
        )

        message = (
            "🔐 <b>قیمت سایر کارخانه‌ها</b>\n\n"
            "⚪ در حال حاضر قیمت کارخانه‌های "
            "دیگر دریافت نشد."
        )

        message += (
            "\n\n"
            + COMPANY_FOOTER
        )

        return send_message(
            PRIVATE_CHAT_ID,
            message
        )

    # -----------------------------------------------------
    # Build one private message
    # -----------------------------------------------------

    parts = [

        "🔐 <b>قیمت سایر کارخانه‌ها</b>",
        "",
        "📌 این گزارش فقط برای مدیریت ارسال شده است.",
        ""
    ]

    for (
        factory_key,
        factory_name,
        prices
    ) in other_factories:

        print(
            "Private factory:",
            factory_key
        )

        parts.append(
            build_private_factory_message(
                factory_name,
                prices
            )
        )

        parts.append(
            "━━━━━━━━━━━━━━"
        )

    parts.append(
        "📞 جهت اطلاع از قیمت سایر کارخانه‌ها "
        "با واحد فروش تماس حاصل نمایید."
    )

    parts.append(
        COMPANY_FOOTER
    )

    message = "\n\n".join(
        parts
    )

    # -----------------------------------------------------
    # Send
    # -----------------------------------------------------

    success = send_message(
        PRIVATE_CHAT_ID,
        message
    )

    if success:

        print(
            "✅ PRIVATE FACTORY REPORT SENT"
        )

    else:

        print(
            "❌ PRIVATE FACTORY REPORT FAILED"
        )

    return success


# =========================================================
# GET IMAGE
# =========================================================

def get_steel_image():

    pexels_key = os.environ.get(
        "PEXELS_API_KEY"
    )

    if not pexels_key:

        print(
            "⚠️ PEXELS_API_KEY not configured."
        )

        return None

    print(
        "Getting steel image..."
    )

    try:

        response = requests.get(

            "https://api.pexels.com/v1/search",

            headers={
                "Authorization":
                    pexels_key
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

        response.raise_for_status()

        photos = response.json().get(
            "photos",
            []
        )

        if not photos:

            print(
                "⚠️ No steel image found."
            )

            return None

        now = datetime.now(
            TEHRAN
        )

        photo = photos[
            now.date().toordinal()
            % len(photos)
        ]

        return photo[
            "src"
        ][
            "large2x"
        ]

    except Exception as e:

        print(
            "Image error:",
            e
        )

        return None


# =========================================================
# SEND CHANNEL POST
# =========================================================

def send_channel_post(
    message,
    image_url
):

    print(
        "Sending steel post to channel..."
    )

    if image_url:

        response = requests.post(

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

    else:

        response = requests.post(

            f"https://api.telegram.org/"
            f"bot{TOKEN}/sendMessage",

            data={

                "chat_id":
                    CHANNEL,

                "text":
                    message,

                "parse_mode":
                    "HTML",

                "disable_web_page_preview":
                    True
            },

            timeout=30
        )

    print(
        "Telegram channel response:"
    )

    print(
        response.text
    )

    if not response.ok:

        raise RuntimeError(
            response.text
        )

    return True


# =========================================================
# MAIN
# =========================================================

def main():

    now = datetime.now(
        TEHRAN
    )

    today_key = now.strftime(
        "%Y-%m-%d"
    )

    weekday = now.weekday()

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

    # -----------------------------------------------------
    # FRIDAY
    # -----------------------------------------------------

    if weekday == 4:

        print(
            "Today is Friday."
        )

        print(
            "Steel post will NOT be sent."
        )

        return

    # -----------------------------------------------------
    # LOAD HISTORY
    # -----------------------------------------------------

    history = load_history()

    previous_prices = history.get(
        "last_steel_prices"
    )

    # -----------------------------------------------------
    # GET ALL FACTORY PRICES
    # -----------------------------------------------------

    print(
        "Getting all steel prices..."
    )

    all_prices = get_all_prices()

    if not all_prices:

        raise RuntimeError(
            "No factory prices found"
        )

    print(
        "Factories found:",
        len(all_prices)
    )

    for key in all_prices:

        print(
            "Factory:",
            key
        )

    # -----------------------------------------------------
    # GET IMAGE
    # -----------------------------------------------------

    image_url = get_steel_image()

    # -----------------------------------------------------
    # MAIN CHANNEL FACTORIES
    # -----------------------------------------------------

    for factory_key in MAIN_FACTORIES:

        factory_data = all_prices.get(
            factory_key
        )

        if not factory_data:

            print(
                "⚠️ Factory data missing:",
                factory_key
            )

            continue

        prices = factory_data.get(
            "prices",
            []
        )

        if not prices:

            print(
                "⚠️ No prices:",
                factory_key
            )

            continue

        previous = {}

        if isinstance(
            previous_prices,
            dict
        ):

            previous = previous_prices.get(
                factory_key,
                {}
            )

        # -------------------------------------------------
        # Support both old and new history format
        # -------------------------------------------------

        if isinstance(
            previous,
            dict
        ):

            previous_list = []

            for size, value in previous.items():

                previous_list.append({

                    "size":
                        size,

                    "price":
                        value
                })

        else:

            previous_list = previous

        message = build_channel_post(

            factory_data.get(
                "name",
                factory_key
            ),

            prices,

            previous_list
        )

        print()
        print(
            "Sending channel:",
            factory_key
        )

        send_channel_post(
            message,
            image_url
        )

        print(
            "✅ CHANNEL POST SENT:",
            factory_key
        )

    # -----------------------------------------------------
    # PRIVATE OTHER FACTORIES
    # -----------------------------------------------------

    send_private_other_factories(
        all_prices
    )

    # -----------------------------------------------------
    # SAVE CURRENT PRICES
    # -----------------------------------------------------

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
    ] = {}

    # Save all factory prices for future comparison
    for factory_key, factory_data in all_prices.items():

        if not isinstance(
            factory_data,
            dict
        ):

            continue

        prices = factory_data.get(
            "prices",
            []
        )

        if not prices:

            continue

        factory_history = {}

        for item in prices:

            size = item.get(
                "size"
            )

            value = item.get(
                "price"
            )

            if (
                size is None
                or value is None
            ):

                continue

            factory_history[
                str(size)
            ] = value

        history[
            "last_steel_prices"
        ][factory_key] = (
            factory_history
        )

    save_history(
        history
    )

    # -----------------------------------------------------
    # SUCCESS
    # -----------------------------------------------------

    print(
        "======================================"
    )

    print(
        "STEEL BOT FINISHED"
    )

    print(
        "Channel factories:"
    )

    print(
        "نیشابور / هیربد / امیرکبیر"
    )

    print(
        "Other factories:"
    )

    print(
        "PRIVATE ONLY"
    )

    print(
        "======================================")


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    main()