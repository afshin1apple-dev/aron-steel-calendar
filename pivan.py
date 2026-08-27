import requests
from bs4 import BeautifulSoup
import re
import json


# =========================================================
# SETTINGS
# =========================================================

URL = "https://pivan.co/brands/khorasan-steel-neishabour/rebar/"

FACTORY = "فولاد خراسان نیشابور"
PRODUCT = "میلگرد"


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
# SESSION
# =========================================================

session = requests.Session()
session.headers.update(HEADERS)


# =========================================================
# NORMALIZE DIGITS
# =========================================================

def normalize_digits(text):

    if text is None:
        return ""

    text = str(text)

    table = str.maketrans(
        "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩",
        "01234567890123456789"
    )

    return text.translate(table)


# =========================================================
# CLEAN TEXT
# =========================================================

def clean_text(text):

    if text is None:
        return ""

    text = normalize_digits(text)

    text = text.replace("\xa0", " ")
    text = text.replace("\u200c", " ")
    text = text.replace("\u200f", "")
    text = text.replace("\u200e", "")

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# =========================================================
# PARSE NUMBER
# =========================================================

def parse_number(text):

    text = clean_text(text)

    if not text:
        return None

    # حذف جداکننده‌های هزارگان
    text = text.replace(",", "")
    text = text.replace("٬", "")

    match = re.search(
        r"\d+(?:\.\d+)?",
        text
    )

    if not match:
        return None

    try:

        value = float(
            match.group()
        )

        return int(value)

    except Exception:

        return None


# =========================================================
# EXTRACT SIZE
# =========================================================

def extract_size(text):

    text = clean_text(text)

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

    except Exception:

        return None

    # محدوده منطقی میلگرد
    if size < 8 or size > 50:
        return None

    return size


# =========================================================
# EXTRACT EX-TAX PRICE
# =========================================================

def extract_ex_tax_price(cell):

    if cell is None:
        return None

    # -----------------------------------------------------
    # اولویت قطعی:
    # span.ex-tax
    # -----------------------------------------------------

    ex_tax = cell.select_one(
        "span.ex-tax"
    )

    if ex_tax:

        price = parse_number(
            ex_tax.get_text(
                " ",
                strip=True
            )
        )

        if price is not None:
            return price

    # -----------------------------------------------------
    # مهم:
    # اگر ex-tax وجود نداشت، از متن کامل سلول
    # قیمت استخراج نمی‌کنیم.
    #
    # چون ممکن است قیمت in-tax باشد.
    # -----------------------------------------------------

    return None


# =========================================================
# FETCH PAGE
# =========================================================

def get_page():

    response = session.get(
        URL,
        timeout=30
    )

    response.raise_for_status()

    # تشخیص encoding واقعی
    response.encoding = response.apparent_encoding

    return response.text


# =========================================================
# FIND PRICE TABLE
# =========================================================

def find_price_table(soup):

    tables = soup.find_all(
        "table"
    )

    if not tables:

        raise RuntimeError(
            "هیچ جدول قیمتی در صفحه پیدا نشد."
        )

    # -----------------------------------------------------
    # جستجوی جدول اصلی
    # -----------------------------------------------------

    for table in tables:

        text = clean_text(
            table.get_text(
                " ",
                strip=True
            )
        )

        if (
            "سایز" in text
            and "قیمت" in text
            and "نوسان" in text
        ):

            return table

    # -----------------------------------------------------
    # حالت دوم:
    # بعضی تغییرات HTML ممکن است "سایز" را نداشته باشند.
    # -----------------------------------------------------

    for table in tables:

        text = clean_text(
            table.get_text(
                " ",
                strip=True
            )
        )

        if (
            "قیمت" in text
            and "نوسان" in text
        ):

            return table

    raise RuntimeError(
        "جدول قیمت میلگرد پیدا نشد."
    )


# =========================================================
# PARSE TABLE
# =========================================================

