import os
import re
import requests
import pandas as pd
from io import StringIO
from datetime import datetime
from zoneinfo import ZoneInfo
from PIL import Image, ImageDraw, ImageFont


# =========================================================
# SETTINGS
# =========================================================

TIMEOUT = 30

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0 Safari/537.36"
    )
}

TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL = os.environ.get("CHANNEL_ID")
PEXELS_KEY = os.environ.get("PEXELS_API_KEY")

TEHRAN = ZoneInfo("Asia/Tehran")

SOURCE_URL = (
    "https://pivan.co/brands/"
    "introduction-of-isfahan-steel-factory/"
    "iron-girder/"
)

IMAGE_FILE = "ipe_price_card.jpg"

FONT_FILE = "NotoSansArabic-Regular.ttf"

FONT_URL = (
    "https://github.com/googlefonts/noto-fonts/"
    "raw/main/hinted/ttf/NotoSansArabic/"
    "NotoSansArabic-Regular.ttf"
)

PEXELS_URL = "https://api.pexels.com/v1/search"


# =========================================================
# تعطیلات رسمی ایران
# =========================================================
#
# جمعه همیشه تعطیل است.
#
# علاوه بر جمعه، تعطیلات رسمی ایران نیز بررسی می‌شوند.
#
# برای جلوگیری از انتشار اشتباه، اگر API تقویم در دسترس
# نباشد، فقط قانون جمعه اجرا می‌شود.
#
# =========================================================

HOLIDAY_API_URL = (
    "https://holidayapi.ir/jalali"
)


def is_official_holiday(now):

    # -----------------------------------------------------
    # جمعه
    # -----------------------------------------------------

    if now.weekday() == 4:

        print(
            "HOLIDAY CHECK: Friday"
        )

        return True


    # -----------------------------------------------------
    # تاریخ شمسی امروز
    # -----------------------------------------------------

    try:

        from datetime import date

        # تبدیل میلادی به شمسی بدون وابستگی به کتابخانه
        # با استفاده از API تقویم

        response = requests.get(

            HOLIDAY_API_URL,

            params={
                "date":
                    now.strftime("%Y-%m-%d")
            },

            headers=HEADERS,

            timeout=10
        )

        if response.ok:

            data = response.json()

            # حالت‌های مختلف پاسخ API
            # بررسی چند ساختار متداول

            if isinstance(data, dict):

                if data.get("holiday") is True:

                    print(
                        "HOLIDAY CHECK: Official holiday"
                    )

                    return True

                if data.get("is_holiday") is True:

                    print(
                        "HOLIDAY CHECK: Official holiday"
                    )

                    return True

                if data.get("isHoliday") is True:

                    print(
                        "HOLIDAY CHECK: Official holiday"
                    )

                    return True

    except Exception as e:

        print(
            "Holiday API error:",
            type(e).__name__,
            str(e)
        )


    # -----------------------------------------------------
    # اگر API در دسترس نبود
    # -----------------------------------------------------

    print(
        "HOLIDAY CHECK: Normal working day"
    )

    return False


# =========================================================
# IPE SIZES
# =========================================================

ALLOWED_SIZES = {
    "12",
    "14",
    "16",
    "18",
    "20",
    "22",
    "24",
    "27",
    "30",
}


# =========================================================
# NUMBER
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

    text = normalize_number(
        value
    )

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
# EXTRACT PRICE
# =========================================================

def extract_price(value):

    if value is None:

        return None

    text = clean_text(
        value
    )

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

            value_int = int(
                number.replace(
                    ",",
                    ""
                )
            )

            if value_int >= 10000:

                candidates.append(
                    value_int
                )

        except Exception:

            continue

    if not candidates:

        return None

    return candidates[-1]


# =========================================================
# EXTRACT SIZE
# =========================================================

def extract_size(text):

    text = clean_text(
        text
    )

    patterns = [

        r"IPE\s*(\d{2})",

        r"تیرآهن\s*(\d{2})",

        r"\b(\d{2})\b",

    ]

    for pattern in patterns:

        match = re.search(

            pattern,

            text,

            re.IGNORECASE
        )

        if not match:

            continue

        size = match.group(1)

        if size in ALLOWED_SIZES:

            return size

    return None


