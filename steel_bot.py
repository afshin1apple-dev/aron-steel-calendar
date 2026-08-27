import os
import json
import requests

from datetime import datetime
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw, ImageFont

from price import get_all_prices


# =========================================================
# SETTINGS
# =========================================================

TOKEN = os.environ["BOT_TOKEN"]

CHANNEL = os.environ["CHANNEL_ID"]

# آیدی عددی خصوصی افشین
PRIVATE_CHAT_ID = os.environ.get("PRIVATE_CHAT_ID")

TEHRAN = ZoneInfo("Asia/Tehran")

HISTORY_FILE = "steel_history.json"

IMAGE_FILE = "steel_market.png"


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
# FONT
# =========================================================

def get_font(size, bold=False):

    possible_fonts = []

    if bold:

        possible_fonts = [
            "/usr/share/fonts/truetype/noto/NotoSansArabic-Bold.ttf",
            "/usr/share/fonts/truetype/noto/NotoNaskhArabic-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]

    else:

        possible_fonts = [
            "/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf",
            "/usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]

    for path in possible_fonts:

        if os.path.exists(path):

            return ImageFont.truetype(
                path,
                size
            )

    return ImageFont.load_default()


# =========================================================
# PRICE FORMAT
# =========================================================

def format_price(value):

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
# COMPARISON
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

            size = int(
                item["size"]
            )

            old_price = float(
                item["price"]
            )

            previous_map[size] = old_price

        except Exception:

            continue


    changes = []


    for item in current:

        if item.get("price") is None:
            continue

        try:

            size = int(
                item["size"]
            )

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
                (
                    current_price
                    - old_price
                )
                / old_price
            ) * 100


            changes.append(
                percent
            )

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
            f"<b>{result:.2f}٪</b> کاهش داشته است."
        )


    return (
        "📊 <b>مقایسه با آخرین قیمت:</b>\n"
        "⚪ قیمت میلگرد در مجموع بدون تغییر بوده است."
    )


# =========================================================
# TEXT PRICE LIST
# =========================================================

def build_price_list(prices):

    if not prices:

        return "⚪ اطلاعات قیمت در دسترس نیست."


    valid_prices = [

        item

        for item in prices

        if item.get("price") is not None

    ]


    if not valid_prices:

        return "⚪ اطلاعات قیمت در دسترس نیست."


    lines = []


    for item in valid_prices:

        lines.append(

            f"▫️ سایز {item['size']}"
            f"   │   "
            f"{format_price(item['price'])} تومان"

        )


    return "\n".join(
        lines
    )


