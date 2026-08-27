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
        "Chrome/126.0 Safari/537.36"
    )
}
TIMEOUT = 30
# =========================================================
# CHANNEL FACTORIES
# =========================================================
CHANNEL_FACTORIES = [
    {
        "name": "ناودانی سبک ناب تبریز",
        "display": "سبک ناب",
        "type": "سبک",
        "url": "https://pivan.co/brands/tabriz-pure-steel/uchannel/",
    },
    {
        "name": "ناودانی سبک شکفته",
        "display": "سبک شکفته",
        "type": "سبک",
        "url": "https://pivan.co/brands/shekofteh-steel/uchannel/",
    },
    {
        "name": "ناودانی سنگین ناب تبریز",
        "display": "سنگین ناب",
        "type": "سنگین",
        "url": "https://pivan.co/brands/tabriz-pure-steel/uchannel/",
    },
    {
        "name": "ناودانی سنگین فایکو",
        "display": "سنگین فایکو",
        "type": "سنگین",
        "url": "https://pivan.co/brands/iranian-alborz-steel-factory-faiko/uchannel/",
    },
    {
        "name": "ناودانی سنگین ابهر",
        "display": "سنگین ابهر",
        "type": "سنگین",
        "url": "https://pivan.co/brands/west-alborz-steel-complex-and-factory/uchannel/",
    },
    {
        "name": "ناودانی سنگین شکفته",
        "display": "سنگین شکفته",
        "type": "سنگین",
        "url": "https://pivan.co/brands/shekofteh-steel/uchannel/",
    },
]
# =========================================================
# NORMALIZE
# =========================================================
def normalize_text(value):
    if value is None:
        return ""
    text = str(value)
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
    return re.sub(r"\s+", " ", text).strip()
# =========================================================
# PRICE PARSER
# =========================================================
def parse_channel_price(raw_price):
    """
    Pivan sometimes returns prices like:
        88000 80000
        89000 80900
        91500 83200
        110000 100000
    For the channel we MUST use the SECOND number.
    Examples:
        88000 80000   -> 80000
        89000 80900   -> 80900
        91500 83200   -> 83200
        110000 100000 -> 100000
    If only one numeric value exists, use that value.
    "تماس بگیرید" is NOT a price.
    """
    text = normalize_text(raw_price)
    if not text:
        return None
    # Contact / unavailable
    contact_words = [
        "تماس بگیرید",
        "تماس",
        "استعلام",
        "ناموجود",
        "موجود نیست",
        "-"
    ]
    if any(word in text for word in contact_words):
        return None
    # Extract all integer numbers
    numbers = re.findall(r"\d+(?:\.\d+)?", text)
    if not numbers:
        return None
    try:
        # IMPORTANT:
        # When Pivan provides two prices, the SECOND is the
        # actual current/channel price.
        if len(numbers) >= 2:
            price = float(numbers[-1])
        else:
            price = float(numbers[0])
        return int(price)
    except Exception:
        return None
# =========================================================
# PRICE FORMAT
# =========================================================
def format_price(price):
    if price is None:
        return None
    return f"{price:,}"
# =========================================================
# SIZE PARSER
# =========================================================
def parse_size(value):
    value = normalize_text(value)
    match = re.search(r"\d+", value)
    if not match:
        return None
    try:
        return int(match.group())
    except Exception:
        return None
# =========================================================
# LENGTH PARSER
# =========================================================
def parse_length(value):
    value = normalize_text(value)
    match = re.search(r"\d+(?:\.\d+)?", value)
    if not match:
        return None
    try:
        number = float(match.group())
        if number.is_integer():
            return int(number)
        return number
    except Exception:
        return None
# =========================================================
# FIND CHANNEL TABLE
# =========================================================
def find_channel_table(tables):
    """
    Pivan pages can contain several tables.
    The channel table is normally the table whose rows contain
    size + length + warehouse/factory + unit + price.
    """
    best_table = None
    best_score = -1
    for index, table in enumerate(tables):
        rows = table.find_all("tr")
        if not rows:
            continue
        score = 0
        for row in rows:
            cells = row.find_all(["td", "th"])
            if not cells:
                continue
            values = [
                normalize_text(cell.get_text(" ", strip=True))
                for cell in cells
            ]
            row_text = " ".join(values)
            # Size
            if any(re.fullmatch(r"\d{1,2}", x) for x in values):
                score += 2
            # Length
            if any(x in ["6", "12", "6 متر", "12 متر"] for x in values):
                score += 2
            # Unit
            if "کیلوگرم" in row_text:
                score += 2
            # Price-like values
            if re.search(r"\d{4,}", row_text):
                score += 2
        if score > best_score:
            best_score = score
            best_table = index
    return best_table
