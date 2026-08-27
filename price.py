import requests
import json
import re
from datetime import datetime, timezone
from bs4 import BeautifulSoup


# =========================================================
# SETTINGS
# =========================================================

PIVAN_URL = (
    "https://pivan.co/brands/"
    "khorasan-steel-neishabour/rebar/"
)

OUTPUT_FILE = "prices.json"

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

    text = text.replace("\xa0", " ")
    text = text.replace("\u200c", " ")
    text = text.replace("\u200f", "")
    text = text.replace("\u200e", "")

    return " ".join(text.split()).strip()


# =========================================================
# PERSIAN / ARABIC DIGITS
# =========================================================

def normalize_digits(text):

    if text is None:
        return ""

    text = str(text)

    translation = str.maketrans(
        "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩",
        "01234567890123456789"
    )

    return text.translate(translation)


# =========================================================
# PRICE PARSER
# =========================================================

def parse_price(text):

    text = clean_text(text)

    if not text:
        return None

    text = normalize_digits(text)

    numbers = re.findall(
        r"\d[\d,]*",
        text
    )

    if not numbers:
        return None

    values = []

    for number in numbers:

        number = number.replace(",", "")

        try:
            value = int(number)

            if value > 1000:
                values.append(value)

        except Exception:
            continue

    if not values:
        return None

    return values[-1]


# =========================================================
# EXTRACT PRICE FROM PRICE CELL
# =========================================================

def extract_price_from_cell(cell):

    if cell is None:
        return None

    # -----------------------------------------
    # اول span مربوط به ex-tax
    # -----------------------------------------

    ex_tax = cell.select_one(
        ".ex-tax"
    )

    if ex_tax:

        value = parse_price(
            ex_tax.get_text(
                " ",
                strip=True
            )
        )

        if value:
            return value

    # -----------------------------------------
    # اگر ex-tax پیدا نشد
    # -----------------------------------------

    text = cell.get_text(
        " ",
        strip=True
    )

    return parse_price(text)


# =========================================================
# FETCH PIVAN
# =========================================================

def fetch_pivan():

    print()
    print("=" * 70)
    print("PIVAN STEEL PRICE")
    print("=" * 70)

    print(
        "URL:",
        PIVAN_URL
    )

    try:

        response = session.get(
            PIVAN_URL,
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
            "REQUEST ERROR:",
            e
        )

        return ""


# =========================================================
# FIND REBAR TABLE
# =========================================================

def find_price_table(soup):

    tables = soup.find_all("table")

    print()
    print(
        "TABLE COUNT:",
        len(tables)
    )

    # -----------------------------------------
    # بررسی تمام جدول‌ها
    # -----------------------------------------

    for index, table in enumerate(
        tables,
        start=1
    ):

        text = clean_text(
            table.get_text(
                " ",
                strip=True
            )
        )

        # جدول مورد نظر باید قیمت، سایز
        # و نوسان داشته باشد
        if (
            "سایز" in text
            and "قیمت" in text
            and "نوسان" in text
        ):

            print(
                "SELECTED PRICE TABLE:",
                index
            )

            return table

    return None


# =========================================================
# EXTRACT PRODUCTS
# =========================================================

def extract_products(html):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    table = find_price_table(
        soup
    )

    if table is None:

        print()
        print(
            "ERROR: PRICE TABLE NOT FOUND"
        )

        return []

    products = []

    rows = table.find_all("tr")

    print()
    print("=" * 70)
    print("EXTRACTING PRODUCTS")
    print("=" * 70)

    for row in rows:

        cells = row.find_all(
            "td"
        )

        if len(cells) < 5:
            continue

        values = [
            clean_text(
                cell.get_text(
                    " ",
                    strip=True
                )
            )
            for cell in cells
        ]

        # -----------------------------------------
        # ستون‌ها طبق جدول پیوان
        #
        # 0 = سایز
        # 1 = استاندارد
        # 2 = محل تحویل
        # 3 = واحد
        # 4 = قیمت
        # 5 = نوسان
        # -----------------------------------------

        size_text = values[0]
        standard = values[1]
        delivery = values[2]
        unit = values[3]

        # -----------------------------------------
        # سایز باید عدد باشد
        # -----------------------------------------

        size_match = re.search(
            r"\d+",
            normalize_digits(size_text)
        )

        if not size_match:
            continue

        size = int(
            size_match.group()
        )

        # فقط سایزهای منطقی میلگرد
        if size < 8 or size > 50:
            continue

        # -----------------------------------------
        # قیمت
        # -----------------------------------------

        price = extract_price_from_cell(
            cells[4]
        )

        if price is None:
            continue

        # -----------------------------------------
        # نوسان
        # -----------------------------------------

        fluctuation = None

        if len(values) > 5:

            fluctuation_text = normalize_digits(
                values[5]
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

        product = {
            "factory": "فولاد خراسان نیشابور",
            "brand": "KSC",
            "product": "میلگرد",
            "size": size,
            "standard": standard,
            "delivery": delivery,
            "unit": unit,
            "price": price,
            "price_unit": "تومان",
            "fluctuation_percent": fluctuation,
            "source": "Pivan",
            "source_url": PIVAN_URL
        }

        products.append(
            product
        )

    # -----------------------------------------
    # حذف سایزهای تکراری
    # -----------------------------------------

    unique = []
    seen = set()

    for product in products:

        key = (
            product["factory"],
            product["size"],
            product["standard"],
            product["delivery"]
        )

        if key in seen:
            continue

        seen.add(key)

        unique.append(
            product
        )

    unique.sort(
        key=lambda x: x["size"]
    )

    return unique


# =========================================================
# SAVE JSON
# =========================================================

def save_json(products):

    data = {
        "source": "Pivan",
        "source_url": PIVAN_URL,
        "factory": "فولاد خراسان نیشابور",
        "product": "میلگرد",
        "updated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "count": len(products),
        "prices": products
    }

    with open(
        OUTPUT_FILE,
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
# PRINT RESULT
# =========================================================

def print_result(products):

    print()
    print("=" * 70)
    print("FINAL RESULT")
    print("=" * 70)

    print(
        "PRODUCTS FOUND:",
        len(products)
    )

    print()

    for product in products:

        print(
            f"🏭 {product['factory']} | "
            f"📏 {product['size']} | "
            f"📋 {product['standard']} | "
            f"💰 {product['price']:,} تومان | "
            f"📍 {product['delivery']}"
        )

    print()
    print("=" * 70)


# =========================================================
# MAIN
# =========================================================

def main():

    html = fetch_pivan()

    if not html:

        print(
            "No HTML received."
        )

        return

    products = extract_products(
        html
    )

    if not products:

        print()
        print(
            "NO PRODUCTS FOUND"
        )

        return

    data = save_json(
        products
    )

    print_result(
        products
    )

    print()
    print(
        "JSON FILE:",
        OUTPUT_FILE
    )

    print(
        "TOTAL:",
        data["count"]
    )

    print()
    print("=" * 70)
    print("PRICE TEST FINISHED SUCCESSFULLY")
    print("=" * 70)


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    main()