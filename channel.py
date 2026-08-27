import re
import requests
from bs4 import BeautifulSoup


# =========================================================
# SETTINGS
# =========================================================

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/139.0 Safari/537.36"
    )
}

TIMEOUT = 30


# =========================================================
# CHANNEL FACTORIES
# =========================================================
#
# ناودانی سبک:
#   ناب
#   شکفته
#
# ناودانی سنگین:
#   ناب
#   فایکو
#   ابهر
#   شکفته
#
# =========================================================

CHANNEL_FACTORIES = {

    # =====================================================
    # LIGHT
    # =====================================================

    "سبک ناب": {
        "name": "ناودانی سبک ناب تبریز",
        "weight": "سبک",
        "factory": "ناب",
        "url": (
            "https://pivan.co/brands/"
            "tabriz-pure-steel/uchannel/"
        )
    },

    "سبک شکفته": {
        "name": "ناودانی سبک شکفته",
        "weight": "سبک",
        "factory": "شکفته",
        "url": (
            "https://pivan.co/brands/"
            "shekofteh-steel/uchannel/"
        )
    },


    # =====================================================
    # HEAVY
    # =====================================================

    "سنگین ناب": {
        "name": "ناودانی سنگین ناب تبریز",
        "weight": "سنگین",
        "factory": "ناب",
        "url": (
            "https://pivan.co/brands/"
            "tabriz-pure-steel/uchannel/"
        )
    },

    "سنگین فایکو": {
        "name": "ناودانی سنگین فایکو",
        "weight": "سنگین",
        "factory": "فایکو",
        "url": (
            "https://pivan.co/brands/"
            "iranian-alborz-steel-factory-faiko/"
            "uchannel/"
        )
    },

    "سنگین ابهر": {
        "name": "ناودانی سنگین ابهر",
        "weight": "سنگین",
        "factory": "ابهر",
        "url": (
            "https://pivan.co/brands/"
            "west-alborz-steel-complex-and-factory/"
            "uchannel/"
        )
    },

    "سنگین شکفته": {
        "name": "ناودانی سنگین شکفته",
        "weight": "سنگین",
        "factory": "شکفته",
        "url": (
            "https://pivan.co/brands/"
            "shekofteh-steel/uchannel/"
        )
    }
}


# =========================================================
# NUMBER NORMALIZATION
# =========================================================

def normalize_digits(text):

    if not text:
        return ""

    translation = str.maketrans(
        "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩",
        "01234567890123456789"
    )

    return text.translate(
        translation
    )


def extract_numbers(text):

    text = normalize_digits(
        text
    )

    text = text.replace(
        ",",
        ""
    )

    text = text.replace(
        "٬",
        ""
    )

    return [
        float(x)
        for x in re.findall(
            r"\d+(?:\.\d+)?",
            text
        )
    ]


# =========================================================
# FIND PRICE TABLE
# =========================================================

def find_channel_table(soup):

    tables = soup.find_all(
        "table"
    )

    print(
        "TABLE COUNT:",
        len(tables)
    )

    if not tables:
        return None

    for index, table in enumerate(
        tables
    ):

        text = table.get_text(
            " ",
            strip=True
        )

        normalized = normalize_digits(
            text
        )

        # -------------------------------------------------
        # جدول ناودانی
        # -------------------------------------------------

        if (
            "سایز" in normalized
            and "قیمت" in normalized
        ):

            print(
                "SELECTED CHANNEL TABLE:",
                index
            )

            return table

    return None


# =========================================================
# PARSE CHANNEL TABLE
# =========================================================

