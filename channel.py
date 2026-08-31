import os
import re
import json
import requests
import pandas as pd
import holidays
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
PRIVATE_CHAT_ID = os.environ.get("PRIVATE_CHAT_ID")
TEHRAN = ZoneInfo("Asia/Tehran")
HISTORY_FILE = "channel_history.json"
IMAGE_FILE = "channel_price_card.jpg"
FONT_FILE = "NotoSansArabic-Regular.ttf"
FONT_URL = (
    "https://github.com/googlefonts/noto-fonts/"
    "raw/main/hinted/ttf/NotoSansArabic/"
    "NotoSansArabic-Regular.ttf"
)
PEXELS_URL = "https://api.pexels.com/v1/search"
# =========================================================
# SOURCE
# آهن ملل
# =========================================================
BASE_URL = (
    "https://ahanmelal.com/"
    "steel-t-bars-studs-angles/"
    "steel-stud-price"
)
# =========================================================
# CHANNEL PRODUCTS
#
# فرمت و نام کارخانه‌ها قفل است
#
# فایکو حذف شده
# تهران حذف شده
# =========================================================
CHANNEL_PRODUCTS = [
    {
        "name": "سبک ناب",
        "factory_keywords": [
            "ناب",
            "ناب تبریز",
        ],
        "type": "سبک",
    },
    {
        "name": "سبک شکفته",
        "factory_keywords": [
            "شکفته",
        ],
        "type": "سبک",
    },
    {
        "name": "سنگین ناب",
        "factory_keywords": [
            "ناب",
            "ناب تبریز",
        ],
        "type": "سنگین",
    },
    {
        "name": "سنگین ابهر",
        "factory_keywords": [
            "ابهر",
            "البرز غرب",
        ],
        "type": "سنگین",
    },
    {
        "name": "سنگین شکفته",
        "factory_keywords": [
            "شکفته",
        ],
        "type": "سنگین",
    },
]
# =========================================================
# COMPANY
# =========================================================
COMPANY_FOOTER = (
    "\n"
    "━━━━━━━━━━━━━━\n"
    "🏭 آروند آرون استیل\n"
    "👤 مدیریت: افشین آورزمانی\n"
    "📞 021-22122239\n"
    "🆔 @arvand_aron_steel"
)
# =========================================================
# تعطیلات رسمی ایران
# =========================================================
def is_iran_holiday(date):
    try:
        iran_holidays = holidays.Iran(
            years=[date.year]
        )
        return date in iran_holidays
    except Exception as e:
        print(
            "Holiday check error:",
            e
        )
        return False
# =========================================================
# CAN PUBLISH
# =========================================================
def can_publish_today(now):
    # -----------------------------------------------------
    # جمعه
    # -----------------------------------------------------
    if now.weekday() == 4:
        print(
            "FRIDAY - NO PRICE PUBLISHING"
        )
        return False
    # -----------------------------------------------------
    # تعطیلات رسمی
    # -----------------------------------------------------
    if is_iran_holiday(
        now.date()
    ):
        print(
            "OFFICIAL IRAN HOLIDAY - "
            "NO PRICE PUBLISHING"
        )
        return False
    return True
# =========================================================
# NORMALIZE NUMBER
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
        "\xa0",
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
# NUMBER
# =========================================================
def to_number(value):
    text = clean_text(
        value
    )
    if not text:
        return None
    text = text.replace(
        "٬",
        ","
    )
    text = text.replace(
        "،",
        ","
    )
    # حذف واحدها و متن
    text = text.replace(
        "تومان",
        ""
    )
    text = text.replace(
        "ریال",
        ""
    )
    match = re.search(
        r"\d[\d,]*(?:\.\d+)?",
        text
    )
    if not match:
        return None
    try:
        number = match.group(
            0
        ).replace(
            ",",
            ""
        )
        return float(
            number
        )
    except Exception:
        return None
