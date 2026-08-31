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
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/125.0 Safari/537.36"
    ),
    "Accept-Language": "fa-IR,fa;q=0.9,en;q=0.8",
}

TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL = os.environ.get("CHANNEL_ID")
PEXELS_KEY = os.environ.get("PEXELS_API_KEY")

TEHRAN = ZoneInfo("Asia/Tehran")


# =========================================================
# SOURCE
# =========================================================
#
# آهن ملل
# صفحه اختصاصی قیمت نبشی ناب تبریز
# =========================================================

SOURCE_URL = (
    "https://ahanmelal.com/"
    "steel-t-bars-studs-angles/"
    "steel-angle-price/"
    "nab-tabriz-angle"
)


IMAGE_FILE = "angle_price_card.jpg"

FONT_FILE = "NotoSansArabic-Regular.ttf"

FONT_URL = (
    "https://github.com/googlefonts/noto-fonts/"
    "raw/main/hinted/ttf/NotoSansArabic/"
    "NotoSansArabic-Regular.ttf"
)

PEXELS_URL = "https://api.pexels.com/v1/search"


# =========================================================
# PUBLISH SETTINGS
# =========================================================

PUBLISH_HOUR = 14


# =========================================================
# OFFICIAL HOLIDAYS 1405
# =========================================================

OFFICIAL_HOLIDAYS_1405 = {
    "1405/01/01",
    "1405/01/02",
    "1405/01/03",
    "1405/01/04",
    "1405/01/12",
    "1405/01/13",
    "1405/01/25",
    "1405/02/04",
    "1405/02/14",
    "1405/02/24",
    "1405/03/06",
    "1405/03/14",
    "1405/03/15",
    "1405/03/24",
    "1405/04/14",
    "1405/04/15",
    "1405/04/25",
    "1405/05/02",
    "1405/05/12",
    "1405/05/22",
    "1405/06/02",
    "1405/06/11",
    "1405/06/12",
    "1405/06/20",
    "1405/06/31",
    "1405/07/01",
    "1405/07/10",
    "1405/07/19",
    "1405/08/03",
    "1405/08/13",
    "1405/08/22",
    "1405/09/03",
    "1405/09/04",
    "1405/09/13",
    "1405/09/14",
    "1405/09/22",
    "1405/10/02",
    "1405/10/13",
    "1405/10/22",
    "1405/11/05",
    "1405/11/22",
    "1405/12/29",
}


# =========================================================
# HOLIDAY CHECK
# =========================================================