# =========================================================
# DELIVERY
# =========================================================

def detect_delivery(text):

    text = clean_text(
        text
    )

    if "کارخانه" in text:

        return "کارخانه"

    if (
        "تهران" in text
        or "انبار" in text
    ):

        return "تهران"

    return None


# =========================================================
# UNIT
# =========================================================

def detect_unit(text):

    text = clean_text(
        text
    )

    if "کیلوگرم" in text:

        return "کیلوگرم"

    if "کیلو" in text:

        return "کیلوگرم"

    if "شاخه" in text:

        return "شاخه"

    return None


# =========================================================
# PARSE
# =========================================================

def parse_ipe_prices():

    print(
        "Getting IPE prices..."
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
        f"Tables found: {len(tables)}"
    )

    factory = {}

    tehran = {}

    for table_index, df in enumerate(
        tables
    ):

        print(
            f"Checking table {table_index + 1}: "
            f"{df.shape}"
        )

        for _, row in df.iterrows():

            values = [

                clean_text(x)

                for x in row.tolist()

            ]

            if len(values) < 4:

                continue

            row_text = " | ".join(
                values
            )

            size = extract_size(
                row_text
            )

            if size is None:

                continue

            delivery = detect_delivery(
                row_text
            )

            if delivery is None:

                continue

            unit = detect_unit(
                row_text
            )

            if unit is None:

                continue

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

            item = {

                "size":
                    size,

                "delivery":
                    delivery,

                "unit":
                    unit,

                "price":
                    price,

            }

            if delivery == "کارخانه":

                factory[size] = item

            elif delivery == "تهران":

                tehran[size] = item

    results = []

    for size in sorted(

        ALLOWED_SIZES,

        key=lambda x: int(x)

    ):

        results.append({

            "size":
                size,

            "factory":
                factory.get(size),

            "tehran":
                tehran.get(size),

        })

    return results


# =========================================================
# FONT
# =========================================================

def get_font(size):

    if not os.path.exists(
        FONT_FILE
    ):

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
# BACKGROUND
# =========================================================

def get_background():

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
                "steel beam construction",

            "orientation":
                "landscape",

            "per_page":
                20,

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
# IMAGE
# =========================================================