# =========================================================
# PRICE
# فقط قیمت واقعی
# =========================================================
def extract_price(value):
    text = clean_text(
        value
    )
    if not text:
        return None
    if (
        "تماس" in text
        or "استعلام" in text
        or "عدم تولید" in text
        or "تعطیلی" in text
    ):
        return None
    number = to_number(
        text
    )
    if number is None:
        return None
    # -----------------------------------------------------
    # محدوده منطقی قیمت ناودانی
    # تومان / کیلو
    # -----------------------------------------------------
    if not (
        10000
        <= number
        <= 1000000
    ):
        return None
    return int(
        number
    )
# =========================================================
# FETCH
# =========================================================
def fetch_page(url):
    response = requests.get(
        url,
        headers=HEADERS,
        timeout=TIMEOUT
    )
    response.raise_for_status()
    return response
# =========================================================
# DETECT COLUMN
# =========================================================
def find_column(
    columns,
    keywords
):
    for column in columns:
        column_text = clean_text(
            column
        )
        for keyword in keywords:
            if keyword in column_text:
                return column
    return None
# =========================================================
# PARSE TABLE
# =========================================================
def parse_ahanmelal_table(
    df
):
    if df.empty:
        return []
    # -----------------------------------------------------
    # Flatten MultiIndex
    # -----------------------------------------------------
    if isinstance(
        df.columns,
        pd.MultiIndex
    ):
        new_columns = []
        for column in df.columns:
            parts = []
            for part in column:
                value = clean_text(
                    part
                )
                if value and value != "nan":
                    parts.append(
                        value
                    )
            new_columns.append(
                " ".join(parts)
            )
        df.columns = new_columns
    else:
        df.columns = [
            clean_text(col)
            for col in df.columns
        ]
    columns = list(
        df.columns
    )
    print(
        "TABLE COLUMNS:",
        columns
    )
    # =====================================================
    # COLUMN DETECTION
    # =====================================================
    size_column = find_column(
        columns,
        [
            "نوع ناودانی",
            "ناودانی",
        ]
    )
    length_column = find_column(
        columns,
        [
            "طول شاخه",
            "طول",
        ]
    )
    weight_column = find_column(
        columns,
        [
            "وزن",
        ]
    )
    unit_column = find_column(
        columns,
        [
            "واحد",
        ]
    )
    factory_column = find_column(
        columns,
        [
            "کارخانه",
        ]
    )
    loading_column = find_column(
        columns,
        [
            "بارگیری",
        ]
    )
    price_column = find_column(
        columns,
        [
            "قیمت",
        ]
    )
    print(
        "DETECTED COLUMNS:"
    )
    print(
        "SIZE:",
        size_column
    )
    print(
        "LENGTH:",
        length_column
    )
    print(
        "WEIGHT:",
        weight_column
    )
    print(
        "UNIT:",
        unit_column
    )
    print(
        "FACTORY:",
        factory_column
    )
    print(
        "LOADING:",
        loading_column
    )
    print(
        "PRICE:",
        price_column
    )
    if (
        size_column is None
        or length_column is None
        or price_column is None
    ):
        print(
            "REQUIRED COLUMNS NOT FOUND"
        )
        return []
    products = []
    # =====================================================
    # ROWS
    # =====================================================
    for _, row in df.iterrows():
        size_text = clean_text(
            row.get(
                size_column,
                ""
            )
        )
        # -------------------------------------------------
        # SIZE
        # -------------------------------------------------
        size_match = re.search(
            r"ناودانی\s*"
            r"(\d+(?:\.\d+)?)",
            size_text
        )
        if not size_match:
            # بعضی جدول‌ها ممکن است فقط عدد داشته باشند
            size_match = re.search(
                r"(\d+(?:\.\d+)?)",
                size_text
            )
        if not size_match:
            continue
        size = size_match.group(
            1
        )
        # -------------------------------------------------
        # LENGTH
        # -------------------------------------------------
        length_text = clean_text(
            row.get(
                length_column,
                ""
            )
        )
        length_number = to_number(
            length_text
        )
        if length_number is None:
            continue
        # فقط طول‌های واقعی ناودانی
        if length_number not in (
            6,
            12,
        ):
            continue
        length = str(
            int(length_number)
        )
        # -------------------------------------------------
        # UNIT
        # -------------------------------------------------
        unit = ""
        if unit_column is not None:
            unit = clean_text(
                row.get(
                    unit_column,
                    ""
                )
            )
        if (
            unit
            and
            "کیلو" not in unit
        ):
            continue
        # -------------------------------------------------
        # FACTORY
        # -------------------------------------------------
        factory = ""
        if factory_column is not None:
            factory = clean_text(
                row.get(
                    factory_column,
                    ""
                )
            )
        # -------------------------------------------------
        # LOADING
        # -------------------------------------------------
        delivery = ""
        if loading_column is not None:
            delivery = clean_text(
                row.get(
                    loading_column,
                    ""
                )
            )
        # -------------------------------------------------
        # WEIGHT
        # -------------------------------------------------
        weight = None
        if weight_column is not None:
            weight = to_number(
                row.get(
                    weight_column,
                    ""
                )
            )
        # -------------------------------------------------
        # PRICE
        # مهم:
        # قیمت فقط از ستون PRICE
        # -------------------------------------------------
        price = extract_price(
            row.get(
                price_column,
                ""
            )
        )
        if price is None:
            continue
        products.append(
            {
                "size":
                    size,
                "length":
                    length,
                "delivery":
                    delivery,
                "unit":
                    unit or "کیلوگرم",
                "weight":
                    weight,
                "factory":
                    factory,
                "price":
                    price,
            }
        )
    return products
