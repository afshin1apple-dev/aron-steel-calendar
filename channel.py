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
        "٠": "0",
        "١": "1",
        "٢": "2",
        "٣": "3",
        "٤": "4",
        "٥": "5",
        "٦": "6",
        "٧": "7",
        "٨": "8",
        "٩": "9",
        "٬": "",
        "،": "",
        ",": "",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text
# =========================================================
# CLEAN TEXT
# =========================================================
def clean_text(text):
    if text is None:
        return ""
    text = normalize_digits(text)
    text = text.replace("\n", " ")
    text = text.replace("\r", " ")
    text = text.replace("\t", " ")
    return " ".join(
        text.split()
    ).strip()
# =========================================================
# EXTRACT INTEGER
# =========================================================
def extract_number(text):
    text = normalize_digits(text)
    matches = re.findall(
        r"\d+(?:\.\d+)?",
        text
    )
    if not matches:
        return None
    try:
        value = matches[0]
        if "." in value:
            return float(value)
        return int(value)
    except Exception:
        return None
# =========================================================
# EXTRACT ALL NUMBERS
# =========================================================
def extract_numbers(text):
    text = normalize_digits(text)
    matches = re.findall(
        r"\d+(?:\.\d+)?",
        text
    )
    result = []
    for value in matches:
        try:
            if "." in value:
                result.append(float(value))
            else:
                result.append(int(value))
        except Exception:
            pass
    return result
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
        ),
        "Accept-Language": "fa-IR,fa;q=0.9,en;q=0.8",
        "Accept": (
            "text/html,application/xhtml+xml,"
            "application/xml;q=0.9,*/*;q=0.8"
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
def extract_price_from_cell(cell):
    if cell is None:
        return None
    # -----------------------------------------------------
    # First inspect the complete visible text.
    # -----------------------------------------------------
    text = clean_text(
        cell.get_text(
            " ",
            strip=True
        )
    )
    if not text:
        return None
    # -----------------------------------------------------
    # Ignore cells that clearly contain dimensions.
    # -----------------------------------------------------
    lower = text.lower()
    if (
        "طول" in text
        or "سایز" in text
        or "اندازه" in text
    ):
        return None
    # -----------------------------------------------------
    # Look for price-like numbers.
    # -----------------------------------------------------
    numbers = extract_numbers(
        text
    )
    if not numbers:
        return None
    candidates = []
    for number in numbers:
        if not isinstance(number, (int, float)):
            continue
        # Dimensions are not prices.
        if number in (6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30):
            continue
        # Percentage / small values.
        if number < 1000:
            continue
        candidates.append(
            int(number)
        )
    if not candidates:
        return None
    # -----------------------------------------------------
    # Pivan prices are normally the largest numeric value
    # inside the price cell.
    # -----------------------------------------------------
    return max(candidates)
# =========================================================
# PARSE ROW
# =========================================================
def parse_row(row, factory):
    cells = row.find_all(
        "td"
    )
    if not cells:
        return None
    cell_texts = [
        clean_text(
            cell.get_text(
                " ",
                strip=True
            )
        )
        for cell in cells
    ]
    row_text = " | ".join(
        cell_texts
    )
    # -----------------------------------------------------
    # Ignore obvious header rows
    # -----------------------------------------------------
    if (
        "سایز" in row_text
        or "قیمت" in row_text
        or "طول" in row_text
        or "وزن" in row_text
    ):
        return None
    # -----------------------------------------------------
    # DEBUG: print exact row structure
    # -----------------------------------------------------
    print(
        "RAW ROW:",
        cell_texts
    )
    # -----------------------------------------------------
    # SIZE
    # -----------------------------------------------------
    size = None
    size_index = None
    for index, text in enumerate(cell_texts):
        numbers = extract_numbers(
            text
        )
        for number in numbers:
            if (
                isinstance(number, int)
                and 6 <= number <= 30
            ):
                size = number
                size_index = index
                break
        if size is not None:
            break
    if size is None:
        return None
    # -----------------------------------------------------
    # LENGTH
    # -----------------------------------------------------
    length = None
    length_index = None
    # First try cells other than size cell.
    for index, text in enumerate(cell_texts):
        if index == size_index:
            continue
        numbers = extract_numbers(
            text
        )
        for number in numbers:
            if number in (6, 12):
                length = int(number)
                length_index = index
                break
        if length is not None:
            break
    # -----------------------------------------------------
    # PRICE
    # -----------------------------------------------------
    price = None
    price_index = None
    # Prefer cells after size/length.
    for index, cell in enumerate(cells):
        if index == size_index:
            continue
        if index == length_index:
            continue
        candidate = extract_price_from_cell(
            cell
        )
        if candidate is not None:
            price = candidate
            price_index = index
            break
    # -----------------------------------------------------
    # If price wasn't found, inspect every cell again.
    # -----------------------------------------------------
    if price is None:
        for index, cell in enumerate(cells):
            candidate = extract_price_from_cell(
                cell
            )
            if candidate is not None:
                price = candidate
                price_index = index
                break
    # -----------------------------------------------------
    # Validate
    # -----------------------------------------------------
    if price is None:
        print(
            f"SIZE {size}: PRICE NOT FOUND"
        )
        return None
    # -----------------------------------------------------
    # If length is missing, do NOT blindly guess 12.
    # -----------------------------------------------------
    if length is None:
        print(
            f"SIZE {size} | "
            f"PRICE {price:,} | "
            f"LENGTH NOT FOUND"
        )
        return None
    product = {
        "size": size,
        "length": length,
        "price": price,
        "factory": factory["key"],
        "factory_name": factory["name"],
        "type": factory["type"]
    }
    print(
        f"SIZE {size} | "
        f"LENGTH {length} | "
        f"PRICE {price:,}"
    )
    return product
# =========================================================
# PARSE UCHANNEL TABLE
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
    # Current Pivan structure:
    # first table = channel price table
    # -----------------------------------------------------
    table = tables[0]
    print(
        "SELECTED CHANNEL TABLE: 0"
    )
    rows = table.find_all(
        "tr"
    )
    print(
        "ROWS:",
        len(rows)
    )
    products = []
    for row in rows:
        product = parse_row(
            row,
            factory
        )
        if product is not None:
            products.append(
                product
            )
    return products
# =========================================================
# FETCH FACTORY
# =========================================================
def fetch_factory(factory):
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
        # Remove duplicate size + length.
        #
        # IMPORTANT:
        # Last value wins only if the same exact
        # size/length combination appears twice.
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