def parse_prices(html):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    table = find_price_table(
        soup
    )

    rows = table.find_all(
        "tr"
    )

    products = []

    # =====================================================
    # READ ROWS
    # =====================================================

    for row in rows:

        cells = row.find_all(
            ["td", "th"]
        )

        if len(cells) < 5:
            continue

        # -------------------------------------------------
        # ستون‌ها
        #
        # 0 = سایز
        # 1 = استاندارد
        # 2 = محل تحویل
        # 3 = واحد
        # 4 = قیمت
        # 5 = نوسان
        # -------------------------------------------------

        size_text = clean_text(
            cells[0].get_text(
                " ",
                strip=True
            )
        )

        standard = clean_text(
            cells[1].get_text(
                " ",
                strip=True
            )
        )

        delivery = clean_text(
            cells[2].get_text(
                " ",
                strip=True
            )
        )

        unit = clean_text(
            cells[3].get_text(
                " ",
                strip=True
            )
        )

        price_cell = cells[4]

        # -------------------------------------------------
        # SIZE
        # -------------------------------------------------

        size = extract_size(
            size_text
        )

        if size is None:
            continue

        # -------------------------------------------------
        # PRICE
        # -------------------------------------------------

        price = extract_ex_tax_price(
            price_cell
        )

        # -------------------------------------------------
        # FLUCTUATION
        # -------------------------------------------------

        fluctuation = None

        if len(cells) >= 6:

            fluctuation_text = clean_text(
                cells[5].get_text(
                    " ",
                    strip=True
                )
            )

            fluctuation_text = (
                fluctuation_text
                .replace("%", "")
            )

            match = re.search(
                r"[-+]?\d+(?:\.\d+)?",
                fluctuation_text
            )

            if match:

                try:

                    fluctuation = float(
                        match.group()
                    )

                except Exception:

                    fluctuation = None

        # -------------------------------------------------
        # PRODUCT
        # -------------------------------------------------

        product = {

            "factory":
                FACTORY,

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

            # قیمت اصلی:
            # قبل از ارزش افزوده
            "price":
                price,

            "price_unit":
                "تومان/کیلوگرم",

            "fluctuation_percent":
                fluctuation,

            "source":
                "Pivan",

            "source_url":
                URL
        }

        products.append(
            product
        )

    # =====================================================
    # REMOVE DUPLICATES
    # =====================================================

    unique = []

    seen = set()

    for product in products:

        key = (
            product["size"],
            product["standard"],
            product["delivery"]
        )

        if key in seen:
            continue

        seen.add(
            key
        )

        unique.append(
            product
        )

    # =====================================================
    # SORT BY SIZE
    # =====================================================

    unique.sort(
        key=lambda item: item["size"]
    )

    return unique


# =========================================================
# PUBLIC FUNCTION
# =========================================================

def get_prices():

    html = get_page()

    products = parse_prices(
        html
    )

    return products


# =========================================================
# SAVE JSON
# =========================================================

def save_json(
    products,
    filename="pivan_prices.json"
):

    data = {

        "source":
            "Pivan",

        "factory":
            FACTORY,

        "product":
            PRODUCT,

        "url":
            URL,

        "price_basis":
            "ex_tax",

        "price_description":
            "قیمت قبل از ارزش افزوده",

        "count":
            len(products),

        "prices":
            products
    }

    with open(
        filename,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2
        )

    return data


# =========================================================
# DIRECT TEST
# =========================================================

if __name__ == "__main__":

    print()
    print("=" * 70)
    print("PIVAN PRICE SCRAPER")
    print("=" * 70)

    try:

        prices = get_prices()

        print()
        print(
            f"PRODUCTS FOUND: {len(prices)}"
        )

        print()

        for item in prices:

            if item["price"] is None:

                price_text = "تماس بگیرید"

            else:

                price_text = (
                    f'{item["price"]:,}'
                )

            print(
                f'🏭 {item["factory"]} | '
                f'📏 {item["size"]} | '
                f'📋 {item["standard"]} | '
                f'💰 {price_text} تومان | '
                f'📍 {item["delivery"]}'
            )

        save_json(
            prices
        )

        print()
        print(
            "JSON SAVED: pivan_prices.json"
        )

        print()
        print("=" * 70)
        print("PIVAN TEST FINISHED")
        print("=" * 70)

    except Exception as e:

        print()
        print(
            "❌ ERROR:"
        )

        print(
            str(e)
        )

        raise