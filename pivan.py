import requests
from bs4 import BeautifulSoup
import re
import holidays
from datetime import datetime
from zoneinfo import ZoneInfo


# =========================================================
# SETTINGS
# =========================================================

URL = "https://pivan.co/brands/khorasan-steel-neishabour/rebar/"

FACTORY = "فولاد خراسان نیشابور"
PRODUCT = "میلگرد"
BRAND = "KSC"

TEHRAN = ZoneInfo("Asia/Tehran")


# =========================================================
# HTTP
# =========================================================

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/139.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,image/avif,image/webp,"
        "image/apng,*/*;q=0.8"
    ),
    "Accept-Language": (
        "fa-IR,fa;q=0.9,en-US;q=0.8,en;q=0.7"
    ),
}


# =========================================================
# OFFICIAL IRAN HOLIDAYS
# =========================================================

IRAN_HOLIDAYS = holidays.Iran()


# =========================================================
# POSTING TIME CHECK
# =========================================================

def can_post_now():

    now = datetime.now(
        TEHRAN
    )

    # -----------------------------------------------------
    # TIME
    # -----------------------------------------------------
    # اجازه انتشار:
    # 08:00 تا قبل از 22:00
    #
    # یعنی:
    # 07:59  -> ممنوع
    # 08:00  -> مجاز
    # 21:59  -> مجاز
    # 22:00  -> ممنوع
    # -----------------------------------------------------

    if now.hour < 8 or now.hour >= 22:

        print(
            "POSTING DISABLED: "
            "outside 08:00-22:00 Iran time."
        )

        print(
            "Iran time:",
            now.strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )

        return False

    # -----------------------------------------------------
    # OFFICIAL HOLIDAY
    # -----------------------------------------------------

    today = now.date()

    if today in IRAN_HOLIDAYS:

        print(
            "POSTING DISABLED: "
            "official Iran holiday."
        )

        print(
            "Date:",
            today
        )

        print(
            "Holiday:",
            IRAN_HOLIDAYS.get(today)
        )

        return False

    # -----------------------------------------------------
    # ALLOWED
    # -----------------------------------------------------

    print(
        "POSTING TIME: ALLOWED"
    )

    print(
        "Iran time:",
        now.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )

    return True


# =========================================================
# NUMBER
# =========================================================

def normalize_digits(text):

    if not text:
        return ""

    table = str.maketrans(
        "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩",
        "01234567890123456789"
    )

    return text.translate(table)


def clean_number(text):

    if not text:
        return None

    text = normalize_digits(text)

    text = text.replace(",", "")
    text = text.replace("٬", "")

    match = re.search(
        r"\d+(?:\.\d+)?",
        text
    )

    if not match:
        return None

    try:

        return int(
            float(
                match.group()
            )
        )

    except Exception:

        return None


# =========================================================
# SIZE
# =========================================================

def extract_size(text):

    text = normalize_digits(
        text
    )

    match = re.search(
        r"\d+",
        text
    )

    if not match:
        return None

    try:

        size = int(
            match.group()
        )

        if size < 8 or size > 50:
            return None

        return size

    except Exception:

        return None


# =========================================================
# PRICE
# =========================================================

def extract_price(price_cell):

    if price_cell is None:
        return None

    # -----------------------------------------------------
    # فقط قیمت قبل از ارزش افزوده
    # -----------------------------------------------------

    ex_tax = price_cell.select_one(
        "span.ex-tax"
    )

    if ex_tax is None:
        return None

    price_text = ex_tax.get_text(
        " ",
        strip=True
    )

    # اگر سایت نوشته باشد:
    # تماس بگیرید
    if "تماس" in price_text:
        return None

    return clean_number(
        price_text
    )


# =========================================================
# IN TAX PRICE
# =========================================================

def extract_in_tax_price(price_cell):

    if price_cell is None:
        return None

    in_tax = price_cell.select_one(
        "span.in-tax"
    )

    if in_tax is None:
        return None

    price_text = in_tax.get_text(
        " ",
        strip=True
    )

    if "تماس" in price_text:
        return None

    return clean_number(
        price_text
    )


# =========================================================
# FLUCTUATION
# =========================================================