# =========================================================
# FACTORY MATCH
# =========================================================
def factory_matches(
    product,
    channel_product
):
    factory = clean_text(
        product.get(
            "factory",
            ""
        )
    )
    size_text = clean_text(
        product.get(
            "size",
            ""
        )
    )
    keywords = channel_product.get(
        "factory_keywords",
        []
    )
    matched = False
    for keyword in keywords:
        if keyword in factory:
            matched = True
            break
    if not matched:
        return False
    # =====================================================
    # سبک / سنگین
    # =====================================================
    #
    # آهن ملل ممکن است نوع را داخل
    # ستون "نوع ناودانی" یا "بارگیری"
    # یا متن محصول داشته باشد.
    #
    # برای جلوگیری از اشتباه، وزن را هم
    # در نظر می‌گیریم.
    # =====================================================
    item_type = channel_product.get(
        "type"
    )
    weight = product.get(
        "weight"
    )
    combined = " ".join(
        [
            factory,
            size_text,
            clean_text(
                product.get(
                    "delivery",
                    ""
                )
            ),
        ]
    )
    if item_type == "سبک":
        if (
            "سنگین" in combined
            and "سبک" not in combined
        ):
            return False
    if item_type == "سنگین":
        if (
            "سبک" in combined
            and "سنگین" not in combined
        ):
            return False
    return True
# =========================================================
# FILTER TYPE
# =========================================================
def filter_factory_products(
    products,
    channel_product
):
    matched = []
    for product in products:
        if factory_matches(
            product,
            channel_product
        ):
            matched.append(
                product
            )
    # -----------------------------------------------------
    # حذف تکراری
    # -----------------------------------------------------
    unique = {}
    for product in matched:
        key = (
            product["size"],
            product["length"],
            product["factory"],
        )
        unique[key] = product
    matched = list(
        unique.values()
    )
    # -----------------------------------------------------
    # SORT
    # -----------------------------------------------------
    def sort_key(item):
        try:
            return (
                float(
                    item["size"]
                ),
                float(
                    item["length"]
                ),
            )
        except Exception:
            return (
                999,
                999
            )
    matched.sort(
        key=sort_key
    )
    return matched
# =========================================================
# PARSE ONE FACTORY
# =========================================================
def parse_channel_product(
    channel_product,
    all_tables
):
    all_products = []
    for table_index, df in enumerate(
        all_tables
    ):
        print(
            "Checking table:",
            table_index + 1
        )
        try:
            products = parse_ahanmelal_table(
                df
            )
        except Exception as e:
            print(
                "TABLE PARSE ERROR:",
                type(e).__name__,
                str(e)
            )
            continue
        all_products.extend(
            products
        )
    products = filter_factory_products(
        all_products,
        channel_product
    )
    if not products:
        return {
            "name":
                channel_product["name"],
            "factory":
                channel_product.get(
                    "factory_keywords",
                    []
                ),
            "type":
                channel_product["type"],
            "ok":
                False,
            "products":
                [],
            "error":
                "No matching prices found",
        }
    return {
        "name":
            channel_product["name"],
        "factory":
            channel_product.get(
                "factory_keywords",
                []
            ),
        "type":
            channel_product["type"],
        "ok":
            True,
        "products":
            products,
    }
