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

# Telegram numeric private chat ID
PRIVATE_CHAT_ID = os.environ.get("PRIVATE_CHAT_ID")

TEHRAN = ZoneInfo("Asia/Tehran")

HISTORY_FILE = "steel_history.json"


# =========================================================
# MAIN FACTORIES
# =========================================================

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
# FORMAT PRICE
# =========================================================

def price(value):

    if value is None:
        return "تماس بگیرید"

    try:
        return f"{int(float(value)):,}"
    except Exception:
        return "تماس بگیرید"


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
# NORMALIZE PRICES
# =========================================================

def normalize_prices(prices):

    result = []

    if not prices:
        return result

    for item in prices:

        try:

            size = item.get("size")
            value = item.get("price")

            if size is None:
                continue

            if value is not None:
                value = float(value)

            result.append({
                "size": str(size),
                "price": value
            })

        except Exception as e:

            print(
                "Price normalize error:",
                e
            )

    return result


# =========================================================
# BUILD PRICE MAP
# =========================================================

def price_map(prices):

    result = {}

    for item in normalize_prices(prices):

        try:

            size = int(
                str(item["size"]).strip()
            )

            value = item.get("price")

            if value is not None:

                result[size] = float(value)

        except Exception:

            continue

    return result


# =========================================================
# OVERALL FACTORY COMPARISON
# =========================================================

def compare_factory(
    current,
    previous
):

    current_map = price_map(current)
    previous_map = price_map(previous)

    if not current_map or not previous_map:
        return None

    changes = []

    for size, current_price in current_map.items():

        old_price = previous_map.get(size)

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
            "📊 <b>مقایسه با آخرین قیمت:</b>\n"
            "⚪ اطلاعات کافی برای مقایسه وجود ندارد."
        )

    if result > 0.01:

        return (
            "📊 <b>مقایسه با آخرین قیمت:</b>\n"
            f"🟢 قیمت میلگرد در مجموع "
            f"<b>{result:+.2f}٪</b> افزایش داشته است."
        )

    if result < -0.01:

        return (
            "📊 <b>مقایسه با آخرین قیمت:</b>\n"
            f"🔴 قیمت میلگرد در مجموع "
            f"<b>{result:+.2f}٪</b> کاهش داشته است."
        )

    return (
        "📊 <b>مقایسه با آخرین قیمت:</b>\n"
        "⚪ قیمت میلگرد در مجموع بدون تغییر بوده است."
    )


# =========================================================
# BUILD TWO-COLUMN PRICE TABLE
# =========================================================

def build_price_table(prices):

    prices = normalize_prices(prices)

    if not prices:

        return (
            "اطلاعات قیمت در دسترس نیست."
        )

    # مرتب‌سازی بر اساس سایز
    try:

        prices.sort(
            key=lambda x: int(x["size"])
        )

    except Exception:
        pass

    lines = []

    # -----------------------------------------------------
    # Header
    # -----------------------------------------------------

    header = (
        "<code>"
        "سایز   قیمت          سایز   قیمت"
        "</code>"
    )

    # -----------------------------------------------------
    # Two columns
    # -----------------------------------------------------

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

        left_size = str(
            left["size"]
        )

        left_price = price(
            left.get("price")
        )

        left_text = (
            f"{left_size:>4}  "
            f"{left_price:>12}"
        )

        if right:

            right_size = str(
                right["size"]
            )

            right_price = price(
                right.get("price")
            )

            right_text = (
                f"{right_size:>4}  "
                f"{right_price:>12}"
            )

            line = (
                "<code>"
                f"{left_text}    "
                f"{right_text}"
                "</code>"
            )

        else:

            line = (
                "<code>"
                f"{left_text}"
                "</code>"
            )

        lines.append(line)

    return (
        header
        + "\n"
        + "\n".join(lines)
    )


# =========================================================
# BUILD CHANNEL POST
# =========================================================

def build_factory_post(
    factory_name,
    prices,
    previous
):

    message = (

        f"🏗 <b>{factory_name}</b>\n"
        f"📌 <b>قیمت روز میلگرد</b>\n"
        f"💰 واحد قیمت: تومان\n\n"

        f"{build_price_table(prices)}\n\n"

        f"{comparison_text(prices, previous)}\n\n"

        "📞 جهت اطلاع از قیمت سایر کارخانه‌ها "
        "با واحد فروش تماس حاصل نمایید.\n\n"

        f"{COMPANY_FOOTER}"
    )

    return message


# =========================================================
# BUILD PRIVATE POST
# =========================================================

