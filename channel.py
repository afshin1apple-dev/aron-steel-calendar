import os
import re
import requests
from bs4 import BeautifulSoup


# =========================================================
# SETTINGS
# =========================================================

PIVAN_BASE = "https://pivan.co"

TIMEOUT = 30


# =========================================================
# CHANNEL FACTORIES
# =========================================================

CHANNEL_FACTORIES = [

    # -----------------------------------------------------
    # ناودانی سبک
    # -----------------------------------------------------

    {
        "key": "سبک ناب",
        "name": "ناودانی سبک ناب تبریز",
        "type": "سبک",
        "url": (
            "https://pivan.co/brands/"
            "tabriz-pure-steel/uchannel/"
        )
    },

    {
        "key": "سبک شکفته",
        "name": "ناودانی سبک شکفته",
        "type": "سبک",
        "url": (
            "https://pivan.co/brands/"
            "shekofteh-steel/uchannel/"
        )
    },

    # -----------------------------------------------------
    # ناودانی سنگین
    # -----------------------------------------------------

    {
        "key": "سنگین ناب",
        "name": "ناودانی سنگین ناب تبریز",
        "type": "سنگین",
        "url": (
            "https://pivan.co/brands/"
            "tabriz-pure-steel/uchannel/"
        )
    },

    {
        "key": "سنگین فایکو",
        "name": "ناودانی سنگین فایکو",
        "type": "سنگین",
        "url": (
            "https://pivan.co/brands/"
            "iranian-alborz-steel-factory-faiko/"
            "uchannel/"
        )
    },

    {
        "key": "سنگین ابهر",
        "name": "ناودانی سنگین ابهر",
        "type": "سنگین",
        "url": (
            "https://pivan.co/brands/"
            "west-alborz-steel-complex-and-factory/"
            "uchannel/"
        )
    },

    {
        "key": "سنگین شکفته",
        "name": "ناودانی سنگین شکفته",
        "type": "سنگین",
        "url": (
            "https://pivan.co/brands/"
            "shekofteh-steel/uchannel/"
        )
    }
]


# =========================================================
# NUMBER NORMALIZER
# =========================================================

def normalize_digits(text):

    if text is None:
        return ""

    text = str(text)

    replacements = {
        "۰": "0",
        "۱": "1",
        "۲": "2",
        "۳": "3",
        "۴": "4",
        "۵": "5",
        "۶": "6",
        "۷": "7",
        "۸": "8",
        "۹": "9",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text


# =========================================================
# EXTRACT NUMBERS
# =========================================================

def extract_numbers(text):

    """
    تمام عددهای مستقل داخل متن را پیدا می‌کند.

    مثال:

    '8,800 80,000 تومان'

    تبدیل می‌شود به:

    [8800, 80000]

    نه:

    880008000
    """

    if not text:
        return []

    text = normalize_digits(text)

    # حذف واحدها و علائم متنی
    text = text.replace("تومان", " ")
    text = text.replace("ریال", " ")
    text = text.replace("٬", ",")
    text = text.replace("،", ",")

    # اعداد با یا بدون جداکننده هزارگان
    matches = re.findall(
        r"\d[\d,]*",
        text
    )

    numbers = []

    for match in matches:

        cleaned = match.replace(
            ",",
            ""
        )

        if not cleaned.isdigit():
            continue

        try:

            numbers.append(
                int(cleaned)
            )

        except Exception:

            continue

    return numbers


# =========================================================
# CLEAN TEXT
# =========================================================

def clean_text(text):

    if text is None:
        return ""

    text = str(text)

    text = text.replace(
        "\n",
        " "
    )

    text = text.replace(
        "\r",
        " "
    )

    text = text.replace(
        "\t",
        " "
    )

    return " ".join(
        text.split()
    ).strip()


# =========================================================
# GET PAGE
# =========================================================

def get_page(url):

    headers = {

        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/126.0 Safari/537.36"
        )
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=TIMEOUT
    )

    response.raise_for_status()

    return response.text


# =========================================================
# FIND PRICE IN CELL
# =========================================================

def find_price_in_cell(text):

    """
    قیمت واقعی را از بین اعداد داخل سلول پیدا می‌کند.

    قیمت‌های فعلی Pivan برای این بخش حدود
    80,000 تا 100,000 هستند.

    اگر سلول شامل مواردی مثل:

        8,800 80,000

    باشد، فقط 80,000 انتخاب می‌شود.

    همچنین اگر:

        9,150 83,200

    باشد، 83,200 انتخاب می‌شود.

    """

    numbers = extract_numbers(
        text
    )

    if not numbers:
        return None

    # -----------------------------------------------------
    # قیمت‌های معمول بازار فولاد
    # -----------------------------------------------------

    price_candidates = [

        number

        for number in numbers

        if 10_000 <= number <= 999_999
    ]

    if price_candidates:

        # معمولاً قیمت واقعی آخرین عدد معتبر است
        return price_candidates[-1]

    return None


# =========================================================
# FIND SIZE
# =========================================================