# =========================================================
# GET ALL PRICES
# =========================================================
def get_channel_prices():
    print(
        "========================================"
    )
    print(
        "FETCHING AHANMELAL"
    )
    print(
        BASE_URL
    )
    print(
        "========================================"
    )
    try:
        response = fetch_page(
            BASE_URL
        )
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
    try:
        tables = pd.read_html(
            StringIO(
                response.text
            )
        )
    except Exception as e:
        print(
            "READ HTML ERROR:",
            type(e).__name__,
            str(e)
        )
        return []
    print(
        "TABLES FOUND:",
        len(tables)
    )
    results = []
    for channel_product in CHANNEL_PRODUCTS:
        result = parse_channel_product(
            channel_product,
            tables
        )
        results.append(
            result
        )
        print(
            "----------------------------------------"
        )
        print(
            "FACTORY:",
            result["name"]
        )
        print(
            "TYPE:",
            result["type"]
        )
        print(
            "VALID:",
            len(
                result.get(
                    "products",
                    []
                )
            )
        )
        for item in result.get(
            "products",
            []
        ):
            print(
                f"{item['size']} | "
                f"{item['length']}m | "
                f"{item.get('factory', '')} | "
                f"{item['price']:,}"
            )
    print(
        "========================================"
    )
    return results
