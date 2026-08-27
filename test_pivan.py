import requests
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime, timezone


URL = "https://pivan.co/brands/khorasan-steel-neishabour/rebar/"

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
# CLEAN TEXT
# =========================================================

def clean_text(text):

    if text is None:
        return ""

    text = str(text)

    text = (
        text.replace("۰", "0")
            .replace("۱", "1")
            .replace("۲", "2")
            .replace("۳", "3")
            .replace("۴", "4")
            .replace("۵", "5")
            .replace("۶", "6")
            .replace("۷", "7")
            .replace("۸", "8")
            .replace("۹", "9")
    )

    text = (
        text.replace("٠", "0")
            .replace("١", "1")
            .replace("٢", "2")
            .replace("٣", "3")
            .replace("٤", "4")
            .replace("٥", "5")
            .replace("٦", "6")
            .replace("٧", "7")
            .replace("٨", "8")
            .replace("٩", "9")
    )

    text = text.replace("\xa0", " ")

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# =========================================================
# FIND NUMBERS
# =========================================================

def extract_numbers(text):

    text = clean_text(text)

    numbers = re.findall(
        r"\d[\d,]*",
        text
    )

    result = []

    for number in numbers:

        number = number.replace(
            ",",
            ""
        )

        try:

            value = int(number)

            result.append(
                value
            )

        except Exception:

            continue

    return result


# =========================================================
# FIND SINGLE PRICE
# =========================================================

def extract_single_price(text):

    numbers = extract_numbers(
        text
    )

    for number in numbers:

        # محدوده منطقی قیمت فولاد
        if 10000 <= number <= 100000000:

            return number

    return None


# =========================================================
# ANALYZE PRICE CELL
# =========================================================

def analyze_price_cell(cell):

    # -----------------------------------------------------
    # متن کامل سلول
    # -----------------------------------------------------

    text = clean_text(
        cell.get_text(
            " ",
            strip=True
        )
    )

    # -----------------------------------------------------
    # قیمت قبل از ارزش افزوده
    # -----------------------------------------------------

    ex_tax_span = cell.select_one(
        "span.ex-tax"
    )

    ex_tax_text = ""

    if ex_tax_span:

        ex_tax_text = clean_text(
            ex_tax_span.get_text(
                " ",
                strip=True
            )
        )

    ex_tax_price = extract_single_price(
        ex_tax_text
    )

    # -----------------------------------------------------
    # قیمت با ارزش افزوده
    # فقط برای ثبت اطلاعات، نه قیمت اصلی
    # -----------------------------------------------------

    in_tax_span = cell.select_one(
        "span.in-tax"
    )

    in_tax_text = ""

    if in_tax_span:

        in_tax_text = clean_text(
            in_tax_span.get_text(
                " ",
                strip=True
            )
        )

    in_tax_price = extract_single_price(
        in_tax_text
    )

    # -----------------------------------------------------
    # قیمت اصلی پروژه
    # قبل از ارزش افزوده
    # -----------------------------------------------------

    price = ex_tax_price

    prices = []

    if price is not None:

        prices.append(
            price
        )

    return {

        # متن کامل سلول
        "text":
            text,

        # قیمت قبل از ارزش افزوده
        "price":
            price,

        # قیمت قبل از ارزش افزوده
        "ex_tax_price":
            ex_tax_price,

        # قیمت با ارزش افزوده
        "in_tax_price":
            in_tax_price,

        # برای سازگاری با ساختار قبلی
        "prices":
            prices,

        # متن قبل از ارزش افزوده
        "ex_tax_text":
            ex_tax_text,

        # متن با ارزش افزوده
        "in_tax_text":
            in_tax_text,

        # HTML برای دیباگ
        "html":
            str(cell)
    }


# =========================================================
# FETCH
# =========================================================

def fetch_page():

    print("=" * 70)
    print("PIVAN STEEL PRICE TEST")
    print("=" * 70)

    print(
        "URL:",
        URL
    )

    try:

        response = session.get(
            URL,
            timeout=30
        )

        print(
            "HTTP:",
            response.status_code
        )

        print(
            "LENGTH:",
            len(response.text)
        )

        response.raise_for_status()

        return response.text

    except Exception as e:

        print(
            "ERROR:",
            e
        )

        return ""


# =========================================================
# ANALYZE TABLE
# =========================================================

