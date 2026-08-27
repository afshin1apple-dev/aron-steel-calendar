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

# Telegram numeric chat ID for private management message
PRIVATE_CHAT_ID = os.environ.get("PRIVATE_CHAT_ID")

TEHRAN = ZoneInfo("Asia/Tehran")

HISTORY_FILE = "steel_history.json"


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
        return "تماس بگیرید"

    return f"{int(value):,}"


# =========================================================
# LOAD HISTORY
# =========================================================

def load_history():

    if not os.path.exists(HISTORY_FILE):
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
# FACTORY COMPARISON
# =========================================================

def compare_factory(
    current,
    previous
):

    if not current or not previous:
        return None

    previous_map = {}

    for item in previous:

        if item.get("price") is None:
            continue

        try:

            size = int(item["size"])
            old_price = float(item["price"])

            previous_map[size] = old_price

        except Exception:
            continue


    changes = []

    for item in current:

        if item.get("price") is None:
            continue

        try:

            size = int(item["size"])

            current_price = float(
                item["price"]
            )

            old_price = previous_map.get(
                size
            )

            if (
                old_price is None
                or old_price == 0
            ):
                continue

            percent = (
                (current_price - old_price)
                / old_price
            ) * 100

            changes.append(percent)

        except Exception:
            continue


    if not changes:
        return None


    return (
        sum(changes)
        / len(changes)
    )


# =========================================================
# COMPARISON TEXT
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
            "📊 <b>مقایسه با آخرین قیمت</b>\n"
            "⚪ اطلاعات کافی برای مقایسه وجود ندارد."
        )


    if result > 0.01:

        return (
            "📊 <b>مقایسه با آخرین قیمت</b>\n"
            f"🟢 قیمت میلگرد در مجموع "
            f"<b>{result:+.2f}٪</b> افزایش داشته است."
        )


    if result < -0.01:

        return (
            "📊 <b>مقایسه با آخرین قیمت</b>\n"
            f"🔴 قیمت میلگرد در مجموع "
            f"<b>{result:.2f}٪</b> کاهش داشته است."
        )


    return (
        "📊 <b>مقایسه با آخرین قیمت</b>\n"
        "⚪ قیمت میلگرد در مجموع بدون تغییر بوده است."
    )


# =========================================================
# PRICE TABLE
# =========================================================

def build_price_table(prices):

    if not prices:

        return "⚪ اطلاعات قیمت در دسترس نیست."


    # فقط محصولاتی که قیمت دارند
    valid_prices = [
        item
        for item in prices
        if item.get("price") is not None
    ]


    if not valid_prices:

        return "⚪ اطلاعات قیمت در دسترس نیست."


    lines = []


    # دو ستون کنار هم
    for i in range(
        0,
        len(valid_prices),
        2
    ):

        left = valid_prices[i]

        right = (
            valid_prices[i + 1]
            if i + 1 < len(valid_prices)
            else None
        )


        left_text = (
            f"▫️ {left['size']}  "
            f"{format_price(left['price'])}"
        )


        if right:

            right_text = (
                f"▫️ {right['size']}  "
                f"{format_price(right['price'])}"
            )

            lines.append(
                f"{left_text:<25}{right_text}"
            )

        else:

            lines.append(
                left_text
            )


    return "\n".join(lines)


# =========================================================
# FACTORY POST
# =========================================================

def build_factory_post(
    factory_name,
    prices,
    previous
):

    message = (

        f"🏗 <b>{factory_name}</b>\n"
        "📌 <b>قیمت روز میلگرد</b>\n"
        "💰 <b>واحد قیمت: تومان</b>\n\n"

        "سایز       قیمت       سایز       قیمت\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"

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
# TELEGRAM
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
            "Telegram error:",
            e
        )

        return False


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
        "🔐 <b>قیمت سایر کارخانه‌ها</b>\n\n"
    )


    main_factories = {
        "نیشابور",
        "هیربد",
        "امیرکبیر"
    }


    found = False


    for factory_key, factory_data in all_prices.items():

        if factory_key in main_factories:
            continue


        prices = factory_data.get(
            "prices",
            []
        )


        if not prices:
            continue


        found = True


        message += (
            f"🏗 <b>{factory_data.get('name', factory_key)}</b>\n"
        )


        for item in prices:

            if item.get("price") is None:
                continue


            message += (
                f"▫️ سایز {item['size']}: "
                f"{format_price(item['price'])} تومان\n"
            )


        message += "\n"


    if not found:

        message += (
            "⚪ در حال حاضر قیمت کارخانه‌های "
            "دیگر دریافت نشد."
        )


    message += (
        "\n"
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


    # =====================================================
    # FRIDAY
    # =====================================================

    if now.weekday() == 4:

        print(
            "Friday."
        )

        print(
            "Steel post will NOT be sent."
        )

        return


    # =====================================================
    # GET ALL PRICES
    # =====================================================

    print(
        "Getting steel prices..."
    )


    all_prices = get_all_prices()


    if not all_prices:

        print(
            "No factory prices received."
        )

        return


    print(
        "Factories received:",
        len(all_prices)
    )


    # =====================================================
    # HISTORY
    # =====================================================

    history = load_history()


    previous_factories = history.get(
        "factories",
        {}
    )


    # =====================================================
    # MAIN FACTORIES
    # =====================================================

    main_factories = [

        "نیشابور",
        "هیربد",
        "امیرکبیر"

    ]


    for factory_key in main_factories:

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

            factory_data.get(
                "name",
                factory_key
            ),

            prices,

            previous

        )


        print()
        print(
            "Sending:",
            factory_data.get(
                "name",
                factory_key
            )
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


    # =====================================================
    # PRIVATE OTHER FACTORIES
    # =====================================================

    print(
        "Sending other factories privately..."
    )


    send_private_message(
        all_prices
    )


    # =====================================================
    # SAVE HISTORY
    # =====================================================

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


    # =====================================================
    # SUCCESS
    # =====================================================

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