# =========================================================
# HISTORY
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
            "HISTORY LOAD ERROR:",
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
    pexels_key = os.environ.get(
        "PEXELS_API_KEY"
    )
    if not pexels_key:
        raise RuntimeError(
            "PEXELS_API_KEY is missing"
        )
    response = requests.get(
        PEXELS_URL,
        headers={
            "Authorization":
                pexels_key
        },
        params={
            "query":
                "steel construction metal",
            "orientation":
                "landscape",
            "per_page":
                30,
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
# PRICE IMAGE
# =========================================================
def create_price_image(
    factory_name,
    prices
):
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
            125
        )
    )
    # -----------------------------------------------------
    # PANEL
    # -----------------------------------------------------
    panel_x1 = 80
    panel_y1 = 80
    panel_x2 = width - 80
    panel_y2 = height - 80
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
    # FONTS
    # -----------------------------------------------------
    title_font = get_font(52)
    subtitle_font = get_font(32)
    price_font = get_font(36)
    small_font = get_font(27)
    watermark_font = get_font(30)
    # -----------------------------------------------------
    # TITLE
    # -----------------------------------------------------
    title = (
        "🏗 " +
        factory_name
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
            130
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
        "قیمت روز ناودانی"
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
            205
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
    # PRICE LIST
    # -----------------------------------------------------
    y = 300
    for item in prices:
        size = item.get(
            "size"
        )
        length = item.get(
            "length"
        )
        value = item.get(
            "price"
        )
        text = (
            f"ناودانی {size} "
            f"- {length} متر    "
            f"{value:,} تومان"
        )
        draw.text(
            (
                180,
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
                170,
                y + 62,
                width - 170,
                y + 62
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
    # UNIT
    # -----------------------------------------------------
    draw.text(
        (
            180,
            y + 15
        ),
        "💰 واحد قیمت: تومان / کیلوگرم",
        font=small_font,
        fill=(
            70,
            70,
            70,
            255
        )
    )
    # -----------------------------------------------------
    # MAIN WATERMARK
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
            width -
            watermark_width -
            110,
            height -
            145,
            width -
            55,
            height -
            70
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
            width -
            watermark_width -
            82,
            height -
            130
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
    # LIGHT WATERMARKS
    # -----------------------------------------------------
    positions = [
        (120, 520),
        (520, 760),
        (170, 1000),
        (620, 1220),
    ]
    for x, y_pos in positions:
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
    # SAVE
    # -----------------------------------------------------
    image.save(
        IMAGE_FILE,
        "JPEG",
        quality=95
    )
    return IMAGE_FILE
# =========================================================
# FORMAT PRICE
# =========================================================
def format_price(value):
    if value is None:
        return "نامشخص"
    return f"{int(value):,}"
# =========================================================
# COMPARISON
# =========================================================
def calculate_average_change(
    current_prices,
    previous_prices
):
    if (
        not current_prices
        or
        not previous_prices
    ):
        return None
    previous_map = {}
    for item in previous_prices:
        try:
            key = (
                str(item["size"]),
                str(item["length"])
            )
            previous_map[key] = float(
                item["price"]
            )
        except Exception:
            continue
    changes = []
    for item in current_prices:
        try:
            key = (
                str(item["size"]),
                str(item["length"])
            )
            current = float(
                item["price"]
            )
            previous = previous_map.get(
                key
            )
            if (
                previous is None
                or
                previous == 0
            ):
                continue
            changes.append(
                (
                    (
                        current -
                        previous
                    )
                    /
                    previous
                )
                *
                100
            )
        except Exception:
            continue
    if not changes:
        return None
    return (
        sum(changes)
        /
        len(changes)
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
            f"🟢 قیمت ناودانی در مجموع "
            f"<b>{change:+.2f}٪ افزایش</b> داشته است."
        )
    if change < -0.01:
        return (
            "📊 <b>مقایسه با آخرین قیمت:</b>\n"
            f"🔴 قیمت ناودانی در مجموع "
            f"<b>{change:+.2f}٪ کاهش</b> داشته است."
        )
    return (
        "📊 <b>مقایسه با آخرین قیمت:</b>\n"
        "⚪ قیمت ناودانی در مجموع "
        "<b>بدون تغییر</b> بوده است."
    )
# =========================================================
# CHANNEL CAPTION
# =========================================================
def build_caption(
    factory_name,
    prices,
    previous
):
    now = datetime.now(
        TEHRAN
    )
    parts = [
        f"🏗 <b>{factory_name}</b>",
        "📌 <b>قیمت روز ناودانی</b>",
        f"📅 {now.strftime('%Y/%m/%d')} "
        f"⏰ {now.strftime('%H:%M')}",
        "💰 واحد قیمت: تومان",
        "",
    ]
    for item in prices:
        size = item.get(
            "size"
        )
        length = item.get(
            "length"
        )
        value = item.get(
            "price"
        )
        parts.append(
            f"🔩 ناودانی {size} - "
            f"{length} متر: "
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
# TELEGRAM - SEND PHOTO
# =========================================================
def send_photo(
    chat_id,
    image_file,
    caption
):
    if not chat_id:
        return False
    if not TOKEN:
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
                        chat_id,
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
        if not response.ok:
            print(
                "TELEGRAM PHOTO ERROR:",
                response.text
            )
        return response.ok
    except Exception as e:
        print(
            "SEND PHOTO ERROR:",
            type(e).__name__,
            str(e)
        )
        return False
# =========================================================
# TELEGRAM - SEND MESSAGE
# =========================================================
def send_message(
    chat_id,
    message
):
    if not chat_id:
        return False
    if not TOKEN:
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
                    True,
            },
            timeout=30
        )
        if not response.ok:
            print(
                "TELEGRAM MESSAGE ERROR:",
                response.text
            )
        return response.ok
    except Exception as e:
        print(
            "SEND MESSAGE ERROR:",
            type(e).__name__,
            str(e)
        )
        return False
# =========================================================
# PRIVATE REPORT
# =========================================================
def send_private_prices(
    results
):
    if not PRIVATE_CHAT_ID:
        return True
    parts = [
        "🔐 <b>گزارش قیمت کارخانه‌ها</b>",
        "",
    ]
    found = False
    for result in results:
        name = result.get(
            "name",
            ""
        )
        # -------------------------------------------------
        # همان منطق قبلی:
        # کارخانه اصلی کانال را دوباره خصوصی نفرست
        # -------------------------------------------------
        prices = result.get(
            "products",
            []
        )
        if not prices:
            continue
        found = True
        parts.append(
            f"🏗 <b>{name}</b>"
        )
        for item in prices:
            parts.append(
                f"ناودانی {item['size']} - "
                f"{item['length']} متر: "
                f"<b>{format_price(item['price'])}</b> تومان"
            )
        parts.append("")
    if not found:
        parts.append(
            "⚪ قیمت کارخانه‌های دیگر دریافت نشد."
        )
    parts.append(
        COMPANY_FOOTER
    )
    return send_message(
        PRIVATE_CHAT_ID,
        "\n".join(parts)
    )
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
        "CHANNEL BOT - AHANMELAL"
    )
    print(
        "Iran time:",
        now.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )
    print(
        "SOURCE:",
        BASE_URL
    )
    print(
        "========================================"
    )
    # =====================================================
    # HOLIDAY
    # =====================================================
    if not can_publish_today(
        now
    ):
        print(
            "Today is a non-publishing day."
        )
        print(
            "No prices will be fetched or published."
        )
        return
    # =====================================================
    # ENV
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
    if missing:
        print(
            "ERROR: missing environment variables:",
            ", ".join(missing)
        )
        return
    # =====================================================
    # GET PRICES
    # =====================================================
    print(
        "Getting prices from AHANMELAL..."
    )
    results = get_channel_prices()
    valid_results = [
        r
        for r in results
        if r.get("ok")
    ]
    total_products = sum(
        len(
            r.get(
                "products",
                []
            )
        )
        for r in valid_results
    )
    print(
        f"Factories: "
        f"{len(valid_results)}/"
        f"{len(CHANNEL_PRODUCTS)}"
    )
    print(
        f"Products: "
        f"{total_products}"
    )
    # =====================================================
    # ERROR SUMMARY
    # =====================================================
    for result in results:
        if not result.get("ok"):
            print(
                f"ERROR | "
                f"{result.get('name')} | "
                f"{result.get('error', 'No prices')}"
            )
    # =====================================================
    # SAFETY LOCK
    # =====================================================
    #
    # اگر هیچ کارخانه‌ای قیمت معتبر نداد
    # چیزی منتشر نکن.
    # =====================================================
    if not valid_results:
        print(
            "SAFETY LOCK:"
        )
        print(
            "No valid AHANMELAL prices found."
        )
        print(
            "NOTHING WILL BE PUBLISHED."
        )
        return
    # =====================================================
    # HISTORY
    # =====================================================
    history = load_history()
    previous = history.get(
        "factories",
        {}
    )
    # =====================================================
    # SEND TO CHANNEL
    # =====================================================
    sent = 0
    for result in results:
        if not result.get("ok"):
            continue
        factory_name = result[
            "name"
        ]
        prices = result[
            "products"
        ]
        previous_prices = previous.get(
            factory_name,
            []
        )
        try:
            image_file = create_price_image(
                factory_name,
                prices
            )
            caption = build_caption(
                factory_name,
                prices,
                previous_prices
            )
            success = send_photo(
                CHANNEL,
                image_file,
                caption
            )
            if success:
                sent += 1
                previous[
                    factory_name
                ] = prices
                print(
                    f"SENT | "
                    f"{factory_name}"
                )
            else:
                print(
                    f"FAILED | "
                    f"{factory_name}"
                )
        except Exception as e:
            print(
                f"FAILED | "
                f"{factory_name} | "
                f"{type(e).__name__} | "
                f"{str(e)}"
            )
    # =====================================================
    # PRIVATE
    # =====================================================
    private_success = send_private_prices(
        results
    )
    if PRIVATE_CHAT_ID:
        if private_success:
            print(
                "PRIVATE | SENT"
            )
        else:
            print(
                "PRIVATE | FAILED"
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
    ] = previous
    save_history(
        history
    )
    # =====================================================
    # FINAL
    # =====================================================
    print(
        "========================================"
    )
    print(
        f"CHANNEL SENT: "
        f"{sent}/"
        f"{len(CHANNEL_PRODUCTS)}"
    )
    print(
        f"TOTAL PRODUCTS: "
        f"{total_products}"
    )
    print(
        "CHANNEL BOT FINISHED"
    )
    print(
        "========================================"
    )
# =========================================================
# RUN
# =========================================================
if __name__ == "__main__":
    main()