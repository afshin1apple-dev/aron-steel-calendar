import os
import re
import json
import requests
import pandas as pd

from io import StringIO
from datetime import datetime
from zoneinfo import ZoneInfo

from holiday import (
    is_non_working_day,
    get_holiday_name,
)


# =========================================================
# SETTINGS
# =========================================================

TIMEOUT = 30

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/125.0 Safari/537.36"
    )
}

TOKEN = os.environ.get("BOT_TOKEN")

# =========================================================
# IMPORTANT
# =========================================================
# قیمت میلگرد فقط برای چت خصوصی افشین ارسال می‌شود.
# CHANNEL_ID دیگر در این فایل استفاده نمی‌شود.
# =========================================================

PRIVATE_CHAT_ID = os.environ.get("PRIVATE_CHAT_ID")

PEXELS_KEY = os.environ.get("PEXELS_API_KEY")

TEHRAN = ZoneInfo("Asia/Tehran")

STEEL_HISTORY_FILE = "steel_history.json"


# =========================================================
# DIRECT PRICE SOURCE
# =========================================================
#
# منبع مستقیم:
# پیوان - میلگرد فولاد خراسان نیشابور
#
# =========================================================

SOURCE_URL = (
    "https://pivan.co/brands/"
    "khorasan-steel-neishabour/"
    "rebar/"
)

PEXELS_URL = (
    "https://api.pexels.com/v1/search"
)

IMAGE_QUERY = "steel rebar construction"


# =========================================================
# PUBLISH SETTINGS
# =========================================================

PUBLISH_HOUR = 15

PUBLISH_MINUTE = 0

# فقط 15:00 تا 15:09
PUBLISH_WINDOW_MINUTES = 10


# =========================================================
# EXPECTED REBAR SIZES
# =========================================================

ALLOWED_SIZES = {
    "12",
    "14",
    "16",
    "18",
    "20",
    "22",
    "25",
    "28",
    "32",
}


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
# NUMBER NORMALIZATION
# =========================================================

def normalize_number(value):

    if value is None:
        return ""

    text = str(value)

    persian = "۰۱۲۳۴۵۶۷۸۹"
    arabic = "٠١٢٣٤٥٦٧٨٩"

    for i, ch in enumerate(persian):
        text = text.replace(
            ch,
            str(i)
        )

    for i, ch in enumerate(arabic):
        text = text.replace(
            ch,
            str(i)
        )

    return text


# =========================================================
# CLEAN TEXT
# =========================================================