def create_price_image(results):

    background = get_background()

    width = 1200

    height = 1600

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
    # DARK OVERLAY
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
            130
        )
    )

    # -----------------------------------------------------
    # PANEL
    # -----------------------------------------------------

    draw.rounded_rectangle(

        [
            60,
            60,
            width - 60,
            height - 60
        ],

        radius=40,

        fill=(
            255,
            255,
            255,
            238
        )
    )

    # -----------------------------------------------------
    # FONTS
    # -----------------------------------------------------

    title_font = get_font(52)

    subtitle_font = get_font(31)

    header_font = get_font(29)

    row_font = get_font(27)

    watermark_font = get_font(29)

    footer_font = get_font(25)

    # -----------------------------------------------------
    # TITLE
    # -----------------------------------------------------

    title = (
        "🏗 تیرآهن ذوب‌آهن اصفهان"
    )

    bbox = draw.textbbox(

        (0, 0),

        title,

        font=title_font
    )

    title_width = (
        bbox[2] -
        bbox[0]
    )

    draw.text(

        (
            (width - title_width) / 2,
            105
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

    # -----------------------------------------------------
    # SUBTITLE
    # -----------------------------------------------------

    subtitle = (
        "قیمت روز تیرآهن IPE"
    )

    bbox = draw.textbbox(

        (0, 0),

        subtitle,

        font=subtitle_font
    )

    subtitle_width = (
        bbox[2] -
        bbox[0]
    )

    draw.text(

        (
            (width - subtitle_width) / 2,
            180
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
    # TABLE HEADER
    # -----------------------------------------------------

    y = 270

    draw.rounded_rectangle(

        [
            110,
            y,
            width - 110,
            y + 70
        ],

        radius=15,

        fill=(
            35,
            55,
            70,
            255
        )
    )

    draw.text(

        (175, y + 18),

        "سایز",

        font=header_font,

        fill=(
            255,
            255,
            255,
            255
        )
    )

    draw.text(

        (430, y + 18),

        "کارخانه / کیلو",

        font=header_font,

        fill=(
            255,
            255,
            255,
            255
        )
    )

    draw.text(

        (800, y + 18),

        "تهران / شاخه",

        font=header_font,

        fill=(
            255,
            255,
            255,
            255
        )
    )

    y += 85

    # -----------------------------------------------------
    # ROWS
    # -----------------------------------------------------

    for result in results:

        size = result["size"]

        factory = result["factory"]

        tehran = result["tehran"]

        factory_price = (

            f"{factory['price']:,}"

            if factory

            else "نامشخص"
        )

        tehran_price = (

            f"{tehran['price']:,}"

            if tehran

            else "نامشخص"
        )

        draw.text(

            (175, y),

            f"IPE {size}",

            font=row_font,

            fill=(
                25,
                25,
                25,
                255
            )
        )

        draw.text(

            (430, y),

            factory_price,

            font=row_font,

            fill=(
                25,
                25,
                25,
                255
            )
        )

        draw.text(

            (800, y),

            tehran_price,

            font=row_font,

            fill=(
                25,
                25,
                25,
                255
            )
        )

        draw.line(

            [
                140,
                y + 55,
                width - 140,
                y + 55
            ],

            fill=(
                190,
                190,
                190,
                180
            ),

            width=2
        )

        y += 105

    # -----------------------------------------------------
    # FOOTER
    # -----------------------------------------------------

    draw.text(

        (150, y + 10),

        "💰 کارخانه: تومان / کیلوگرم",

        font=footer_font,

        fill=(
            70,
            70,
            70,
            255
        )
    )

    draw.text(

        (150, y + 55),

        "🏙 تهران: تومان / شاخه",

        font=footer_font,

        fill=(
            70,
            70,
            70,
            255
        )
    )

    # -----------------------------------------------------
    # WATERMARK
    # -----------------------------------------------------

    watermark = (
        "@arvand_aron_steel"
    )

    bbox = draw.textbbox(

        (0, 0),

        watermark,

        font=watermark_font
    )

    watermark_width = (
        bbox[2] -
        bbox[0]
    )

    draw.rounded_rectangle(

        [
            width - watermark_width - 105,
            height - 135,
            width - 45,
            height - 65
        ],

        radius=18,

        fill=(
            0,
            0,
            0,
            150
        )
    )

    draw.text(

        (
            width - watermark_width - 78,
            height - 122
        ),

        watermark,

        font=watermark_font,

        fill=(
            255,
            255,
            255,
            235
        )
    )

    # -----------------------------------------------------
    # SAVE
    # -----------------------------------------------------

    image.save(

        IMAGE_FILE,

        "JPEG",

        quality=95
    )

    return IMAGE_FILE


# =========================================================
# CAPTION
# =========================================================

def build_caption(results):

    now = datetime.now(
        TEHRAN
    )

    parts = [

        "🏗 <b>تیرآهن ذوب‌آهن اصفهان</b>",

        "📌 <b>قیمت روز تیرآهن IPE</b>",

        (
            f"📅 {now.strftime('%Y/%m/%d')} "
            f"⏰ {now.strftime('%H:%M')}"
        ),

        "",
    ]

    for result in results:

        size = result["size"]

        factory = result["factory"]

        tehran = result["tehran"]

        factory_price = (

            f"{factory['price']:,}"

            if factory

            else "نامشخص"
        )

        tehran_price = (

            f"{tehran['price']:,}"

            if tehran

            else "نامشخص"
        )

        parts.append(

            f"🔩 <b>IPE {size}</b>"
        )

        parts.append(

            f"🏭 کارخانه: "
            f"<b>{factory_price}</b> تومان/کیلو"
        )

        parts.append(

            f"🏙 تهران: "
            f"<b>{tehran_price}</b> تومان/شاخه"
        )

        parts.append("")

    parts.extend([

        "📞 جهت اطلاع از قیمت سایر محصولات "
        "با واحد فروش تماس حاصل نمایید.",

        "",

        "━━━━━━━━━━━━━━",

        "🏭 آروند آرون استیل",

        "👤 مدیریت: افشین آورزمانی",

        "📞 021-22122239",

        "🆔 @arvand_aron_steel",

    ])

    return "\n".join(parts)


# =========================================================
# SEND PHOTO
# =========================================================

def send_photo(

    image_file,

    caption

):

    if not TOKEN:

        print(
            "ERROR: BOT_TOKEN missing"
        )

        return False

    if not CHANNEL:

        print(
            "ERROR: CHANNEL_ID missing"
        )

        return False

    try:

        with open(

            image_file,

            "rb"

        ) as photo:

            response = requests.post(

                f"https://api.telegram.org/"
                f"bot{TOKEN}/sendPhoto",

                data={

                    "chat_id":
                        CHANNEL,

                    "caption":
                        caption,

                    "parse_mode":
                        "HTML",

                },

                files={

                    "photo":
                        photo

                },

                timeout=60
            )

        if response.ok:

            return True

        print(

            "TELEGRAM ERROR:",

            response.text
        )

        return False

    except Exception as e:

        print(

            "SEND ERROR:",

            type(e).__name__,

            str(e)
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
        "========================================"
    )

    print(
        "IPE CHANNEL"
    )

    print(
        "Iran time:",
        now.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )

    print(
        "========================================"
    )

    # -----------------------------------------------------
    # FRIDAY + OFFICIAL HOLIDAY LOCK
    # -----------------------------------------------------

    if is_official_holiday(now):

        print(
            "========================================"
        )

        print(
            "HOLIDAY: IPE POST DISABLED"
        )

        print(
            "No price will be published today."
        )

        print(
            "========================================"
        )

        return

    # -----------------------------------------------------
    # ENV
    # -----------------------------------------------------

    missing = []

    if not TOKEN:

        missing.append(
            "BOT_TOKEN"
        )

    if not CHANNEL:

        missing.append(
            "CHANNEL_ID"
        )

    if not PEXELS_KEY:

        missing.append(
            "PEXELS_API_KEY"
        )

    if missing:

        print(

            "ERROR: missing environment variables:",

            ", ".join(missing)
        )

        return

    # -----------------------------------------------------
    # GET PRICES
    # -----------------------------------------------------

    results = parse_ipe_prices()

    valid = [

        x

        for x in results

        if x["factory"]
        or x["tehran"]

    ]

    print(

        f"VALID SIZES: {len(valid)}"
    )

    if len(valid) != 9:

        print(
            "ERROR: Expected 9 IPE sizes."
        )

        return

    # -----------------------------------------------------
    # PRINT
    # -----------------------------------------------------

    for item in valid:

        size = item["size"]

        factory = item["factory"]

        tehran = item["tehran"]

        print(

            f"IPE {size} | "

            f"FACTORY: "

            f"{factory['price'] if factory else 'N/A'} | "

            f"TEHRAN: "

            f"{tehran['price'] if tehran else 'N/A'}"

        )

    # -----------------------------------------------------
    # IMAGE
    # -----------------------------------------------------

    print(
        "Creating price image..."
    )

    try:

        image_file = create_price_image(
            valid
        )

    except Exception as e:

        print(

            "IMAGE ERROR:",

            type(e).__name__,

            str(e)
        )

        return

    # -----------------------------------------------------
    # CAPTION
    # -----------------------------------------------------

    caption = build_caption(
        valid
    )

    # -----------------------------------------------------
    # SEND
    # -----------------------------------------------------

    print(
        "Sending to channel..."
    )

    success = send_photo(

        image_file,

        caption
    )

    # -----------------------------------------------------
    # FINAL
    # -----------------------------------------------------

    print(
        "========================================"
    )

    if success:

        print(
            "CHANNEL: SUCCESS"
        )

    else:

        print(
            "CHANNEL: FAILED"
        )

    print(
        "========================================"
    )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    main()