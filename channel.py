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
    )
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
# CHANNEL PRODUCTS
# فایکو حذف شده
# تهران حذف شده
# =========================================================

CHANNEL_PRODUCTS = [

    {
        "name": "سبک ناب",
        "factory": "ناودانی سبک ناب تبریز",
        "type": "سبک",
        "url": (
            "https://pivan.co/brands/"
            "tabriz-pure-steel/uchannel/"
        ),
    },

    {
        "name": "سبک شکفته",
        "factory": "ناودانی سبک شکفته",
        "type": "سبک",
        "url": (
            "https://pivan.co/brands/"
            "shekofteh-steel/uchannel/"
        ),
    },

    {
        "name": "سنگین ناب",
        "factory": "ناودانی سنگین ناب تبریز",
        "type": "سنگین",
        "url": (
            "https://pivan.co/brands/"
            "tabriz-pure-steel/uchannel/"
        ),
    },

    {
        "name": "سنگین ابهر",
        "factory": "ناودانی سنگین ابهر",
        "type": "سنگین",
        "url": (
            "https://pivan.co/brands/"
            "west-alborz-steel-complex-and-factory/"
            "uchannel/"
        ),
    },

    {
        "name": "سنگین شکفته",
        "factory": "ناودانی سنگین شکفته",
        "type": "سنگین",
        "url": (
            "https://pivan.co/brands/"
            "shekofteh-steel/uchannel/"
        ),
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

    """
    بررسی می‌کند آیا تاریخ موردنظر
    تعطیل رسمی ایران است یا خیر.

    جمعه جداگانه بررسی می‌شود.
    """

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

        # اگر سرویس/کتابخانه خطا داد،
        # جمعه همچنان طبق قانون بررسی می‌شود.
        return False


# =========================================================
# بررسی اینکه امروز روز انتشار هست یا نه
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
    # تعطیلات رسمی ایران
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
# NUMBER
# =========================================================

def normalize_number(value):

    if value is None:

        return None

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
# PRICE
# =========================================================

def extract_current_price(value):

    if value is None:

        return None

    text = normalize_number(
        value
    )

    if "تماس" in text:

        return None

    numbers = re.findall(
        r"\d[\d,]*",
        text
    )

    if not numbers:

        return None

    try:

        return int(
            numbers[-1].replace(
                ",",
                ""
            )
        )

    except Exception:

        return None


# =========================================================
# FETCH
# =========================================================

def fetch_page(url):

    response = requests.get(

        url,

        headers=HEADERS,

        timeout=TIMEOUT,

    )

    response.raise_for_status()

    return response


# =========================================================
# PARSE PRODUCT
# =========================================================

def parse_channel_product(
    product
):

    try:

        response = fetch_page(
            product["url"]
        )

    except Exception as e:

        return {

            "name":
                product["name"],

            "factory":
                product["factory"],

            "type":
                product["type"],

            "ok":
                False,

            "products":
                [],

            "error":
                (
                    f"Request error: "
                    f"{type(e).__name__}"
                ),
        }


    try:

        tables = pd.read_html(
            StringIO(
                response.text
            )
        )

    except Exception as e:

        return {

            "name":
                product["name"],

            "factory":
                product["factory"],

            "type":
                product["type"],

            "ok":
                False,

            "products":
                [],

            "error":
                (
                    f"Table error: "
                    f"{type(e).__name__}"
                ),
        }


    if not tables:

        return {

            "name":
                product["name"],

            "factory":
                product["factory"],

            "type":
                product["type"],

            "ok":
                False,

            "products":
                [],

            "error":
                "No table found",
        }


    df = tables[0]

    products = []


    for _, row in df.iterrows():

        values = [

            str(x).strip()

            for x in row.tolist()

        ]


        if len(values) < 5:

            continue


        size = normalize_number(
            values[0]
        )

        length = normalize_number(
            values[1]
        )

        delivery = values[2]

        unit = values[3]

        raw_price = values[4]


        # -------------------------------------------------
        # SIZE
        # -------------------------------------------------

        if not re.fullmatch(
            r"\d+(?:\.\d+)?",
            size
        ):

            continue


        # -------------------------------------------------
        # LENGTH
        # -------------------------------------------------

        if not re.fullmatch(
            r"\d+(?:\.\d+)?",
            length
        ):

            continue


        # -------------------------------------------------
        # UNIT
        # -------------------------------------------------

        if "کیلو" not in unit:

            continue


        # -------------------------------------------------
        # PRICE
        # -------------------------------------------------

        price = extract_current_price(
            raw_price
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
                    unit,

                "price":
                    price,

            }

        )


    return {

        "name":
            product["name"],

        "factory":
            product["factory"],

        "type":
            product["type"],

        "ok":
            len(products) > 0,

        "products":
            products,

    }


# =========================================================
# GET ALL PRICES
# =========================================================

def get_channel_prices():

    results = []


    for product in CHANNEL_PRODUCTS:

        result = parse_channel_product(
            product
        )

        results.append(
            result
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


    except Exception:

        pass


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

        "💰 واحد قیمت: تومان",

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


        return response.ok


    except Exception:

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


        return response.ok


    except Exception:

        return False


# =========================================================
# PRIVATE REPORT
# فقط برای کارخانه‌های غیر اصلی
# =========================================================

def send_private_prices(

    results

):

    if not PRIVATE_CHAT_ID:

        return True


    main_factories = {

        "نیشابور",

        "هیربد",

        "امیرکبیر",

    }


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


        if name in main_factories:

            continue


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
        "CHANNEL BOT"
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
    # بررسی تعطیلی
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

        print(
            "========================================"
        )

        print(
            "CHANNEL BOT FINISHED"
        )

        print(
            "========================================"
        )

        return


    # =====================================================
    # ENV CHECK
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
        "Getting channel prices..."
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

                f"{type(e).__name__}"

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