# =========================================================
# EXTRACT TABLE
# =========================================================
def extract_channel_products(factory):
    print()
    print("=" * 70)
    print("CHANNEL PRICE")
    print("=" * 70)
    print(f"FACTORY: {factory['name']}")
    print(f"TYPE: {factory['type']}")
    print(f"URL: {factory['url']}")
    try:
        response = requests.get(
            factory["url"],
            headers=HEADERS,
            timeout=TIMEOUT
        )
        print(f"HTTP: {response.status_code}")
        print(f"LENGTH: {len(response.text)}")
        response.raise_for_status()
    except Exception as e:
        print(f"REQUEST ERROR: {e}")
        return []
    soup = BeautifulSoup(response.text, "html.parser")
    tables = soup.find_all("table")
    print(f"TABLE COUNT: {len(tables)}")
    if not tables:
        print("NO TABLE FOUND")
        return []
    table_index = find_channel_table(tables)
    if table_index is None:
        print("CHANNEL TABLE NOT FOUND")
        return []
    print(f"SELECTED CHANNEL TABLE: {table_index}")
    table = tables[table_index]
    rows = table.find_all("tr")
    print(f"ROWS: {len(rows)}")
    products = []
    for row in rows:
        cells = row.find_all(["td", "th"])
        if len(cells) < 5:
            continue
        values = [
            normalize_text(cell.get_text(" ", strip=True))
            for cell in cells
        ]
        # Debug
        print(f"RAW ROW: {values}")
        # -------------------------------------------------
        # Expected Pivan structure:
        #
        # [size, length, location, unit, price, change, ...]
        # -------------------------------------------------
        size = parse_size(values[0])
        length = parse_length(values[1])
        if size is None:
            continue
        if length is None:
            continue
        # Unit must normally be kilogram
        row_text = " ".join(values)
        if "کیلوگرم" not in row_text:
            continue
        # Price normally lives in column 5
        raw_price = values[4] if len(values) > 4 else ""
        price = parse_channel_price(raw_price)
        if price is None:
            print(
                f"SIZE {size}: PRICE NOT FOUND"
            )
            continue
        print(
            f"SIZE {size} | "
            f"LENGTH {length} | "
            f"PRICE {format_price(price)}"
        )
        products.append(
            {
                "size": size,
                "length": length,
                "price": price,
                "location": values[2] if len(values) > 2 else "",
            }
        )
    # =====================================================
    # REMOVE DUPLICATES
    # =====================================================
    # Same size + length can appear more than once.
    # For example Shekofteh can have:
    #
    # 8 / 6 / warehouse
    # 8 / 6 / factory
    #
    # For the channel we keep the FACTORY price when available.
    #
    # Otherwise keep the first valid record.
    grouped = {}
    for product in products:
        key = (
            product["size"],
            product["length"]
        )
        location = normalize_text(product.get("location", ""))
        is_factory = "کارخانه" in location
        if key not in grouped:
            grouped[key] = product
            grouped[key]["_factory"] = is_factory
        else:
            old = grouped[key]
            old_factory = old.get("_factory", False)
            # Prefer کارخانه over انبار
            if is_factory and not old_factory:
                grouped[key] = product
                grouped[key]["_factory"] = True
    products = list(grouped.values())
    # Sort by size then length
    products.sort(
        key=lambda x: (
            x["size"],
            x["length"]
        )
    )
    # Remove internal field
    for product in products:
        product.pop("_factory", None)
    print(f"VALID CHANNEL PRODUCTS: {len(products)}")
    return products
# =========================================================
# ALL FACTORIES
# =========================================================
def get_all_channel_prices():
    result = {}
    for factory in CHANNEL_FACTORIES:
        products = extract_channel_products(factory)
        result[factory["display"]] = {
            "name": factory["name"],
            "type": factory["type"],
            "products": products,
        }
    return result
# =========================================================
# FINAL RESULT
# =========================================================
def print_final_result(data):
    print()
    print("=" * 70)
    print("FINAL CHANNEL RESULT")
    print("=" * 70)
    for display, factory in data.items():
        products = factory["products"]
        print()
        if products:
            print(f"{display} -> ok")
            for product in products:
                print(
                    f"ناودانی "
                    f"{product['size']} - "
                    f"{product['length']} متر : "
                    f"{format_price(product['price'])} تومان"
                )
        else:
            print(f"{display} -> NO VALID PRICE")
# =========================================================
# MAIN
# =========================================================
if __name__ == "__main__":
    data = get_all_channel_prices()
    print_final_result(data)