def parse_channel_table(table):

    products = []

    rows = table.find_all(
        "tr"
    )

    print(
        "ROWS:",
        len(rows)
    )

    for row in rows:

        cells = row.find_all(
            ["td", "th"]
        )

        if not cells:
            continue

        texts = [
            c.get_text(
                " ",
                strip=True
            )
            for c in cells
        ]

        full_text = " ".join(
            texts
        )

        # -------------------------------------------------
        # HEADER
        # -------------------------------------------------

        if "سایز" in full_text:
            continue

        # -------------------------------------------------
        # SIZE
        # -------------------------------------------------

        size = None

        for text in texts:

            numbers = extract_numbers(
                text
            )

            if not numbers:
                continue

            for number in numbers:

                value = int(
                    number
                )

                # سایزهای معمول ناودانی
                if 5 <= value <= 30:

                    size = value

                    break

            if size is not None:
                break

        if size is None:
            continue

        # -------------------------------------------------
        # LENGTH
        # -------------------------------------------------

        length = None

        for text in texts:

            numbers = extract_numbers(
                text
            )

            for number in numbers:

                if number in (
                    6,
                    12
                ):

                    length = int(
                        number
                    )

                    break

            if length is not None:
                break

        # -------------------------------------------------
        # PRICE
        # -------------------------------------------------

        price_candidates = []

        for text in texts:

            numbers = extract_numbers(
                text
            )

            for number in numbers:

                # قیمت واقعی
                if number >= 10000:

                    price_candidates.append(
                        int(number)
                    )

        if not price_candidates:

            print(
                f"SIZE {size}: PRICE NOT FOUND"
            )

            continue

        # آخرین قیمت بزرگ جدول
        price = price_candidates[-1]

        item = {

            "size":
                size,

            "price":
                price
        }

        if length is not None:

            item["length"] = length

        products.append(
            item
        )

        print(
            f"SIZE {size} "
            f"| LENGTH {length} "
            f"| PRICE {price:,}"
        )

    # -----------------------------------------------------
    # REMOVE DUPLICATES
    # -----------------------------------------------------

    unique = {}

    for item in products:

        key = (
            item["size"],
            item.get("length")
        )

        unique[key] = item

    products = list(
        unique.values()
    )

    products.sort(
        key=lambda x: (
            x["size"],
            x.get("length") or 0
        )
    )

    return products


# =========================================================
# PARSE FACTORY
# =========================================================

def parse_factory(
    factory_key,
    factory_data
):

    print()
    print("=" * 70)
    print("CHANNEL PRICE")
    print("=" * 70)

    print(
        "FACTORY:",
        factory_data["name"]
    )

    print(
        "TYPE:",
        factory_data["weight"]
    )

    print(
        "URL:",
        factory_data["url"]
    )

    response = requests.get(
        factory_data["url"],
        headers=HEADERS,
        timeout=TIMEOUT
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

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    table = find_channel_table(
        soup
    )

    if table is None:

        raise RuntimeError(
            "Channel price table not found"
        )

    prices = parse_channel_table(
        table
    )

    if not prices:

        raise RuntimeError(
            "No valid channel prices found"
        )

    print(
        "VALID CHANNEL PRODUCTS:",
        len(prices)
    )

    return prices


# =========================================================
# GET ALL CHANNEL PRICES
# =========================================================

def get_all_channel_prices():

    result = {}

    for key, factory in CHANNEL_FACTORIES.items():

        try:

            prices = parse_factory(
                key,
                factory
            )

            result[key] = {

                "name":
                    factory["name"],

                "weight":
                    factory["weight"],

                "factory":
                    factory["factory"],

                "prices":
                    prices,

                "status":
                    "ok"

            }

        except Exception as e:

            print(
                f"ERROR {key}:",
                e
            )

            result[key] = {

                "name":
                    factory["name"],

                "weight":
                    factory["weight"],

                "factory":
                    factory["factory"],

                "prices":
                    [],

                "status":
                    "error",

                "error":
                    str(e)

            }

    return result


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    data = get_all_channel_prices()

    print()
    print("=" * 70)
    print("FINAL CHANNEL RESULT")
    print("=" * 70)

    for key, factory in data.items():

        print()
        print(
            f"{key} -> "
            f"{factory['status']}"
        )

        if factory["status"] == "error":

            print(
                "ERROR:",
                factory.get(
                    "error",
                    ""
                )
            )

            continue

        for item in factory["prices"]:

            length = item.get(
                "length"
            )

            if length:

                print(
                    f"ناودانی {item['size']} "
                    f" - {length} متر : "
                    f"{item['price']:,} تومان"
                )

            else:

                print(
                    f"ناودانی {item['size']} : "
                    f"{item['price']:,} تومان"
                )