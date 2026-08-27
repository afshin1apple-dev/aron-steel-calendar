import re
import requests
from bs4 import BeautifulSoup


# =========================================================
# SETTINGS
# =========================================================

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/139.0 Safari/537.36"
    )
}

TIMEOUT = 30


# =========================================================
# FACTORIES
# =========================================================
#
# مهم:
# سه کارخانه اول برای کانال هستند.
#
# کارخانه‌های بعدی فقط برای PRIVATE_CHAT_ID
# استفاده می‌شوند و وارد کانال نمی‌شوند.
#
# =========================================================

FACTORIES = {

    # =====================================================
    # CHANNEL FACTORIES
    # =====================================================

    "نیشابور": {
        "name": "فولاد خراسان (نیشابور)",
        "url": (
            "https://pivan.co/brands/"
            "khorasan-steel-neishabour/rebar/"
        )
    },

    "هیربد": {
        "name": "فولاد هیربد زرندیه",
        "url": (
            "https://pivan.co/brands/"
            "zirandieh-hirbod-steel-factory/rebar/"
        )
    },

    "امیرکبیر": {
        "name": "فولاد امیرکبیر خزر",
        "url": (
            "https://pivan.co/brands/"
            "folad-amir-kabir-khazar-factory/rebar/"
        )
    },


    # =====================================================
    # PRIVATE FACTORIES
    # =====================================================

    "میانه": {
        "name": "فولاد میانه (آذربایجان)",
        "url": (
            "https://pivan.co/brands/"
            "miyane-factory/rebar/"
        )
    },

    "سیرجان": {
        "name": "جهان فولاد سیرجان",
        "url": (
            "https://pivan.co/brands/"
            "jahan-folad-sirjan/rebar/"
        )
    },

    "بافق": {
        "name": "فولاد بافق یزد",
        "url": (
            "https://pivan.co/brands/"
            "bafgh-steel/rebar/"
        )
    },

    "آریان": {
        "name": "آریان فولاد",
        "url": (
            "https://pivan.co/brands/"
            "arian-steel-factory/rebar/"
        )
    },

    "فایکو": {
        "name": "فولاد البرز ایرانیان (فایکو)",
        "url": (
            "https://pivan.co/brands/"
            "iranian-alborz-steel-factory-faiko/rebar/"
        )
    },

    "راد همدان": {
        "name": "فولاد راد همدان",
        "url": (
            "https://pivan.co/brands/"
            "folad-rad-hamedan-factory/rebar/"
        )
    }
}


# =========================================================
# NUMBER
# =========================================================

def normalize_digits(text):

    if not text:
        return ""

    translation = str.maketrans(
        "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩",
        "01234567890123456789"
    )

    return text.translate(translation)


def extract_numbers(text):

    text = normalize_digits(text)

    text = text.replace(",", "")
    text = text.replace("٬", "")

    numbers = re.findall(
        r"\d+(?:\.\d+)?",
        text
    )

    return [
        float(x)
        for x in numbers
    ]


# =========================================================
# PARSE FACTORY PAGE
# =========================================================

def parse_factory(
    factory_key,
    factory_data
):

    print()
    print("=" * 70)
    print("PIVAN STEEL PRICE")
    print("=" * 70)

    url = factory_data["url"]

    print(
        "FACTORY:",
        factory_data["name"]
    )

    print(
        "URL:",
        url
    )

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=TIMEOUT
    )

    response.raise_for_status()

    print(
        "HTTP:",
        response.status_code
    )

    print(
        "LENGTH:",
        len(response.text)
    )

    soup = BeautifulSoup(
        response.text,
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

        raise RuntimeError(
            f"No table found for {factory_key}"
        )

    selected_table = None

    # -----------------------------------------------------
    # Find table containing size / price
    # -----------------------------------------------------

    for index, table in enumerate(tables):

        table_text = table.get_text(
            " ",
            strip=True
        )

        if (
            "سایز" in table_text
            and "قیمت" in table_text
        ):

            selected_table = table

            print(
                "SELECTED PRICE TABLE:",
                index
            )

            break

    if selected_table is None:

        raise RuntimeError(
            f"Price table not found for {factory_key}"
        )

    # -----------------------------------------------------
    # Extract rows
    # -----------------------------------------------------

    products = []

    rows = selected_table.find_all(
        "tr"
    )

    print()
    print("=" * 70)
    print("EXTRACTING PRODUCTS")
    print("=" * 70)

    for row in rows:

        cells = row.find_all(
            ["td", "th"]
        )

        if not cells:
            continue

        cell_texts = [
            c.get_text(
                " ",
                strip=True
            )
            for c in cells
        ]

        full_text = " ".join(
            cell_texts
        )

        # -------------------------------------------------
        # Ignore header
        # -------------------------------------------------

        if "سایز" in full_text:
            continue

        # -------------------------------------------------
        # SIZE
        # -------------------------------------------------

        size = None

        for text in cell_texts:

            nums = extract_numbers(
                text
            )

            if not nums:
                continue

            candidate = int(
                nums[0]
            )

            if 6 <= candidate <= 40:

                size = candidate
                break

        if size is None:
            continue

        # -------------------------------------------------
        # PRICE
        # -------------------------------------------------

        price_candidates = []

        for text in cell_texts:

            nums = extract_numbers(
                text
            )

            for value in nums:

                if value >= 10000:

                    price_candidates.append(
                        int(value)
                    )

        if not price_candidates:

            print(
                f"⚠️ SIZE {size}: "
                "PRICE NOT AVAILABLE"
            )

            continue

        # -------------------------------------------------
        # PIVAN:
        # last large number = EX-TAX PRICE
        # -------------------------------------------------

        steel_price = price_candidates[-1]

        print(
            f"SIZE {size}: "
            f"EX-TAX PRICE = "
            f"{steel_price:,}"
        )

        products.append({

            "size":
                size,

            "price":
                steel_price
        })

    # -----------------------------------------------------
    # Remove duplicate sizes
    # -----------------------------------------------------

    unique = {}

    for product in products:

        size = product["size"]

        unique[size] = product

    products = list(
        unique.values()
    )

    products.sort(
        key=lambda x: x["size"]
    )

    print(
        "Steel products found:",
        len(products)
    )

    return products


# =========================================================
# GET ALL FACTORIES
# =========================================================

def get_all_prices():

    result = {}

    for key, factory in FACTORIES.items():

        try:

            prices = parse_factory(
                key,
                factory
            )

            result[key] = {

                "name":
                    factory["name"],

                "prices":
                    prices
            }

        except Exception as e:

            print(
                f"ERROR {key}:",
                e
            )

            result[key] = {

                "name":
                    factory["name"],

                "prices":
                    []
            }

    return result


# =========================================================
# COMPATIBILITY
# =========================================================

def get_prices():

    """
    Compatibility with previous code.

    فقط قیمت نیشابور را برمی‌گرداند.
    """

    return parse_factory(
        "نیشابور",
        FACTORIES["نیشابور"]
    )


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    data = get_all_prices()

    print()
    print("=" * 70)
    print("FINAL RESULT")
    print("=" * 70)

    for factory_key, factory in data.items():

        print()
        print(
            factory["name"]
        )

        for item in factory["prices"]:

            print(
                f"{item['size']} : "
                f"{item['price']:,} تومان"
            )