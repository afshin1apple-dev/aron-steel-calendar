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

PRIVATE_CHAT_ID = os.environ.get(
    "PRIVATE_CHAT_ID"
)

TEHRAN = ZoneInfo(
    "Asia/Tehran"
)

STEEL_HISTORY_FILE = (
    "steel_history.json"
)

IMAGE_FILE = (
    "steel_price_card.jpg"
)

FONT_FILE = (
    "NotoSansArabic-Regular.ttf"
)

FONT_URL = (
    "https://github.com/googlefonts/noto-fonts/"
    "raw/main/hinted/ttf/NotoSansArabic/"
    "NotoSansArabic-Regular.ttf"
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
# PRICE FORMAT
# =========================================================

def format_price(value):

    if value is None:

        return "نامشخص"

    return f"{int(value):,}"


# =========================================================
# CALCULATE AVERAGE CHANGE
# =========================================================

def calculate_average_change(
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

        try:

            size = int(
                item["size"]
            )

            price = float(
                item["price"]
            )

            previous_map[size] = price

        except Exception:

            continue

    for item in current_prices:

        try:

            size = int(
                item["size"]
            )

            current = float(
                item["price"]
            )

            previous = previous_map.get(
                size
            )

            if (
                previous is None
                or previous == 0
            ):

                continue

            change = (
                (current - previous)
                / previous
            ) * 100

            changes.append(
                change
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
    current_prices,
    previous_prices
):

    change = calculate_average_change(
        current_prices,
        previous_prices
    )

    if change is None:

        return (
            "📊 <b>مقایسه با آخرین قیمت:</b>\n"
            "⚪ اطلاعات کافی برای مقایسه وجود ندارد."
        )

    if change > 0.01:

        return (
            "📊 <b>مقایسه با آخرین قیمت:</b>\n"
            f"🟢 قیمت میلگرد در مجموع "
            f"<b>{change:+.2f}٪ افزایش</b> داشته است."
        )

    if change < -0.01:

        return (
            "📊 <b>مقایسه با آخرین قیمت:</b>\n"
            f"🔴 قیمت میلگرد در مجموع "
            f"<b>{change:+.2f}٪ کاهش</b> داشته است."
        )

    return (
        "📊 <b>مقایسه با آخرین قیمت:</b>\n"
        "⚪ قیمت میلگرد در مجموع "
        "<b>بدون تغییر</b> بوده است."
    )


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
            e
        )

    return {}


# =========================================================
# SAVE HISTORY
# =========================================================

def save_history(
    history
):

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
# FONT
# =========================================================

def get_font(
    size
):

    if not os.path.exists(
        FONT_FILE
    ):

        print(
            "Downloading Persian font..."
        )

        response = requests.get(
            FONT_URL,
            timeout=30
        )

        response.raise_for_status()

        with open(
            FONT_FILE,
            "wb"
        ) as f:

            f.write(
                response.content
            )

    return ImageFont.truetype(
        FONT_FILE,
        size
    )


# =========================================================
# DOWNLOAD BACKGROUND
# =========================================================

def get_background():

    print(
        "Getting steel image..."
    )

    pexels_key = os.environ.get(
        "PEXELS_API_KEY"
    )

    if not pexels_key:

        raise RuntimeError(
            "PEXELS_API_KEY is missing"
        )

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

        raise RuntimeError(
            "No Pexels image found"
        )

    now = datetime.now(
        TEHRAN
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

    image_response = requests.get(
        image_url,
        timeout=30
    )

    image_response.raise_for_status()

    with open(
        IMAGE_FILE,
        "wb"
    ) as f:

        f.write(
            image_response.content
        )

    return Image.open(
        IMAGE_FILE
    ).convert(
        "RGB"
    )


# =========================================================
# CREATE PRICE IMAGE
# =========================================================

def create_price_image(
    factory_name,
    prices
):

    print(
        "Creating branded steel image..."
    )

    background = get_background()

    width = 1200
    height = 1500

    background = background.resize(
        (
            width,
            height
        )
    )

    image = background.copy()

    draw = ImageDraw.Draw(
        image,
        "RGBA"
    )

    # -----------------------------------------------------
    # Dark overlay
    # -----------------------------------------------------

    draw.rectangle(
        [
            0,
            0,
            width,
            height
        ],
        fill=(
            0,
            0,
            0,
            125
        )
    )

    # -----------------------------------------------------
    # Main panel
    # -----------------------------------------------------

    panel_x1 = 100
    panel_y1 = 100
    panel_x2 = width - 100
    panel_y2 = height - 100

    draw.rounded_rectangle(
        [
            panel_x1,
            panel_y1,
            panel_x2,
            panel_y2
        ],
        radius=40,
        fill=(
            255,
            255,
            255,
            235
        )
    )

    # -----------------------------------------------------
    # Fonts
    # -----------------------------------------------------

    title_font = get_font(
        54
    )

    subtitle_font = get_font(
        34
    )

    price_font = get_font(
        39
    )

    small_font = get_font(
        27
    )

    watermark_font = get_font(
        32
    )

    # -----------------------------------------------------
    # Header
    # -----------------------------------------------------

    title = (
        "🏗 " + factory_name
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
            145
        ),
        title,
        font=title_font,
        fill=(
            20,
            40,
            60,
            255
        )
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
            225
        ),
        subtitle,
        font=subtitle_font,
        fill=(
            80,
            80,
            80,
            255
        )
    )

    # -----------------------------------------------------
    # Price list - ONE COLUMN
    # -----------------------------------------------------

    y = 330

    for item in prices:

        size = item.get(
            "size"
        )

        value = item.get(
            "price"
        )

        text = (
            f"میلگرد {size}      "
            f"{format_price(value)} تومان"
        )

        draw.text(
            (
                220,
                y
            ),
            text,
            font=price_font,
            fill=(
                25,
                25,
                25,
                255
            )
        )

        draw.line(
            [
                200,
                y + 65,
                width - 200,
                y + 65
            ],
            fill=(
                190,
                190,
                190,
                180
            ),
            width=2
        )

        y += 115

    # -----------------------------------------------------
    # Unit
    # -----------------------------------------------------

    unit_text = (
        "💰 واحد قیمت: تومان"
    )

    draw.text(
        (
            220,
            y + 20
        ),
        unit_text,
        font=small_font,
        fill=(
            70,
            70,
            70,
            255
        )
    )

    # -----------------------------------------------------
    # MAIN BRAND
    # -----------------------------------------------------

    brand = (
        "@arvand_aron_steel"
    )

    bbox = draw.textbbox(
        (0, 0),
        brand,
        font=watermark_font
    )

    brand_width = (
        bbox[2] - bbox[0]
    )

    # -----------------------------------------------------
    # Bottom brand
    # -----------------------------------------------------

    draw.rounded_rectangle(
        [
            width - brand_width - 110,
            height - 145,
            width - 55,
            height - 70
        ],
        radius=20,
        fill=(
            0,
            0,
            0,
            145
        )
    )

    draw.text(
        (
            width - brand_width - 82,
            height - 130
        ),
        brand,
        font=watermark_font,
        fill=(
            255,
            255,
            255,
            235
        )
    )

    # -----------------------------------------------------
    # WATERMARKS
    # -----------------------------------------------------

    watermark = (
        "@arvand_aron_steel"
    )

    watermark_positions = [

        (120, 520),

        (500, 760),

        (170, 1000),

        (620, 1220)
    ]

    for x, y_pos in watermark_positions:

        draw.text(
            (
                x,
                y_pos
            ),
            watermark,
            font=watermark_font,
            fill=(
                255,
                255,
                255,
                45
            )
        )

    # -----------------------------------------------------
    # SAVE IMAGE
    # -----------------------------------------------------

    image.save(
        IMAGE_FILE,
        "JPEG",
        quality=95
    )

    print(
        "Branded image created:",
        IMAGE_FILE
    )

    return IMAGE_FILE


