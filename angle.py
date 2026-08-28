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
    "tabriz-pure-steel/angel/"
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
# NUMBER
# =========================================================

def normalize_number(value):

    if value is None:
        return ""

    text = str(value)

    persian = "۰۱۲۳۴۵۶۷۸۹"
    arabic = "٠١٢٣٤٥٦٧٨٩"

    for i, ch in enumerate(persian):
        text = text.replace(ch, str(i))

    for i, ch in enumerate(arabic):
        text = text.replace(ch, str(i))

    return text


# =========================================================
# CLEAN
# =========================================================

def clean_text(value):

    text = normalize_number(value)

    text = text.replace("\u200c", " ")
    text = text.replace("\n", " ")

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

    text = clean_text(value)

    if "تماس" in text:
        return None

    text = text.replace("٬", ",")

    numbers = re.findall(
        r"\d[\d,]*",
        text
    )

    candidates = []

    for number in numbers:

        try:

            number_int = int(
                number.replace(",", "")
            )

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
# ANGLE SIZE
# =========================================================

def extract_size(value):

    text = clean_text(value)

    match = re.search(
        r"(\d{2,3}\s*[x×]\s*\d{2,3})",
        text,
        re.IGNORECASE
    )

    if match:
        return match.group(1).replace(" ", "")

    return None


# =========================================================
# THICKNESS
# =========================================================

def extract_thickness(value):

    text = clean_text(value)

    match = re.search(
        r"(\d+(?:[./]\d+)?)",
        text
    )

    if match:
        return match.group(1)

    return None


# =========================================================
# PARSE
# =========================================================

def parse_angle_prices():

    print("Getting ANGLE prices...")
    print("SOURCE:", SOURCE_URL)

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
            StringIO(response.text)
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

    for table_index, df in enumerate(tables):

        print(
            f"Checking table {table_index + 1}: "
            f"{df.shape}"
        )

        for _, row in df.iterrows():

            values = [
                clean_text(x)
                for x in row.tolist()
            ]

            if len(values) < 5:
                continue

            row_text = " | ".join(values)

            size = extract_size(
                row_text
            )

            if size is None:
                continue

            # -------------------------------------------------
            # THICKNESS
            # -------------------------------------------------

            thickness = None

            for value in values:

                clean = clean_text(value)

                if re.fullmatch(
                    r"\d+(?:[./]\d+)?",
                    clean
                ):

                    try:

                        number = float(
                            clean.replace(
                                "/",
                                "."
                            )
                        )

                        if 1 <= number <= 20:
                            thickness = clean
                            break

                    except Exception:
                        pass

            if thickness is None:
                continue

            # -------------------------------------------------
            # DELIVERY
            # -------------------------------------------------

            delivery = None

            for value in values:

                if "کارخانه" in value:
                    delivery = "کارخانه"
                    break

                if "تهران" in value:
                    delivery = "تهران"
                    break

                if "انبار" in value:
                    delivery = "تهران"
                    break

            if delivery is None:
                continue

            # -------------------------------------------------
            # WEIGHT
            # -------------------------------------------------

            weight = None

            for value in values:

                clean = clean_text(value)

                try:

                    number = float(
                        clean.replace(",", "")
                    )

                    if 1 <= number <= 500:
                        weight = number
                        break

                except Exception:
                    continue

            # -------------------------------------------------
            # PRICE
            # -------------------------------------------------

            price = None

            for value in reversed(values):

                candidate = extract_price(
                    value
                )

                if candidate is None:
                    continue

                price = candidate
                break

            if price is None:
                continue

            results.append(
                {
                    "size": size,
                    "thickness": thickness,
                    "delivery": delivery,
                    "weight": weight,
                    "price": price,
                }
            )

    # ---------------------------------------------------------
    # REMOVE DUPLICATES
    # ---------------------------------------------------------

    unique = {}

    for item in results:

        key = (
            item["size"],
            item["thickness"],
            item["delivery"],
            item["weight"],
        )

        unique[key] = item

    results = list(
        unique.values()
    )

    return results


# =========================================================
# FONT
# =========================================================

def get_font(size):

    if not os.path.exists(FONT_FILE):

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
            "Authorization": PEXELS_KEY
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
    ).convert("RGB")


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

    title_font = get_font(52)
    subtitle_font = get_font(32)
    header_font = get_font(27)
    row_font = get_font(26)
    footer_font = get_font(25)
    watermark_font = get_font(29)

    # -----------------------------------------------------
    # TITLE
    # -----------------------------------------------------

    title = "📐 نبشی ناب تبریز"

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

    subtitle = "قیمت روز نبشی"

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
    # HEADER
    # -----------------------------------------------------

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
        (400, y + 18),
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
        (620, y + 18),
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

    # -----------------------------------------------------
    # ROWS
    # -----------------------------------------------------

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
            (400, y),
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
            (620, y),
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

    # -----------------------------------------------------
    # FOOTER
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # WATERMARK
    # -----------------------------------------------------

    watermark = "@arvand_aron_steel"

    bbox = draw.textbbox(
        (0, 0),
        watermark,
        font=watermark_font
    )

    watermark_width = (
        bbox[2] - bbox[0]
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

    return "\n".join(parts)


# =========================================================
# TELEGRAM
# =========================================================

def send_photo(
    image_file,
    caption
):

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
        "ANGLE PRICE BOT - TEST"
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
    # FRIDAY
    # -----------------------------------------------------

    if now.weekday() == 4:

        print(
            "Friday - no angle channel post."
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
    # PRICE
    # -----------------------------------------------------

    results = parse_angle_prices()

    print(
        "========================================"
    )

    print(
        f"VALID ANGLE PRODUCTS: {len(results)}"
    )

    print(
        "========================================"
    )

    if not results:

        print(
            "ERROR: No valid angle prices found."
        )

        return

    # -----------------------------------------------------
    # PRINT
    # -----------------------------------------------------

    for item in results:

        print(
            f"{item['size']} | "
            f"Thickness: {item['thickness']} | "
            f"Delivery: {item['delivery']} | "
            f"Weight: {item['weight']} | "
            f"Price: {item['price']:,}"
        )

    # -----------------------------------------------------
    # IMAGE
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # CAPTION
    # -----------------------------------------------------

    caption = build_caption(
        results
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
            "ANGLE CHANNEL TEST: SUCCESS"
        )

    else:

        print(
            "ANGLE CHANNEL TEST: FAILED"
        )

    print(
        "========================================"
    )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    main()