def clean_text(value):

    text = normalize_number(value)

    text = text.replace(
        "\u200c",
        " "
    )

    text = text.replace(
        "\n",
        " "
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# =========================================================
# EXTRACT SIZE
# =========================================================

def extract_size(text):

    text = clean_text(text)

    # -----------------------------------------------------
    # فقط سایزهای مجاز
    # -----------------------------------------------------

    matches = re.findall(
        r"\b(12|14|16|18|20|22|25|28|32)\b",
        text
    )

    for size in matches:

        if size in ALLOWED_SIZES:

            return size

    return None


# =========================================================
# EXTRACT PRICE
# =========================================================

def extract_price(value):

    if value is None:
        return None

    text = clean_text(value)

    if "تماس" in text:
        return None

    text = text.replace(
        "٬",
        ","
    )

    numbers = re.findall(
        r"\d[\d,]*",
        text
    )

    candidates = []

    for number in numbers:

        try:

            number_int = int(
                number.replace(
                    ",",
                    ""
                )
            )

            # قیمت میلگرد به تومان
            if number_int >= 10000:

                candidates.append(
                    number_int
                )

        except Exception:
            continue

    if not candidates:
        return None

    return candidates[-1]


# =========================================================
# DETECT KHORASAN / NEYSHABOUR
# =========================================================

def is_neyshabour_row(text):

    text = clean_text(text)

    keywords = [
        "نیشابور",
        "فولاد خراسان",
        "خراسان",
        "Khorasan",
        "Neyshabour",
        "Neyshabor",
    ]

    for keyword in keywords:

        if keyword.lower() in text.lower():

            return True

    return False


# =========================================================
# PARSE PIVAN
# =========================================================

def get_steel_prices():

    print(
        "======================================"
    )

    print(
        "GETTING REBAR PRICES"
    )

    print(
        "SOURCE:",
        SOURCE_URL
    )

    print(
        "======================================"
    )

    try:

        response = requests.get(
            SOURCE_URL,
            headers=HEADERS,
            timeout=TIMEOUT
        )

        response.raise_for_status()

    except Exception as e:

        print(
            "FETCH ERROR:",
            type(e).__name__,
            str(e)
        )

        return []


    # -----------------------------------------------------
    # READ HTML TABLES
    # -----------------------------------------------------

    try:

        tables = pd.read_html(
            StringIO(
                response.text
            )
        )

    except Exception as e:

        print(
            "TABLE ERROR:",
            type(e).__name__,
            str(e)
        )

        return []


    print(
        "Tables found:",
        len(tables)
    )


    prices = {}


    # =====================================================
    # PARSE ALL TABLES
    # =====================================================

    for table_index, df in enumerate(
        tables
    ):

        print(
            f"Checking table "
            f"{table_index + 1}: "
            f"{df.shape}"
        )


        for _, row in df.iterrows():

            values = [
                clean_text(x)
                for x in row.tolist()
            ]


            if not values:
                continue


            row_text = " | ".join(
                values
            )


            # -------------------------------------------------
            # فقط نیشابور
            # -------------------------------------------------

            size = extract_size(
                row_text
            )


            if size is None:
                continue


            # -------------------------------------------------
            # PRICE
            # -------------------------------------------------

            price = None


            for value in reversed(
                values
            ):

                candidate = extract_price(
                    value
                )


                if candidate is None:
                    continue


                price = candidate

                break


            if price is None:
                continue


            # -------------------------------------------------
            # DELIVERY
            # -------------------------------------------------

            delivery = "کارخانه"


            if (
                "تهران" in row_text
                and "کارخانه" not in row_text
            ):

                delivery = "تهران"


            # -------------------------------------------------
            # UNIT
            # -------------------------------------------------

            unit = "کیلوگرم"


            if "شاخه" in row_text:

                unit = "شاخه"

            elif "کیلو" in row_text:

                unit = "کیلوگرم"


            # -------------------------------------------------
            # SAVE
            # -------------------------------------------------

            if delivery != "کارخانه":

                continue


            prices[size] = {
                "size": size,
                "price": price,
                "delivery": delivery,
                "unit": unit,
            }


    # =====================================================
    # BUILD ORDERED RESULT
    # =====================================================

    results = []


    for size in sorted(
        ALLOWED_SIZES,
        key=lambda x: int(x)
    ):

        item = prices.get(
            size
        )


        if item is None:

            print(
                f"SIZE {size}: "
                "NOT FOUND"
            )

            continue


        results.append(
            item
        )


    print(
        "======================================"
    )

    print(
        "VALID REBAR SIZES:",
        len(results)
    )

    print(
        "======================================"
    )


    for item in results:

        print(
            f"Rebar {item['size']} | "
            f"{item['price']:,} | "
            f"{item['delivery']} | "
            f"{item['unit']}"
        )


    return results


# =========================================================
# HISTORY
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

            data = json.load(
                f
            )


        if isinstance(
            data,
            dict
        ):

            return data


    except Exception as e:

        print(
            "History load error:",
            type(e).__name__,
            str(e)
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
# PREVIOUS PRICE
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
# CHANGE
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
        (
            current - previous
        )
        / previous
    ) * 100


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

        return (
            f"🟢 +{value:.2f}%"
        )


    if value < 0:

        return (
            f"🔴 {value:.2f}%"
        )


    return "⚪ 0.00%"


# =========================================================
# PUBLISH TIME LOCK
# =========================================================

def check_publish_time(now):

    # -----------------------------------------------------
    # فقط ساعت 15
    # -----------------------------------------------------

    if now.hour != PUBLISH_HOUR:

        print(
            "TIME LOCK:"
        )

        print(
            "Current Iran time:",
            now.strftime(
                "%H:%M:%S"
            )
        )

        print(
            "Rebar is allowed only at 15:00 Iran time."
        )

        return False


    # -----------------------------------------------------
    # فقط 15:00 تا 15:09
    # -----------------------------------------------------

    if (
        now.minute < PUBLISH_MINUTE
        or now.minute >= (
            PUBLISH_MINUTE
            + PUBLISH_WINDOW_MINUTES
        )
    ):

        print(
            "TIME WINDOW LOCK"
        )

        return False


    return True


# =========================================================
# HOLIDAY LOCK
# =========================================================

def check_holiday(now):

    # -----------------------------------------------------
    # FRIDAY
    # -----------------------------------------------------

    if now.weekday() == 4:

        print(
            "HOLIDAY LOCK: FRIDAY"
        )

        print(
            "No rebar post today."
        )

        return False


    # -----------------------------------------------------
    # OFFICIAL HOLIDAY
    # -----------------------------------------------------

    try:

        holiday = is_non_working_day(
            now.date()
        )

    except Exception as e:

        print(
            "HOLIDAY CHECK ERROR:",
            type(e).__name__,
            str(e)
        )

        print(
            "FAIL SAFE: "
            "No rebar post."
        )

        return False


    if holiday:

        try:

            holiday_name = (
                get_holiday_name(
                    now.date()
                )
            )

        except Exception:

            holiday_name = None


        print(
            "HOLIDAY LOCK: "
            "OFFICIAL HOLIDAY"
        )


        if holiday_name:

            print(
                "Holiday:",
                holiday_name
            )


        return False


    return True


# =========================================================
# BUILD MESSAGE
# =========================================================

def build_message(
    current_prices,
    previous_prices
):

    now = datetime.now(
        TEHRAN
    )


    message_parts = [

        "🏗 <b>گزارش قیمت فولاد</b>",

        "",

        "📍 <b>میلگرد فولاد خراسان نیشابور</b>",

        "💰 قیمت‌ها به تومان",

        "",
    ]


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
            f"📊 تغییر: "
            f"{format_change(change)}"
        )


        message_parts.append("")


    message_parts.append(
        COMPANY_FOOTER
    )


    return "\n".join(
        message_parts
    )