# =========================================================
# SEND PHOTO
# =========================================================

def send_photo(
    chat_id,
    image_file,
    caption
):

    if not chat_id:

        print(
            "Chat ID missing."
        )

        return False

    with open(
        image_file,
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
        "Telegram response:",
        response.text
    )

    return response.ok


# =========================================================
# SEND TEXT
# =========================================================

def send_message(
    chat_id,
    message
):

    if not chat_id:

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
        "Telegram text response:",
        response.text
    )

    return response.ok


# =========================================================
# BUILD CHANNEL CAPTION
# =========================================================

def build_caption(
    factory_name,
    prices,
    previous
):

    parts = [

        f"🏗 <b>{factory_name}</b>",

        "📌 <b>قیمت روز میلگرد</b>",

        "💰 واحد قیمت: تومان",

        ""
    ]

    for item in prices:

        size = item.get(
            "size"
        )

        value = item.get(
            "price"
        )

        parts.append(
            f"🔩 میلگرد {size}: "
            f"<b>{format_price(value)}</b> تومان"
        )

    parts.append("")

    parts.append(
        comparison_text(
            prices,
            previous
        )
    )

    parts.append("")

    parts.append(
        "📞 جهت اطلاع از قیمت سایر کارخانه‌ها "
        "با واحد فروش تماس حاصل نمایید."
    )

    parts.append(
        COMPANY_FOOTER
    )

    return "\n".join(
        parts
    )