def find_size(values):

    for value in values:

        numbers = extract_numbers(
            value
        )

        for number in numbers:

            # سایز ناودانی
            if 6 <= number <= 30:

                return number

    return None


# =========================================================
# FIND LENGTH
# =========================================================

def find_length(values):

    lengths = []

    for value in values:

        numbers = extract_numbers(
            value
        )

        for number in numbers:

            if number in (6, 12):

                lengths.append(
                    number
                )

    if lengths:

        return lengths[-1]

    return None


# =========================================================
# PARSE TABLE
# =========================================================

def parse_uchannel_table(
    html,
    factory
):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    tables = soup.find_all(
        "table"
    )

    print(
        "TABLE COUNT:",
        len(tables)
    )

    if not tables:

        return []

    # -----------------------------------------------------
    # Pivan channel table
    # -----------------------------------------------------

    table = tables[0]

    rows = table.find_all(
        "tr"
    )

    print(
        "SELECTED CHANNEL TABLE: 0"
    )

    print(
        "ROWS:",
        len(rows)
    )

    products = []

    for row in rows:

        cells = row.find_all(
            ["td", "th"]
        )

        if not cells:
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

        row_text = " ".join(
            values
        )

        # -------------------------------------------------
        # Skip headers
        # -------------------------------------------------

        header_words = [
            "سایز",
            "قیمت",
            "طول",
            "ناودانی",
            "وزن",
        ]

        if any(
            word in row_text
            for word in header_words
        ):

            continue

        # -------------------------------------------------
        # SIZE
        # -------------------------------------------------

        size = find_size(
            values
        )

        if size is None:

            continue

        # -------------------------------------------------
        # LENGTH
        # -------------------------------------------------

        length = find_length(
            values
        )

        # -------------------------------------------------
        # PRICE
        # -------------------------------------------------

        price = None

        # از آخرین سلول‌ها شروع می‌کنیم
        # چون قیمت معمولاً سمت راست جدول است.

        for value in reversed(
            values
        ):

            candidate = find_price_in_cell(
                value
            )

            if candidate is not None:

                price = candidate

                break

        if price is None:

            print(
                f"SIZE {size}: PRICE NOT FOUND"
            )

            continue

        # -------------------------------------------------
        # DEFAULT LENGTH
        # -------------------------------------------------

        if length is None:

            length = 12

        product = {

            "size": size,

            "length": length,

            "price": price,

            "factory":
                factory["key"],

            "factory_name":
                factory["name"],

            "type":
                factory["type"]
        }

        products.append(
            product
        )

        print(
            f"SIZE {size} | "
            f"LENGTH {length} | "
            f"PRICE {price:,}"
        )

    return products


# =========================================================
# FETCH FACTORY
# =========================================================

def fetch_factory(
    factory
):

    print()
    print(
        "=" * 70
    )

    print(
        "CHANNEL PRICE"
    )

    print(
        "=" * 70
    )

    print(
        "FACTORY:",
        factory["name"]
    )

    print(
        "TYPE:",
        factory["type"]
    )

    print(
        "URL:",
        factory["url"]
    )

    try:

        html = get_page(
            factory["url"]
        )

        print(
            "HTTP: 200"
        )

        print(
            "LENGTH:",
            len(html)
        )

        prices = parse_uchannel_table(
            html,
            factory
        )

        # -------------------------------------------------
        # REMOVE DUPLICATES
        # -------------------------------------------------

        unique = {}

        for item in prices:

            key = (
                item["size"],
                item["length"]
            )

            unique[key] = item

        prices = list(
            unique.values()
        )

        prices.sort(
            key=lambda x: (
                x["size"],
                x["length"]
            )
        )

        print(
            "VALID CHANNEL PRODUCTS:",
            len(prices)
        )

        return {

            "key":
                factory["key"],

            "name":
                factory["name"],

            "type":
                factory["type"],

            "url":
                factory["url"],

            "prices":
                prices
        }

    except Exception as e:

        print(
            "FACTORY ERROR:",
            factory["name"],
            e
        )

        return {

            "key":
                factory["key"],

            "name":
                factory["name"],

            "type":
                factory["type"],

            "url":
                factory["url"],

            "prices":
                []
        }


# =========================================================
# MAIN
# =========================================================

def main():

    results = []

    for factory in CHANNEL_FACTORIES:

        result = fetch_factory(
            factory
        )

        results.append(
            result
        )

    # =====================================================
    # FINAL RESULT
    # =====================================================

    print()
    print(
        "=" * 70
    )

    print(
        "FINAL CHANNEL RESULT"
    )

    print(
        "=" * 70
    )

    for factory in results:

        print()

        status = (
            "ok"
            if factory["prices"]
            else "FAILED"
        )

        print(
            f"{factory['key']} -> {status}"
        )

        for item in factory["prices"]:

            print(
                f"ناودانی "
                f"{item['size']} - "
                f"{item['length']} متر : "
                f"{item['price']:,} تومان"
            )

    print()
    print(
        "=" * 70
    )

    return results


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    main()