# =========================================================
# GET IMAGE
# =========================================================

def get_steel_image(now):

    if not PEXELS_KEY:

        raise RuntimeError(
            "PEXELS_API_KEY is missing"
        )


    response = requests.get(

        PEXELS_URL,

        headers={
            "Authorization":
                PEXELS_KEY
        },

        params={
            "query":
                IMAGE_QUERY,

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

        raise RuntimeError(
            "No steel image found"
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


# =========================================================
# SEND TELEGRAM
# =========================================================

def send_telegram(
    image_url,
    message
):

    print(
        "Sending rebar post..."
    )

    print(
        "DESTINATION: PRIVATE CHAT"
    )


    response = requests.post(

        f"https://api.telegram.org/"
        f"bot{TOKEN}/sendPhoto",

        data={

            # =================================================
            # مهم:
            # میلگرد فقط به چت خصوصی ارسال می‌شود.
            # =================================================

            "chat_id":
                PRIVATE_CHAT_ID,

            "photo":
                image_url,

            "caption":
                message,

            "parse_mode":
                "HTML"
        },

        timeout=60
    )


    print(
        "Telegram status:",
        response.status_code
    )


    if not response.ok:

        print(
            response.text
        )

        return False


    return True


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
        "REBAR / STEEL BOT"
    )

    print(
        "Iran time:",
        now.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )

    print(
        "DESTINATION: PRIVATE CHAT"
    )

    print(
        "======================================"
    )


    # =====================================================
    # 1. TIME LOCK
    # =====================================================

    if not check_publish_time(
        now
    ):

        print(
            "BOT STOPPED BY TIME LOCK."
        )

        return


    # =====================================================
    # 2. HOLIDAY LOCK
    # =====================================================

    if not check_holiday(
        now
    ):

        print(
            "BOT STOPPED BY HOLIDAY LOCK."
        )

        return


    # =====================================================
    # 3. ENVIRONMENT
    # =====================================================

    missing = []


    if not TOKEN:

        missing.append(
            "BOT_TOKEN"
        )


    if not PRIVATE_CHAT_ID:

        missing.append(
            "PRIVATE_CHAT_ID"
        )


    if not PEXELS_KEY:

        missing.append(
            "PEXELS_API_KEY"
        )


    if missing:

        raise RuntimeError(
            "Missing environment variables: "
            + ", ".join(missing)
        )


    # =====================================================
    # 4. LOAD HISTORY
    # =====================================================

    history = load_history()


    previous_prices = (
        history.get(
            "last_steel_prices",
            {}
        )
    )


    # =====================================================
    # 5. GET PRICES
    # =====================================================

    results = get_steel_prices()


    if not results:

        raise RuntimeError(
            "No rebar prices found."
        )


    # =====================================================
    # 6. VALIDATE
    # =====================================================

    if len(results) < 1:

        raise RuntimeError(
            "No valid rebar prices."
        )


    # =====================================================
    # 7. CURRENT PRICES
    # =====================================================

    current_prices = {}


    for item in results:

        current_prices[
            str(item["size"])
        ] = item["price"]


    if not current_prices:

        raise RuntimeError(
            "Current rebar prices are empty."
        )


    # =====================================================
    # 8. FINAL TIME CHECK
    # =====================================================

    final_now = datetime.now(
        TEHRAN
    )


    if not check_publish_time(
        final_now
    ):

        print(
            "FINAL TIME LOCK."
        )

        return


    # =====================================================
    # 9. FINAL HOLIDAY CHECK
    # =====================================================

    if not check_holiday(
        final_now
    ):

        print(
            "FINAL HOLIDAY LOCK."
        )

        return


    # =====================================================
    # 10. BUILD MESSAGE
    # =====================================================

    message = build_message(
        current_prices,
        previous_prices
    )


    print(
        "======================================"
    )

    print(
        message
    )

    print(
        "======================================"
    )


    # =====================================================
    # 11. IMAGE
    # =====================================================

    image_url = get_steel_image(
        final_now
    )


    # =====================================================
    # 12. SEND
    # =====================================================

    success = send_telegram(
        image_url,
        message
    )


    if not success:

        raise RuntimeError(
            "Telegram private message failed."
        )


    # =====================================================
    # 13. SAVE HISTORY
    # =====================================================

    today_key = final_now.strftime(
        "%Y-%m-%d"
    )


    history[
        "last_steel_post_date"
    ] = today_key


    history[
        "last_steel_post_time"
    ] = final_now.strftime(
        "%Y-%m-%d %H:%M:%S"
    )


    history[
        "last_steel_prices"
    ] = current_prices


    save_history(
        history
    )


    # =====================================================
    # SUCCESS
    # =====================================================

    print(
        "======================================"
    )

    print(
        "REBAR PRIVATE MESSAGE SENT SUCCESSFULLY"
    )

    print(
        "SOURCE: PIVAN"
    )

    print(
        "DESTINATION: PRIVATE CHAT"
    )

    print(
        "TIME: 15:00 IRAN"
    )

    print(
        "======================================"
    )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    main()