def extract_fluctuation(cell):

    if cell is None:
        return None

    text = normalize_digits(
        cell.get_text(
            " ",
            strip=True
        )
    )

    match = re.search(
        r"[-+]?\d+(?:\.\d+)?",
        text
    )

    if not match:
        return None

    try:

        return float(
            match.group()
        )

    except Exception:

        return None


# =========================================================
# GET PAGE
# =========================================================

def get_page():

    response = requests.get(
        URL,
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()

    return response.text


# =========================================================
# FIND PRICE TABLE
# =========================================================

def find_price_table(soup):

    tables = soup.find_all(
        "table"
    )

    for table in tables:

        text = table.get_text(
            " ",
            strip=True
        )

        if (
            "سایز" in text
            and "قیمت" in text
            and "نوسان" in text
        ):

            return table

    return None


# =========================================================
# PARSE
# =========================================================

def parse_prices(html):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    table = find_price_table(
        soup
    )

    if table is None:

        raise RuntimeError(
            "جدول قیمت میلگرد در Pivan پیدا نشد."
        )

    products = []

    rows = table.find_all(
        "tr"
    )

    for row in rows:

        cells = row.find_all(
            ["th", "td"]
        )

        if len(cells) < 5:
            continue

        # -------------------------------------------------
        # SIZE
        # -------------------------------------------------

        size = extract_size(
            cells[0].get_text(
                " ",
                strip=True
            )
        )

        if size is None:
            continue

        # -------------------------------------------------
        # STANDARD
        # -------------------------------------------------

        standard = cells[1].get_text(
            " ",
            strip=True
        ).strip()

        # -------------------------------------------------
        # DELIVERY
        # -------------------------------------------------

        delivery = cells[2].get_text(
            " ",
            strip=True
        ).strip()

        # -------------------------------------------------
        # UNIT
        # -------------------------------------------------

        unit = cells[3].get_text(
            " ",
            strip=True
        ).strip()

        # -------------------------------------------------
        # PRICE CELL
        # -------------------------------------------------

        price_cell = cells[4]

        # -------------------------------------------------
        # EX-TAX PRICE
        # -------------------------------------------------

        price = extract_price(
            price_cell
        )

        # -------------------------------------------------
        # IN-TAX PRICE
        # -------------------------------------------------

        in_tax_price = extract_in_tax_price(
            price_cell
        )

        # -------------------------------------------------
        # FLUCTUATION
        # -------------------------------------------------

        fluctuation = None

        if len(cells) > 5:

            fluctuation = extract_fluctuation(
                cells[5]
            )

        # -------------------------------------------------
        # IMPORTANT
        # -------------------------------------------------
        # محصول بدون قیمت واقعی وارد خروجی نشود
        # -------------------------------------------------

        if price is None:
            continue

        # -------------------------------------------------
        # PRODUCT
        # -------------------------------------------------

        products.append({

            "factory":
                FACTORY,

            "brand":
                BRAND,

            "product":
                PRODUCT,

            "size":
                size,

            "standard":
                standard,

            "delivery":
                delivery,

            "unit":
                unit,

            # قیمت اصلی پروژه
            # قبل از ارزش افزوده
            "price":
                price,

            # قیمت با ارزش افزوده
            "in_tax_price":
                in_tax_price,

            "price_unit":
                "تومان/کیلوگرم",

            "price_basis":
                "ex_tax",

            "fluctuation_percent":
                fluctuation,

            "source":
                "Pivan",

            "source_url":
                URL,
        })

    # =====================================================
    # REMOVE DUPLICATES
    # =====================================================

    unique = []

    seen = set()

    for item in products:

        key = (
            item["factory"],
            item["size"],
            item["standard"],
            item["delivery"],
        )

        if key in seen:
            continue

        seen.add(key)

        unique.append(
            item
        )

    # =====================================================
    # SORT BY SIZE
    # =====================================================

    unique.sort(
        key=lambda x: x["size"]
    )

    return unique


# =========================================================
# PUBLIC FUNCTION
# =========================================================

def get_prices():

    # -----------------------------------------------------
    # TIME / HOLIDAY LOCK
    # -----------------------------------------------------

    if not can_post_now():

        return []

    # -----------------------------------------------------
    # GET PRICES
    # -----------------------------------------------------

    html = get_page()

    return parse_prices(
        html
    )