def analyze_table(table):

    rows = table.find_all(
        "tr"
    )

    products = []

    print()
    print("=" * 70)
    print("PRICE TABLE ANALYSIS")
    print("=" * 70)

    print(
        "ROWS:",
        len(rows)
    )

    for row_index, row in enumerate(
        rows,
        start=1
    ):

        cells = row.find_all(
            ["th", "td"]
        )

        values = [
            clean_text(
                cell.get_text(
                    " ",
                    strip=True
                )
            )
            for cell in cells
        ]

        if not values:
            continue

        print()
        print(
            f"ROW {row_index}:"
        )

        print(
            values
        )

        # -------------------------------------------------
        # Header
        # -------------------------------------------------

        if row_index == 1:
            continue

        # -------------------------------------------------
        # حداقل 5 ستون
        # -------------------------------------------------

        if len(cells) < 5:
            continue

        # -------------------------------------------------
        # SIZE
        # -------------------------------------------------

        size = clean_text(
            cells[0].get_text(
                " ",
                strip=True
            )
        )

        # -------------------------------------------------
        # STANDARD
        # -------------------------------------------------

        standard = clean_text(
            cells[1].get_text(
                " ",
                strip=True
            )
        )

        # -------------------------------------------------
        # DELIVERY
        # -------------------------------------------------

        delivery = clean_text(
            cells[2].get_text(
                " ",
                strip=True
            )
        )

        # -------------------------------------------------
        # UNIT
        # -------------------------------------------------

        unit = clean_text(
            cells[3].get_text(
                " ",
                strip=True
            )
        )

        # -------------------------------------------------
        # PRICE
        # -------------------------------------------------

        price_cell = analyze_price_cell(
            cells[4]
        )

        # -------------------------------------------------
        # FLUCTUATION
        # -------------------------------------------------

        fluctuation = ""

        if len(cells) >= 6:

            fluctuation = clean_text(
                cells[5].get_text(
                    " ",
                    strip=True
                )
            )

        # -------------------------------------------------
        # DEBUG OUTPUT
        # -------------------------------------------------

        print(
            "SIZE:",
            size
        )

        print(
            "STANDARD:",
            standard
        )

        print(
            "DELIVERY:",
            delivery
        )

        print(
            "UNIT:",
            unit
        )

        print(
            "PRICE TEXT:",
            price_cell["text"]
        )

        print(
            "EX TAX TEXT:",
            price_cell["ex_tax_text"]
        )

        print(
            "EX TAX PRICE:",
            price_cell["ex_tax_price"]
        )

        print(
            "IN TAX TEXT:",
            price_cell["in_tax_text"]
        )

        print(
            "IN TAX PRICE:",
            price_cell["in_tax_price"]
        )

        print(
            "FINAL PRICE:",
            price_cell["price"]
        )

        print(
            "PRICES:",
            price_cell["prices"]
        )

        print(
            "FLUCTUATION:",
            fluctuation
        )

        print(
            "PRICE CELL HTML:"
        )

        print(
            price_cell["html"][:5000]
        )

        # -------------------------------------------------
        # PRODUCT
        # -------------------------------------------------
        # فقط وقتی قیمت قبل از ارزش افزوده عدد داشته باشد
        # -------------------------------------------------

        if (
            size
            and standard
            and price_cell["price"] is not None
        ):

            products.append({

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
                    price_cell["price"],

                # قیمت قبل از ارزش افزوده
                "ex_tax_price":
                    price_cell["ex_tax_price"],

                # قیمت با ارزش افزوده
                "in_tax_price":
                    price_cell["in_tax_price"],

                # متن کامل
                "price_text":
                    price_cell["text"],

                # فقط قیمت اصلی
                "prices":
                    price_cell["prices"],

                "fluctuation":
                    fluctuation

            })

    return products


# =========================================================
# SAVE JSON
# =========================================================

def save_json(products):

    data = {

        "source":
            "pivan.co",

        "product":
            "میلگرد فولاد خراسان نیشابور",

        "url":
            URL,

        "price_type":
            "ex_tax",

        "price_description":
            "قیمت قبل از ارزش افزوده",

        "updated_at":
            datetime.now(
                timezone.utc
            ).isoformat(),

        "count":
            len(products),

        "products":
            products
    }

    with open(
        "pivan_test.json",
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2
        )


# =========================================================
# MAIN
# =========================================================

def main():

    html = fetch_page()

    if not html:

        print(
            "NO HTML RECEIVED"
        )

        return

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    tables = soup.find_all(
        "table"
    )

    print()
    print("=" * 70)
    print(
        "TABLE COUNT:",
        len(tables)
    )
    print("=" * 70)

    if not tables:

        print(
            "NO TABLE FOUND"
        )

        return

    all_products = []

    # =====================================================
    # پیدا کردن جدول قیمت
    # =====================================================

    for index, table in enumerate(
        tables,
        start=1
    ):

        headers = [

            clean_text(
                cell.get_text(
                    " ",
                    strip=True
                )
            )

            for cell in table.find_all(
                ["th", "td"]
            )[:10]
        ]

        table_text = clean_text(
            table.get_text(
                " ",
                strip=True
            )
        )

        # -------------------------------------------------
        # جدول قیمت
        # -------------------------------------------------

        if (
            "قیمت" not in table_text
            and "سایز" not in table_text
        ):

            continue

        print()
        print(
            "SELECTED TABLE:",
            index
        )

        print(
            "HEADERS:",
            headers
        )

        products = analyze_table(
            table
        )

        all_products.extend(
            products
        )

    # =====================================================
    # حذف تکراری
    # =====================================================

    unique = []

    seen = set()

    for product in all_products:

        key = (

            product["size"],

            product["standard"],

            product["delivery"],

            product["price"]

        )

        if key in seen:
            continue

        seen.add(
            key
        )

        unique.append(
            product
        )

    all_products = unique

    # =====================================================
    # SAVE
    # =====================================================

    save_json(
        all_products
    )

    # =====================================================
    # FINAL RESULT
    # =====================================================

    print()
    print("=" * 70)
    print("FINAL RESULT")
    print("=" * 70)

    print(
        "PRODUCTS FOUND:",
        len(all_products)
    )

    for product in all_products:

        print()

        print(
            "🏭 فولاد خراسان نیشابور"
        )

        print(
            "📏 سایز:",
            product["size"]
        )

        print(
            "📋 استاندارد:",
            product["standard"]
        )

        print(
            "📍 تحویل:",
            product["delivery"]
        )

        print(
            "⚖️ واحد:",
            product["unit"]
        )

        print(
            "💰 قیمت قبل از ارزش افزوده:",
            f'{product["price"]:,}'
        )

        print(
            "💰 قیمت با ارزش افزوده:",
            (
                f'{product["in_tax_price"]:,}'
                if product["in_tax_price"] is not None
                else "ندارد"
            )
        )

        print(
            "📊 نوسان:",
            product["fluctuation"]
        )

    print()
    print(
        "JSON FILE: pivan_test.json"
    )

    print()
    print("=" * 70)
    print(
        "TEST FINISHED"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()