# =========================================================
# BUILD TELEGRAM TEXT
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

    )


    message += build_price_list(
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
# IMAGE - FACTORY PRICE CARD
# =========================================================

def create_price_image(
    factory_name,
    prices
):

    width = 1200

    row_height = 85

    header_height = 260

    footer_height = 120


    valid_prices = [

        item

        for item in prices

        if item.get("price") is not None

    ]


    height = (

        header_height
        + len(valid_prices) * row_height
        + footer_height

    )


    image = Image.new(
        "RGB",
        (width, height),
        "#F5F7FA"
    )


    draw = ImageDraw.Draw(
        image
    )


    # =====================================================
    # FONTS
    # =====================================================

    title_font = get_font(
        58,
        bold=True
    )

    subtitle_font = get_font(
        34,
        bold=True
    )

    header_font = get_font(
        30,
        bold=True
    )

    body_font = get_font(
        34,
        bold=False
    )

    price_font = get_font(
        36,
        bold=True
    )

    footer_font = get_font(
        26,
        bold=False
    )


    # =====================================================
    # HEADER
    # =====================================================

    draw.rectangle(
        [
            0,
            0,
            width,
            header_height
        ],
        fill="#172B4D"
    )


    title = (
        f"🏗 {factory_name}"
    )


    bbox = draw.textbbox(
        (0, 0),
        title,
        font=title_font
    )


    title_width = (
        bbox[2] - bbox[0]
    )


    draw.text(
        (
            (width - title_width) / 2,
            55
        ),
        title,
        font=title_font,
        fill="white"
    )


    subtitle = (
        "قیمت روز میلگرد"
    )


    bbox = draw.textbbox(
        (0, 0),
        subtitle,
        font=subtitle_font
    )


    subtitle_width = (
        bbox[2] - bbox[0]
    )


    draw.text(
        (
            (width - subtitle_width) / 2,
            145
        ),
        subtitle,
        font=subtitle_font,
        fill="white"
    )


    unit = (
        "واحد قیمت: تومان"
    )


    bbox = draw.textbbox(
        (0, 0),
        unit,
        font=header_font
    )


    unit_width = (
        bbox[2] - bbox[0]
    )


    draw.text(
        (
            (width - unit_width) / 2,
            200
        ),
        unit,
        font=header_font,
        fill="white"
    )


    # =====================================================
    # TABLE HEADER
    # =====================================================

    y = header_height


    draw.rectangle(
        [
            0,
            y,
            width,
            y + row_height
        ],
        fill="#DDE3EA"
    )


    draw.text(
        (
            170,
            y + 22
        ),
        "سایز",
        font=header_font,
        fill="#172B4D"
    )


    draw.text(
        (
            760,
            y + 22
        ),
        "قیمت",
        font=header_font,
        fill="#172B4D"
    )


    y += row_height


    # =====================================================
    # TABLE ROWS
    # =====================================================

    for index, item in enumerate(
        valid_prices
    ):

        if index % 2 == 0:

            fill = "#FFFFFF"

        else:

            fill = "#EEF2F6"


        draw.rectangle(
            [
                0,
                y,
                width,
                y + row_height
            ],
            fill=fill
        )


        # separator
        draw.line(
            [
                80,
                y + row_height,
                width - 80,
                y + row_height
            ],
            fill="#D0D5DB",
            width=2
        )


        size_text = (
            f"سایز {item['size']}"
        )


        price_text = (
            f"{format_price(item['price'])} تومان"
        )


        draw.text(
            (
                150,
                y + 20
            ),
            size_text,
            font=body_font,
            fill="#222222"
        )


        draw.text(
            (
                650,
                y + 17
            ),
            price_text,
            font=price_font,
            fill="#172B4D"
        )


        y += row_height


    # =====================================================
    # FOOTER
    # =====================================================

    draw.rectangle(
        [
            0,
            y,
            width,
            height
        ],
        fill="#172B4D"
    )


    footer_text = (
        "آروند آرون استیل  |  021-22122239"
    )


    bbox = draw.textbbox(
        (0, 0),
        footer_text,
        font=footer_font
    )


    footer_width = (
        bbox[2] - bbox[0]
    )


    draw.text(
        (
            (width - footer_width) / 2,
            y + 38
        ),
        footer_text,
        font=footer_font,
        fill="white"
    )


    image.save(
        IMAGE_FILE,
        quality=95
    )


    print(
        "Price image created:",
        IMAGE_FILE
    )


    return IMAGE_FILE


# =========================================================
# SEND TEXT MESSAGE
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
            "Telegram send error:",
            e
        )

        return False


# =========================================================
# SEND PHOTO
# =========================================================

def send_photo(
    chat_id,
    image_path,
    caption
):

    if not chat_id:

        print(
            "Chat ID not configured."
        )

        return False


    try:

        with open(
            image_path,
            "rb"
        ) as photo:

            response = requests.post(

                f"https://api.telegram.org/"
                f"bot{TOKEN}/sendPhoto",

                data={

                    "chat_id":
                        chat_id,

                    "caption":
                        caption,

                    "parse_mode":
                        "HTML"

                },

                files={

                    "photo":
                        photo

                },

                timeout=60
            )


        print(
            "Telegram photo response:",
            response.text
        )


        return response.ok


    except Exception as e:

        print(
            "Telegram photo error:",
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


    found = False


    for factory_key, factory_data in all_prices.items():

        if factory_key in MAIN_FACTORIES:

            continue


        prices = factory_data.get(
            "prices",
            []
        )


        if not prices:

            continue


        found = True


        message += (
            f"🏗 <b>"
            f"{factory_data.get('name', factory_key)}"
            f"</b>\n"
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
            "Steel posts will NOT be sent."
        )

        return


    # =====================================================
    # GET PRICES
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
    # MAIN CHANNEL POSTS
    # =====================================================

    for factory_key in MAIN_FACTORIES:

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


        factory_name = factory_data.get(
            "name",
            factory_key
        )


        # =================================================
        # TEXT
        # =================================================

        message = build_factory_post(

            factory_name,

            prices,

            previous

        )


        # =================================================
        # IMAGE
        # =================================================

        image_path = create_price_image(

            factory_name,

            prices

        )


        print()
        print(
            "Sending:",
            factory_name
        )


        # =================================================
        # SEND PHOTO + CAPTION
        # =================================================

        success = send_photo(

            CHANNEL,

            image_path,

            message

        )


        if success:

            print(
                "STEEL POST SENT SUCCESSFULLY:",
                factory_key
            )


            previous_factories[
                factory_key
            ] = prices


        else:

            print(
                "STEEL POST FAILED:",
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