# =========================================================
# SEND PRIVATE OTHER FACTORIES
# =========================================================

def send_private_prices(
    all_prices
):

    if not PRIVATE_CHAT_ID:

        print(
            "PRIVATE_CHAT_ID not configured."
        )

        return

    main_factories = {

        "نیشابور",
        "هیربد",
        "امیرکبیر"
    }

    parts = [

        "🔐 <b>قیمت سایر کارخانه‌ها</b>",

        ""
    ]

    found = False

    for key, data in all_prices.items():

        if key in main_factories:

            continue

        prices = data.get(
            "prices",
            []
        )

        if not prices:

            continue

        found = True

        parts.append(
            f"🏗 <b>{data['name']}</b>"
        )

        for item in prices:

            parts.append(
                f"میلگرد {item['size']}: "
                f"<b>{format_price(item['price'])}</b> تومان"
            )

        parts.append("")

    if not found:

        parts.append(
            "⚪ در حال حاضر قیمت کارخانه‌های دیگر دریافت نشد."
        )

    parts.append(
        COMPANY_FOOTER
    )

    success = send_message(
        PRIVATE_CHAT_ID,
        "\n".join(parts)
    )

    if success:

        print(
            "PRIVATE PRICE REPORT SENT SUCCESSFULLY"
        )

    else:

        print(
            "PRIVATE PRICE REPORT FAILED"
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

    if now.weekday() == 4:

        print(
            "Friday - no steel post."
        )

        return

    # -----------------------------------------------------
    # GET ALL PRICES
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
    # MAIN CHANNEL
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
                "Factory missing:",
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

        # -------------------------------------------------
        # CREATE BRANDED IMAGE
        # -------------------------------------------------

        image_file = create_price_image(
            factory_data["name"],
            prices
        )

        # -------------------------------------------------
        # CAPTION
        # -------------------------------------------------

        caption = build_caption(
            factory_data["name"],
            prices,
            previous
        )

        print()
        print(
            "Sending:",
            factory_data["name"]
        )

        success = send_photo(
            CHANNEL,
            image_file,
            caption
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
    # PRIVATE REPORT
    # -----------------------------------------------------

    send_private_prices(
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