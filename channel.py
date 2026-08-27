import os
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
# NUMBER CLEANER
# =========================================================

def clean_number(text):

    if not text:
        return None

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
        "٬": "",
        ",": "",
        "،": "",
        "تومان": "",
        "ریال": "",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    digits = ""

    for char in text:

        if char.isdigit():
            digits += char

    if not digits:
        return None

    try:
        return int(digits)

    except Exception:
        return None


# =========================================================
# TEXT CLEANER
# =========================================================

def clean_text(text):

    if text is None:
        return ""

    text = str(text)

    text = text.replace("\n", " ")
    text = text.replace("\r", " ")
    text = text.replace("\t", " ")

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
    # Pivan's first table is currently the channel table.
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
        # Skip header rows
        # -------------------------------------------------

        if (
            "سایز" in row_text
            or "قیمت" in row_text
            or "طول" in row_text
        ):
            continue

        # -------------------------------------------------
        # Find size
        # -------------------------------------------------

        size = None

        for value in values:

            number = clean_number(
                value
            )

            if number is not None:

                # U-channel sizes are normally
                # between 6 and 30.
                if 6 <= number <= 30:

                    size = number

                    break

        if size is None:

            continue

        # -------------------------------------------------
        # Find length
        # -------------------------------------------------

        length = None

        for value in values:

            number = clean_number(
                value
            )

            if number in (
                6,
                12
            ):

                length = number

        # -------------------------------------------------
        # Find price
        # -------------------------------------------------

        price = None

        for value in reversed(values):

            number = clean_number(
                value
            )

            if number is not None:

                # Price should be considerably
                # larger than dimensions.
                if number >= 1000:

                    price = number

                    break

        if price is None:

            print(
                f"SIZE {size}: PRICE NOT FOUND"
            )

            continue

        if length is None:

            length = 12

        product = {

            "size": size,

            "length": length,

            "price": price,

            "factory": factory["key"],

            "factory_name": factory["name"],

            "type": factory["type"]
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
        # Remove duplicates
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

        print(
            f"{factory['key']} -> "
            f"{'ok' if factory['prices'] else 'FAILED'}"
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