def is_official_holiday(now):

    # -----------------------------------------------------
    # FRIDAY
    # -----------------------------------------------------

    if now.weekday() == 4:

        print(
            "HOLIDAY: FRIDAY"
        )

        return True


    # -----------------------------------------------------
    # OFFICIAL HOLIDAY
    # -----------------------------------------------------

    try:

        from persiantools.jdatetime import JalaliDate

        jalali = JalaliDate(
            now.date()
        )

        date_string = (
            f"{jalali.year:04d}/"
            f"{jalali.month:02d}/"
            f"{jalali.day:02d}"
        )

        if date_string in OFFICIAL_HOLIDAYS_1405:

            print(
                "HOLIDAY: OFFICIAL"
            )

            print(
                "DATE:",
                date_string
            )

            return True

    except Exception as e:

        print(
            "Holiday check error:",
            type(e).__name__,
            str(e)
        )

        # -------------------------------------------------
        # FAIL SAFE
        # -------------------------------------------------

        return True


    return False


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

    text = text.replace(
        "\xa0",
        " "
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# =========================================================
# PRICE
# =========================================================

def extract_price(value):

    if value is None:

        return None

    text = clean_text(
        value
    )

    if not text:

        return None

    # -----------------------------------------------------
    # CONTACT PRICE
    # -----------------------------------------------------

    if (
        "تماس" in text
        or "استعلام" in text
    ):

        return None


    # -----------------------------------------------------
    # SEPARATORS
    # -----------------------------------------------------

    text = text.replace(
        "٬",
        ","
    )

    text = text.replace(
        "،",
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

            # -------------------------------------------------
            # قیمت نبشی به تومان / کیلو
            # -------------------------------------------------

            if (
                10000
                <= number_int
                <= 1000000
            ):

                candidates.append(
                    number_int
                )

        except Exception:

            continue


    if not candidates:

        return None


    return candidates[-1]


# =========================================================
# ANGLE SIZE
# =========================================================

def extract_size(value):

    text = clean_text(
        value
    )


    # -----------------------------------------------------
    # 40*40
    # 40×40
    # 40 x 40
    # -----------------------------------------------------

    match = re.search(
        r"(\d{2,3})\s*"
        r"[*×xX]\s*"
        r"(\d{2,3})",
        text
    )


    if not match:

        return None


    return (
        f"{match.group(1)}x"
        f"{match.group(2)}"
    )


# =========================================================
# THICKNESS
# =========================================================

def extract_thickness(value):

    text = clean_text(
        value
    )


    match = re.search(
        r"(\d+(?:[./]\d+)?)",
        text
    )


    if not match:

        return None


    return match.group(1)


# =========================================================
# PARSE ANGLE PRICES
# =========================================================

def parse_angle_prices():

    print(
        "========================================"
    )

    print(
        "Getting ANGLE prices..."
    )

    print(
        "SOURCE: AHANMELAL"
    )

    print(
        SOURCE_URL
    )

    print(
        "========================================"
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


    print(
        "HTTP STATUS:",
        response.status_code
    )


    # =====================================================
    # READ TABLES
    # =====================================================

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


    results = []


    # =====================================================
    # TABLE SCAN
    # =====================================================

    for table_index, df in enumerate(
        tables
    ):

        print(
            f"Checking table {table_index + 1}: "
            f"{df.shape}"
        )


        # -------------------------------------------------
        # COLUMN DETECTION
        # -------------------------------------------------

        columns = [
            clean_text(col)
            for col in df.columns
        ]


        print(
            "Columns:",
            columns
        )


        for _, row in df.iterrows():

            values = [
                clean_text(x)
                for x in row.tolist()
            ]


            if len(values) < 5:

                continue


            row_text = " | ".join(
                values
            )


            # =================================================
            # ONLY NAB TABRIZ
            # =================================================

            if "ناب تبریز" not in row_text:

                continue


            if "نبشی" not in row_text:

                continue


            # =================================================
            # SIZE
            # =================================================

            size = extract_size(
                row_text
            )


            if size is None:

                continue


            # =================================================
            # THICKNESS
            # =================================================

            thickness = None


            # از ستون دوم/مقادیر عددی کوچک استفاده می‌کنیم
            for value in values:

                clean = clean_text(
                    value
                )


                if not re.fullmatch(
                    r"\d+(?:[./]\d+)?",
                    clean
                ):

                    continue


                try:

                    number = float(
                        clean.replace(
                            "/",
                            "."
                        )
                    )


                    if (
                        1
                        <= number
                        <= 20
                    ):

                        thickness = clean

                        break

                except Exception:

                    continue


            if thickness is None:

                continue


            # =================================================
            # LENGTH
            # =================================================

            length = None


            for value in values:

                clean = clean_text(
                    value
                )


                if clean in {
                    "6",
                    "12",
                    "6.0",
                    "12.0",
                }:

                    length = clean

                    break


            # =================================================
            # DELIVERY
            # =================================================

            delivery = "کارخانه"


            if (
                "کارخانه تبریز" in row_text
                or "کارخانه" in row_text
            ):

                delivery = "کارخانه"


            # =================================================
            # UNIT
            # =================================================

            unit = "کیلوگرم"


            if "کیلوگرم" not in row_text:

                # صفحه اختصاصی آهن ملل
                # برای این جدول واحد کیلوگرم است.
                unit = "کیلوگرم"


            # =================================================
            # WEIGHT
            # =================================================

            weight = None


            for value in values:

                clean = clean_text(
                    value
                )


                # وزن واحد نبشی
                # معمولاً بین 5 تا 300 کیلو
                try:

                    number = float(
                        clean.replace(
                            ",",
                            ""
                        )
                    )


                    if (
                        5
                        <= number
                        <= 300
                    ):

                        # سایز/ضخامت/طول
                        # نباید به عنوان وزن برداشته شود.
                        if clean not in {
                            "6",
                            "12",
                            thickness,
                            "3",
                            "4",
                            "5",
                            "6",
                            "7",
                            "8",
                            "9",
                            "10",
                            "11",
                            "12",
                        }:

                            weight = number

                            break

                except Exception:

                    continue


            # =================================================
            # PRICE
            # =================================================

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


            # =================================================
            # ITEM
            # =================================================

            item = {

                "size":
                    size,

                "thickness":
                    thickness,

                "length":
                    length,

                "delivery":
                    delivery,

                "weight":
                    weight,

                "unit":
                    unit,

                "price":
                    price,
            }


            results.append(
                item
            )


    # =====================================================
    # REMOVE DUPLICATES
    # =====================================================

    unique = {}


    for item in results:

        key = (

            item["size"],

            item["thickness"],

            item["length"],

            item["delivery"],

        )


        unique[key] = item


    results = list(
        unique.values()
    )


    # =====================================================
    # SORT
    # =====================================================

    def sort_key(item):

        size = item["size"]

        match = re.match(
            r"(\d+)x(\d+)",
            size
        )


        if match:

            return (
                int(match.group(1)),
                int(match.group(2)),
                float(
                    item["thickness"]
                    .replace(
                        "/",
                        "."
                    )
                )
            )


        return (
            999,
            999,
            999
        )


    results.sort(
        key=sort_key
    )


    # =====================================================
    # DEBUG
    # =====================================================

    print(
        "========================================"
    )

    print(
        f"VALID ANGLE PRODUCTS: {len(results)}"
    )

    print(
        "========================================"
    )


    for item in results:

        print(
            f"{item['size']} | "
            f"Thickness: {item['thickness']} | "
            f"Length: {item['length']} | "
            f"Delivery: {item['delivery']} | "
            f"Weight: {item['weight']} | "
            f"Price: {item['price']:,}"
        )


    print(
        "========================================"
    )


    return results


# =========================================================
# FONT
# =========================================================

def get_font(size):

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
                "steel angle construction",

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
# CREATE PRICE IMAGE
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


    # =====================================================
    # DARK OVERLAY
    # =====================================================

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


    # =====================================================
    # PANEL
    # =====================================================

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


    # =====================================================
    # FONTS
    # =====================================================

    title_font = get_font(52)

    subtitle_font = get_font(32)

    header_font = get_font(27)

    row_font = get_font(26)

    footer_font = get_font(25)

    watermark_font = get_font(29)


    # =====================================================
    # TITLE
    # =====================================================

    title = "📐 نبشی ناب تبریز"


    bbox = draw.textbbox(
        (0, 0),
        title,
        font=title_font
    )


    title_width = (
        bbox[2]
        -
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


    # =====================================================
    # SUBTITLE
    # =====================================================

    subtitle = "قیمت روز نبشی"


    bbox = draw.textbbox(
        (0, 0),
        subtitle,
        font=subtitle_font
    )


    subtitle_width = (
        bbox[2]
        -
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


    # =====================================================
    # HEADER
    # =====================================================

    y = 270


    draw.rounded_rectangle(
        [
            100,
            y,
            width - 100,
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
        (145, y + 18),
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
        (390, y + 18),
        "ضخامت",
        font=header_font,
        fill=(
            255,
            255,
            255,
            255
        )
    )


    draw.text(
        (600, y + 18),
        "تحویل",
        font=header_font,
        fill=(
            255,
            255,
            255,
            255
        )
    )


    draw.text(
        (850, y + 18),
        "قیمت",
        font=header_font,
        fill=(
            255,
            255,
            255,
            255
        )
    )


    y += 90


    # =====================================================
    # ROWS
    # =====================================================

    for item in results:

        draw.text(
            (145, y),
            item["size"],
            font=row_font,
            fill=(
                25,
                25,
                25,
                255
            )
        )


        draw.text(
            (390, y),
            item["thickness"],
            font=row_font,
            fill=(
                25,
                25,
                25,
                255
            )
        )


        draw.text(
            (600, y),
            item["delivery"],
            font=row_font,
            fill=(
                25,
                25,
                25,
                255
            )
        )


        draw.text(
            (850, y),
            f"{item['price']:,}",
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
                120,
                y + 58,
                width - 120,
                y + 58
            ],
            fill=(
                190,
                190,
                190,
                180
            ),
            width=2
        )


        y += 90


        if y > height - 250:

            break


    # =====================================================
    # FOOTER
    # =====================================================

    draw.text(
        (
            150,
            height - 230
        ),
        "💰 قیمت: تومان / کیلوگرم",
        font=footer_font,
        fill=(
            70,
            70,
            70,
            255
        )
    )


    # =====================================================
    # WATERMARK
    # =====================================================

    watermark = (
        "@arvand_aron_steel"
    )


    bbox = draw.textbbox(
        (0, 0),
        watermark,
        font=watermark_font
    )


    watermark_width = (
        bbox[2]
        -
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


    # =====================================================
    # SAVE
    # =====================================================

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

        "📐 <b>نبشی ناب تبریز</b>",

        "📌 <b>قیمت روز نبشی</b>",

        (
            f"📅 {now.strftime('%Y/%m/%d')} "
            f"⏰ {now.strftime('%H:%M')}"
        ),

        "💰 واحد قیمت: تومان / کیلوگرم",

        "",
    ]


    for item in results:

        parts.append(
            f"🔩 <b>{item['size']}</b> "
            f"ضخامت {item['thickness']}"
        )


        parts.append(
            f"🏭 {item['delivery']}: "
            f"<b>{item['price']:,}</b> تومان/کیلو"
        )


        parts.append("")


    parts.extend(
        [

            "📞 جهت اطلاع از قیمت سایر محصولات "
            "با واحد فروش تماس حاصل نمایید.",

            "",

            "━━━━━━━━━━━━━━",

            "🏭 آروند آرون استیل",

            "👤 مدیریت: افشین آورزمانی",

            "📞 021-22122239",

            "🆔 @arvand_aron_steel",

        ]
    )


    return "\n".join(
        parts
    )


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


        print(
            "Telegram status:",
            response.status_code
        )


        if not response.ok:

            print(
                "TELEGRAM ERROR:",
                response.text
            )


        return response.ok


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
        "ANGLE PRICE BOT"
    )

    print(
        "SOURCE: AHANMELAL"
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


    # =====================================================
    # TIME LOCK
    # =====================================================
    #
    # فقط ساعت 14
    # =====================================================

    if now.hour != PUBLISH_HOUR:

        print(
            "TIME LOCK:"
        )

        print(
            "ANGLE is allowed only at 14:00 Iran time."
        )

        return


    # =====================================================
    # MINUTE LOCK
    # =====================================================

    if now.minute > 9:

        print(
            "TIME LOCK:"
        )

        print(
            "ANGLE publication window has passed."
        )

        return


    # =====================================================
    # HOLIDAY LOCK
    # =====================================================

    if is_official_holiday(
        now
    ):

        print(
            "ANGLE BOT STOPPED BY HOLIDAY LOCK."
        )

        return


    # =====================================================
    # ENVIRONMENT
    # =====================================================

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


    # =====================================================
    # GET PRICES
    # =====================================================

    results = parse_angle_prices()


    if not results:

        print(
            "ERROR: No valid angle prices found."
        )

        return


    # =====================================================
    # CREATE IMAGE
    # =====================================================

    print(
        "Creating price image..."
    )


    try:

        image_file = create_price_image(
            results
        )

    except Exception as e:

        print(
            "IMAGE ERROR:",
            type(e).__name__,
            str(e)
        )

        return


    # =====================================================
    # CAPTION
    # =====================================================

    caption = build_caption(
        results
    )


    # =====================================================
    # FINAL TIME CHECK
    # =====================================================

    final_now = datetime.now(
        TEHRAN
    )


    if final_now.hour != PUBLISH_HOUR:

        print(
            "FINAL TIME LOCK."
        )

        return


    if final_now.minute > 9:

        print(
            "FINAL TIME LOCK: window passed."
        )

        return


    # =====================================================
    # FINAL HOLIDAY CHECK
    # =====================================================

    if is_official_holiday(
        final_now
    ):

        print(
            "FINAL HOLIDAY LOCK."
        )

        return


    # =====================================================
    # SEND
    # =====================================================

    print(
        "Sending to channel..."
    )


    success = send_photo(
        image_file,
        caption
    )


    # =====================================================
    # FINAL
    # =====================================================

    print(
        "========================================"
    )


    if success:

        print(
            "ANGLE CHANNEL: SUCCESS"
        )

    else:

        print(
            "ANGLE CHANNEL: FAILED"
        )


    print(
        "========================================"
    )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    main()