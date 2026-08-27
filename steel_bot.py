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

# IMPORTANT:
# Telegram private user numeric chat ID
PRIVATE_CHAT_ID = os.environ.get(
    "PRIVATE_CHAT_ID"
)

TEHRAN = ZoneInfo(
    "Asia/Tehran"
)

HISTORY_FILE = (
    "steel_history.json"
)


# =========================================================
# COMPANY
# =========================================================

COMPANY_FOOTER = """
━━━━━━━━━━━━━━
🏭 آروند آرون استیل
👤 مدیریت: افشین آورزمانی
📞 021-22122239
🆔 @arvand_aron_steel
"""


# =========================================================
# FORMAT NUMBER
# =========================================================

def price(value):

    if value is None:
        return "تماس بگیرید"

    return f"{int(value):,}"


# =========================================================
# LOAD HISTORY
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

            if isinstance(
                data,
                dict
            ):

                return data

    except Exception as e:

        print(
            "History error:",
            e
        )

    return {}


# =========================================================
# SAVE HISTORY
# =========================================================

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
# COMPARE FACTORY
# =========================================================

def compare_factory(
    current,
    previous
):

    if not current or not previous:

        return None

    changes = []

    previous_map = {
        int(item["size"]):
            float(item["price"])
        for item in previous
        if item.get("price") is not None
    }

    for item in current:

        size = int(
            item["size"]
        )

        current_price = item.get(
            "price"
        )

        old_price = previous_map.get(
            size
        )

        if (
            current_price is None
            or old_price is None
            or old_price == 0
        ):

            continue

        percent = (
            (
                current_price
                - old_price
            )
            / old_price
        ) * 100

        changes.append(
            percent
        )

    if not changes:

        return None

    return (
        sum(changes)
        / len(changes)
    )


# =========================================================
# OVERALL COMPARISON TEXT
# =========================================================

def comparison_text(
    current,
    previous
):

    result = compare_factory(
        current,
        previous
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

    # -----------------------------------------------------
    # Two columns side by side
    # -----------------------------------------------------

    lines = []

    for i in range(
        0,
        len(prices),
        2
    ):

        left = prices[i]

        right = (
            prices[i + 1]
            if i + 1 < len(prices)
            else None
        )

        left_text = (
            f"{left['size']:>2}  "
            f"{price(left['price'])}"
        )

        if right:

            right_text = (
                f"{right['size']:>2}  "
                f"{price(right['price'])}"
            )

            line = (
                f"<code>"
                f"{left_text:<18}"
                f"{right_text}"
                f"</code>"
            )

        else:

            line = (
                f"<code>"
                f"{left_text}"
                f"</code>"
            )

        lines.append(
            line
        )

    header = (
        "<code>"
        "سایز   قیمت           سایز   قیمت"
        "</code>"
    )

    return (
        header
        + "\n"
        + "\n".join(lines)
    )


# =========================================================
# BUILD FACTORY POST
# =========================================================

def build_factory_post(
    factory_name,
    prices,
    previous
):

    message = (
        f"🏗 <b>{factory_name}</b>\n"
        f"📌 <b>قیمت روز میلگرد</b>\n\n"
    )

    message += build_price_table(
        prices
    )

    message += "\n\n"

    message += comparison_text(
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
# SEND MESSAGE
# =========================================================

def send_message(
    chat_id,
    message
):

    if not chat_id:

        print(
            "Chat ID not configured."
        )

        return False

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


# =========================================================
# PRIVATE OTHER FACTORIES
# =========================================================

def send_private_message(
    all_prices
):

    if not PRIVATE_CHAT_ID:

        print(
            "PRIVATE_CHAT_ID not configured."
        )

        return

    message = (
        "🔐 <b>گزارش قیمت سایر کارخانه‌ها</b>\n\n"
        "این گزارش فقط برای مدیریت ارسال شده است.\n\n"
    )

    # -----------------------------------------------------
    # فعلاً فقط کارخانه‌های خارج از سه کارخانه اصلی
    # -----------------------------------------------------
    #
    # این بخش را وقتی لیست کارخانه‌های موردنظر را مشخص
    # کردیم کامل می‌کنیم.
    #

    message += (
        "ℹ️ برای دریافت قیمت سایر کارخانه‌ها "
        "با واحد فروش تماس حاصل نمایید."
    )

    message += (
        "\n\n"
        + COMPANY_FOOTER
    )

    send_message(
        PRIVATE_CHAT_ID,
        message
    )


# =========================================================
# MAIN
# =========================================================

def main():

    now = datetime.now(
        TEHRAN
    )

    print(
        "======================================"
    )

    print(
        "STEEL BOT"
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

    # Python:
    # Monday = 0
    # Friday = 4

    if now.weekday() == 4:

        print(
            "Friday."
        )

        print(
            "Steel post will NOT be sent."
        )

        return

    # -----------------------------------------------------
    # GET PRICES
    # -----------------------------------------------------

    print(
        "Getting steel prices..."
    )

    all_prices = get_all_prices()

    # -----------------------------------------------------
    # HISTORY
    # -----------------------------------------------------

    history = load_history()

    previous_factories = history.get(
        "factories",
        {}
    )

    # -----------------------------------------------------
    # MAIN CHANNEL POSTS
    # -----------------------------------------------------

    for factory_key in [
        "نیشابور",
        "هیربد",
        "امیرکبیر"
    ]:

        factory_data = all_prices.get(
            factory_key
        )

        if not factory_data:

            print(
                "Factory data missing:",
                factory_key
            )

            continue

        prices = factory_data.get(
            "prices",
            []
        )

        if not prices:

            print(
                "No prices:",
                factory_key
            )

            continue

        previous = previous_factories.get(
            factory_key,
            []
        )

        message = build_factory_post(
            factory_data["name"],
            prices,
            previous
        )

        print()
        print(
            "Sending:",
            factory_data["name"]
        )

        success = send_message(
            CHANNEL,
            message
        )

        if success:

            print(
                "POST SENT:",
                factory_key
            )

            previous_factories[
                factory_key
            ] = prices

        else:

            print(
                "POST FAILED:",
                factory_key
            )

    # -----------------------------------------------------
    # PRIVATE MESSAGE
    # -----------------------------------------------------

    send_private_message(
        all_prices
    )

    # -----------------------------------------------------
    # SAVE HISTORY
    # -----------------------------------------------------

    history[
        "last_update"
    ] = now.strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    history[
        "factories"
    ] = previous_factories

    save_history(
        history
    )

    print()
    print(
        "======================================"
    )

    print(
        "STEEL BOT FINISHED"
    )

    print(
        "======================================")


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    main()