def build_private_post(
    factory_name,
    prices,
    previous
):

    message = (

        f"🔐 <b>{factory_name}</b>\n"
        f"📌 <b>قیمت روز میلگرد</b>\n"
        f"💰 واحد قیمت: تومان\n\n"

        f"{build_price_table(prices)}\n\n"

        f"{comparison_text(prices, previous)}\n\n"

        f"{COMPANY_FOOTER}"
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
            "Chat ID is empty."
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

        if response.ok:

            return True

        print(
            "Telegram send failed."
        )

        return False

    except Exception as e:

        print(
            "Telegram error:",
            e
        )

        return False


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

    # Python:
    # Monday = 0
    # Tuesday = 1
    # Wednesday = 2
    # Thursday = 3
    # Friday = 4
    # Saturday = 5
    # Sunday = 6

    if now.weekday() == 4:

        print(
            "Friday."
        )

        print(
            "No steel post today."
        )

        return

    # =====================================================
    # GET ALL PRICES
    # =====================================================

    print(
        "Getting steel prices..."
    )

    try:

        all_prices = get_all_prices()

    except Exception as e:

        print(
            "ERROR getting prices:",
            e
        )

        raise

    if not all_prices:

        print(
            "No factory prices returned."
        )

        return

    print(
        "Factories found:",
        len(all_prices)
    )

    for key in all_prices:

        print(
            "Factory:",
            key
        )

    # =====================================================
    # LOAD HISTORY
    # =====================================================

    history = load_history()

    previous_factories = history.get(
        "factories",
        {}
    )

    if not isinstance(
        previous_factories,
        dict
    ):

        previous_factories = {}

    # =====================================================
    # MAIN CHANNEL
    # =====================================================

    print()
    print(
        "======================================"
    )

    print(
        "CHANNEL POSTS"
    )

    print(
        "======================================"
    )

    for factory_key in MAIN_FACTORIES:

        factory_data = all_prices.get(
            factory_key
        )

        if not factory_data:

            print(
                "Factory missing:",
                factory_key
            )

            continue

        factory_name = factory_data.get(
            "name",
            factory_key
        )

        prices = normalize_prices(
            factory_data.get(
                "prices",
                []
            )
        )

        if not prices:

            print(
                "No prices:",
                factory_name
            )

            continue

        previous = previous_factories.get(
            factory_key,
            []
        )

        message = build_factory_post(
            factory_name,
            prices,
            previous
        )

        print()
        print(
            "Sending channel post:",
            factory_name
        )

        success = send_message(
            CHANNEL,
            message
        )

        if success:

            print(
                "CHANNEL POST SENT:",
                factory_name
            )

            previous_factories[
                factory_key
            ] = prices

        else:

            print(
                "CHANNEL POST FAILED:",
                factory_name
            )

    # =====================================================
    # PRIVATE MESSAGE
    # =====================================================

    print()
    print(
        "======================================"
    )

    print(
        "PRIVATE MESSAGE"
    )

    print(
        "======================================"
    )

    if not PRIVATE_CHAT_ID:

        print(
            "PRIVATE_CHAT_ID is not configured."
        )

    else:

        private_messages = []

        for factory_key, factory_data in all_prices.items():

            if factory_key in MAIN_FACTORIES:
                continue

            if not isinstance(
                factory_data,
                dict
            ):
                continue

            factory_name = factory_data.get(
                "name",
                factory_key
            )

            prices = normalize_prices(
                factory_data.get(
                    "prices",
                    []
                )
            )

            if not prices:

                print(
                    "No prices for private factory:",
                    factory_name
                )

                continue

            previous = previous_factories.get(
                factory_key,
                []
            )

            private_messages.append(
                build_private_post(
                    factory_name,
                    prices,
                    previous
                )
            )

            previous_factories[
                factory_key
            ] = prices

        # -------------------------------------------------
        # Send private messages
        # -------------------------------------------------

        if private_messages:

            private_header = (
                "🔐 <b>گزارش قیمت سایر کارخانه‌ها</b>\n\n"
                "این گزارش فقط برای مدیریت ارسال شده است.\n\n"
            )

            private_message = (
                private_header
                + "\n\n"
                .join(private_messages)
            )

            # Telegram message limit protection
            if len(private_message) <= 3900:

                success = send_message(
                    PRIVATE_CHAT_ID,
                    private_message
                )

                if success:

                    print(
                        "PRIVATE POST SENT SUCCESSFULLY"
                    )

                else:

                    print(
                        "PRIVATE POST FAILED"
                    )

            else:

                print(
                    "Private message is too long."
                )

                for message in private_messages:

                    success = send_message(
                        PRIVATE_CHAT_ID,
                        message
                    )

                    if success:

                        print(
                            "PRIVATE FACTORY POST SENT"
                        )

                    else:

                        print(
                            "PRIVATE FACTORY POST FAILED"
                        )

        else:

            print(
                "No other factories available."
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
    # FINISH
    # =====================================================

    print()
    print(
        "======================================"
    )

    print(
        "STEEL BOT FINISHED SUCCESSFULLY"
    )

    print(
        "======================================")


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    main()